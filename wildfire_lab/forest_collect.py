"""Audit saved forest predictions/selection by arithmetic; never fit or sample."""
import hashlib
import json
from pathlib import Path
from zipfile import ZipFile
import numpy as np
import pandas as pd
from wildfire_lab.forest_models import rbf
from wildfire_lab.selection import configurations,energies,exact_subset
from wildfire_lab.annual_classical import errors


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def scale_saved(raw,preprocessing):
    filled=np.where(np.isnan(raw),np.array(preprocessing['median']),raw)
    return (filled-np.array(preprocessing['mean']))/np.array(preprocessing['scale'])


def check_preprocessing(raw,cross,targets,record):
    p=record['preprocessing']
    medians=np.nanmedian(raw,axis=0)
    np.testing.assert_allclose(medians,p['median'],atol=1e-10)
    filled=np.where(np.isnan(raw),medians,raw)
    scale=filled.std(axis=0)
    scale[scale==0]=1
    np.testing.assert_allclose(filled.mean(axis=0),p['mean'],atol=1e-10)
    np.testing.assert_allclose(scale,p['scale'],atol=1e-10)
    np.testing.assert_allclose(np.log1p(targets).mean(),p['y_mean'],atol=1e-10)
    np.testing.assert_allclose(np.log1p(targets).std(),p['y_scale'],atol=1e-10)
    x,v=scale_saved(raw,p),scale_saved(cross,p)
    y=(np.log1p(targets)-p['y_mean'])/p['y_scale']
    np.testing.assert_allclose(x,record['scaled_train'],atol=1e-10)
    np.testing.assert_allclose(v,record['scaled_cross'],atol=1e-10)
    np.testing.assert_allclose(y,record['scaled_targets'],atol=1e-10)
    return x,v,y


def check_selection(record,plan):
    obj={k:np.array(v) if isinstance(v,list) else v for k,v in record['objective'].items()}
    bits=configurations(len(obj['linear']))
    exact,minimum=exact_subset(obj)
    if record['choices']['exact']!=exact:
        raise ValueError('Saved exact subset changed')
    np.testing.assert_allclose(minimum,record['exact_minimum'],atol=1e-9)
    if sum(record['counts'].values())!=plan['selection']['shots']:
        raise ValueError('Selector shot budget changed')
    draws=np.array([int(b,2) for b,n in record['counts'].items() for _ in range(n)])
    for kind,samples in [('sampled',draws),('uniform',np.array(record['uniform_draws']))]:
        eligible=np.unique(samples[bits[samples].sum(axis=1)==obj['k']])
        costs=energies(obj,bits[eligible])
        best=eligible[np.argmin(costs)]
        result=record[kind]
        np.testing.assert_allclose(result['sqd_energy'],costs.min(),atol=1e-9)
        np.testing.assert_allclose(result['gap_to_exact'],costs.min()-minimum,atol=1e-9)
        if result['selected_subset']!=np.flatnonzero(bits[best]).tolist():
            raise ValueError('Saved SQD subset does not match sampled diagonal minimum')
    return dict(quantum_shots=len(draws),uniform_draws=len(record['uniform_draws']),
                diagonal_subspaces_checked=2,mutual_information_refitted=False)


def audit(root,evidence):
    intent=evidence['intent']
    plan=intent['plan']
    dataset=root/plan['dataset']
    if digest(dataset)!=intent['dataset_sha256']:
        raise ValueError('Frozen forest training table changed')
    table=pd.read_csv(dataset)
    if table.year.tolist()!=list(range(1988,2019)):
        raise ValueError('Forest table contains unexpected years')
    checked,selectors,pairs=0,[],0
    for fold in evidence['folds']:
        first,last,vfirst,vlast=fold['fold']
        train=table[table.year.between(first,last)]
        valid=table[table.year.between(vfirst,vlast)]
        targets=train.mean_reported_size_ha.to_numpy()
        actual=valid.mean_reported_size_ha.to_numpy()
        np.testing.assert_array_equal(fold['train_years'],train.year)
        np.testing.assert_array_equal(fold['validation_years'],valid.year)
        selectors.append(check_selection(fold['selection'],plan))
        for condition,record in fold['conditions'].items():
            columns=record['rows'][0]['features']
            x,v,y=check_preprocessing(train[columns].to_numpy(),valid[columns].to_numpy(),targets,record)
            gram=np.array(record['quantum_gram']);cross=np.array(record['quantum_cross'])
            np.testing.assert_allclose(gram,gram.T,atol=1e-10)
            np.testing.assert_allclose(np.diag(gram),1.,atol=1e-10)
            if np.linalg.eigvalsh(gram).min()<-1e-7 or cross.shape!=(len(v),len(x)):
                raise ValueError('Saved quantum matrix geometry is invalid')
            pairs+=record['resource']['pair_circuits']
            for row in record['rows']:
                parameters=row['parameters']
                if row['model']=='ridge':
                    coef=np.array(parameters['coef'])
                    prediction=v@coef+parameters['intercept']
                    residual=x@coef+parameters['intercept']-y
                    np.testing.assert_allclose(x.T@residual+plan['models']['ridge']['alpha']*coef,0,atol=1e-8)
                    np.testing.assert_allclose(residual.mean(),0,atol=1e-9)
                else:
                    kernel=cross if row['model']=='qsvr' else rbf(x,v,record['rbf_gamma'])
                    prediction=kernel[:,parameters['support']]@np.array(parameters['dual_coef'])+parameters['intercept']
                p=record['preprocessing']
                hectares=np.maximum(0,np.expm1(prediction*p['y_scale']+p['y_mean']))
                np.testing.assert_allclose(prediction,row['predicted_scaled'],atol=1e-9)
                np.testing.assert_allclose(hectares,row['predicted_ha'],atol=1e-7)
                np.testing.assert_allclose(actual,row['actual_ha'],atol=1e-9)
                for metric,value in errors(actual,hectares).items():
                    np.testing.assert_allclose(value,row[metric],atol=1e-7)
                global_row=next(r for r in evidence['rows'] if r['fold']==fold['fold']
                    and r['condition']==condition and r['model']==row['model'])
                np.testing.assert_allclose(global_row['predicted_ha'],hectares,atol=1e-7)
                checked+=1
        baseline=next(r for r in evidence['rows'] if r['fold']==fold['fold'] and r['model']=='training_mean')
        np.testing.assert_allclose(baseline['predicted_ha'],np.repeat(targets.mean(),len(actual)),atol=1e-9)
        for metric,value in errors(actual,np.repeat(targets.mean(),len(actual))).items():
            np.testing.assert_allclose(value,baseline[metric],atol=1e-9)
    if checked!=plan['budget']['model_fits'] or pairs!=evidence['pair_circuits']:
        raise ValueError('Saved panel budget/count does not match plan')
    return dict(status='verified',predictor_equations_checked=checked,
        baseline_records_checked=len(evidence['folds']),kernel_records_checked=sum(len(f['conditions']) for f in evidence['folds']),
        selectors=selectors,new_predictor_fits=0,new_quantum_evaluations=0,new_draws=0,
        limitation='Checks stored quantum matrix shape/PSD and fitted prediction equations; does not regenerate quantum kernels, refit mutual information, or establish independent predictive validation.')


def collect(root,output,bundle=None):
    if bundle is not None:
        index=json.loads((root/'docs/results/forest-expansion.json').read_text())
        if digest(bundle)!=index['bundle_sha256']:
            raise ValueError('Public forest evidence bundle changed')
        with ZipFile(bundle) as archive:
            if archive.namelist()!=['evidence.json']:
                raise ValueError('Unexpected forest evidence members')
            output.mkdir(parents=True,exist_ok=False)
            (output/'evidence.json').write_bytes(archive.read('evidence.json'))
    evidence=json.loads((output/'evidence.json').read_text())
    receipt=audit(root,evidence)
    (output/'audit.json').write_text(json.dumps(receipt,indent=2)+'\n')
    return receipt

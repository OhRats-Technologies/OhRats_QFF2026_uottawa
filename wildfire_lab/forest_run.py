"""Execute one frozen annual forest panel, preserving raw selectors and fit equations."""
import hashlib
import importlib.metadata
import json
import subprocess
import time
import numpy as np
import pandas as pd
from wildfire_lab.forest_features import POOL,panels
from wildfire_lab.forest_models import prepare,fit
from wildfire_lab.forest_selectors import select
from wildfire_lab.annual_classical import errors


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write(path,value):
    path.write_text(json.dumps(value,indent=2)+'\n')


def run(root,output,plan_path):
    plan=json.loads(plan_path.read_text())
    for name,expected in plan['input_sha256'].items():
        if digest(root/name)!=expected:
            raise ValueError(f'Frozen forest input changed: {name}')
    dataset=root/plan['dataset']
    table=pd.read_csv(dataset)
    if table.year.tolist()!=list(range(1988,2019)):
        raise ValueError('Only the31 training years are permitted')
    output.mkdir(parents=True,exist_ok=False)
    start=time.perf_counter()
    code_sha={name:digest(root/name) for name in plan['code_paths']}
    revision=subprocess.check_output(['git','rev-parse','HEAD'],cwd=root,text=True).strip()
    intent=dict(plan=plan,plan_sha256=digest(plan_path),code_sha256=code_sha,
        revision=revision,dataset_sha256=digest(dataset),
        packages={n:importlib.metadata.version(n) for n in
                  ['qiskit','qiskit-machine-learning','qiskit-addon-sqd','scikit-learn','numpy']})
    write(output/'intent.json',intent)
    evidence=dict(intent=intent,folds=[],rows=[],pair_circuits=0,model_fits=0,
                  final_test_accessed=False,hardware_jobs=0)
    for number,fold in enumerate(plan['folds']):
        first,last,vfirst,vlast=fold
        train=table[table.year.between(first,last)]
        valid=table[table.year.between(vfirst,vlast)]
        targets=train.mean_reported_size_ha.to_numpy()
        actual=valid.mean_reported_size_ha.to_numpy()
        path=output/f'fold-{number}'
        path.mkdir()
        x,cross,y,_,preprocessing=prepare(train[POOL].to_numpy(),valid[POOL].to_numpy(),targets)
        choices,selection=select(x,y,plan,path)
        record=dict(fold=fold,train_years=train.year.tolist(),validation_years=valid.year.tolist(),
            target_train_ha=targets.tolist(),actual_ha=actual.tolist(),selection=selection,
            selector_preprocessing=preprocessing,selector_train=x.tolist(),conditions={})
        prediction=np.repeat(targets.mean(),len(actual))
        evidence['rows'].append(dict(fold=fold,condition='no_inputs',model='training_mean',
            predicted_ha=prediction.tolist(),actual_ha=actual.tolist(),**errors(actual,prediction)))
        for condition,columns in panels(choices).items():
            if time.perf_counter()-start>plan['budget']['elapsed_soft_limit_seconds']:
                raise TimeoutError('Frozen panel budget reached; partial evidence preserved')
            result=fit(train[columns].to_numpy(),valid[columns].to_numpy(),targets,actual,columns,plan)
            record['conditions'][condition]=result
            evidence['pair_circuits']+=result['resource']['pair_circuits']
            evidence['model_fits']+=len(result['rows'])
            if evidence['pair_circuits']>plan['budget']['pair_circuits_max']:
                raise ValueError('Frozen quantum-pair budget exceeded')
            evidence['rows'].extend(dict(fold=fold,condition=condition,**row) for row in result['rows'])
            write(path/'progress.json',record)
            print(f'Fold{number} {condition}: {evidence["model_fits"]} fits, {evidence["pair_circuits"]} pairs',flush=True)
        evidence['folds'].append(record)
        write(output/'progress.json',evidence)
    if evidence['model_fits']!=plan['budget']['model_fits']:
        raise ValueError('Expected model panel is incomplete')
    evidence.update(status='complete',seconds=time.perf_counter()-start,
        local_selector_shots=len(plan['folds'])*plan['selection']['shots'],
        auxiliary_classical_draws=len(plan['folds'])*plan['selection']['shots'])
    write(output/'evidence.json',evidence)
    return evidence

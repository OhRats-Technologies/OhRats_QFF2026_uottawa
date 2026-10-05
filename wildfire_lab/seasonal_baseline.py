"""Pure seasonal/spatial controls and read-only saved-parameter verification."""
import hashlib
import json
import time
import warnings
import numpy as np
from scipy.special import expit
from sklearn.exceptions import ConvergenceWarning
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler
from wildfire_lab.evaluation import scores,split


def identities(frame):
    return hashlib.sha256(json.dumps(frame.incident_id.tolist()).encode()).hexdigest()


def eligible(frame,plan):
    if not frame.year.between(*plan['train_years']).all() or not frame.incident_id.is_unique:
        raise ValueError('Only unique training-period incidents are allowed')
    if not set(frame.target.unique())=={0,1}:raise ValueError('Binary training target required')


def run(frame,plan,checkpoint=lambda:None):
    eligible(frame,plan);rows=[];fits=0
    for fold in plan['folds']:
        train,valid=split(frame,fold,tuple(plan['train_years']))
        y=train.target.to_numpy()
        for group,columns in plan['feature_groups'].items():
            checkpoint();start=time.perf_counter()
            parameters=None
            if columns:
                fits+=1
                if fits>plan['max_logistic_fits']:raise ValueError('Logistic-fit cap exceeded')
                imputer=SimpleImputer(strategy='median',keep_empty_features=True)
                x=imputer.fit_transform(train[columns]);v=imputer.transform(valid[columns])
                scaler=StandardScaler().fit(x)
                with warnings.catch_warnings():
                    warnings.simplefilter('error',ConvergenceWarning)
                    model=LogisticRegression(**plan['logistic']).fit(scaler.transform(x),y)
                prediction=model.predict_proba(scaler.transform(v))[:,1]
                parameters=dict(median=imputer.statistics_.tolist(),mean=scaler.mean_.tolist(),
                    scale=scaler.scale_.tolist(),coefficient=model.coef_[0].tolist(),
                    intercept=float(model.intercept_[0]),iterations=int(model.n_iter_[0]))
            else:prediction=np.full(len(valid),y.mean())
            rows.append(dict(group=group,features=columns,fold=fold,train_rows=len(train),validation_rows=len(valid),
                train_id_sha256=identities(train),validation_id_sha256=identities(valid),
                train_prevalence=float(y.mean()),parameters=parameters,predictions=prediction.tolist(),
                metric=scores(valid.target.to_numpy(),prediction),seconds=time.perf_counter()-start))
    return rows


def validate(frame,plan,rows):
    eligible(frame,plan);expected={(tuple(f),g) for f in plan['folds'] for g in plan['feature_groups']};seen=set()
    for row in rows:
        key=(tuple(row['fold']),row['group'])
        if key not in expected or key in seen:raise ValueError('Missing/duplicate/changed baseline condition')
        seen.add(key);train,valid=split(frame,row['fold'],tuple(plan['train_years']))
        columns=plan['feature_groups'][row['group']]
        if row['features']!=columns or row['train_id_sha256']!=identities(train) or row['validation_id_sha256']!=identities(valid):
            raise ValueError('Changed baseline features/sample identities')
        if (row['train_rows'],row['validation_rows'])!=(len(train),len(valid)):
            raise ValueError('Changed baseline row counts')
        if not np.isclose(row['train_prevalence'],train.target.mean(),atol=1e-12):
            raise ValueError('Changed training prevalence')
        if columns:
            p=row['parameters'];raw=train[columns].to_numpy(dtype=float)
            median=np.nanmedian(raw,axis=0);median=np.nan_to_num(median,nan=0)
            x=np.where(np.isnan(raw),median,raw);mean=x.mean(axis=0);scale=x.std(axis=0);scale[scale==0]=1
            for name,value in [('median',median),('mean',mean),('scale',scale)]:
                if not np.allclose(p[name],value,atol=1e-9,rtol=1e-9):raise ValueError('Changed train-only transform')
            raw=valid[columns].to_numpy(dtype=float);v=np.where(np.isnan(raw),p['median'],raw)
            prediction=expit(((v-p['mean'])/p['scale'])@np.asarray(p['coefficient'])+p['intercept'])
            if not 0<p['iterations']<plan['logistic']['max_iter']:raise ValueError('Unconverged baseline fit')
        else:
            if row['parameters'] is not None:raise ValueError('Intercept control cannot have fitted coefficients')
            prediction=np.full(len(valid),train.target.mean())
        if not np.allclose(row['predictions'],prediction,atol=1e-10,rtol=1e-10):raise ValueError('Changed stored predictions')
        metric=scores(valid.target.to_numpy(),prediction)
        if any(not np.isclose(metric[k],row['metric'][k],atol=1e-10,rtol=1e-10) for k in metric):
            raise ValueError('Metrics disagree with reconstructed predictions')
    if seen!=expected:raise ValueError('Missing baseline conditions')
    return dict(conditions=len(seen),train_only_transform=True,stored_parameters_reconstruct_predictions=True,
                metrics_recomputed=True,no_model_refit=True)

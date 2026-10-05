"""Recompute final metrics and verify the frozen label/sample budgets."""
import hashlib
import numpy as np
from wildfire_lab.evaluation import scores,sample_indices
from wildfire_lab.final_gate import validate_plan


def metric(row,labels,probability):
    prediction=np.asarray(row['predictions'])
    if len(prediction)!=len(labels) or not np.isfinite(prediction).all():raise ValueError('Invalid saved predictions')
    expected=scores(labels,prediction,probability)
    if set(expected)!=set(row['metric']) or any(not np.isclose(value,row['metric'][name],atol=1e-12,rtol=0) for name,value in expected.items()):
        raise ValueError('Saved metric differs from recomputed prediction score')


def validate(record,train,test):
    plan=record['plan'];validate_plan(plan)
    if record['status']!='complete' or record['hardware_jobs_submitted']!=0:raise ValueError('Final outcome incomplete or unexpected hardware')
    if train.incident_id.duplicated().any() or test.incident_id.duplicated().any() or set(train.incident_id)&set(test.incident_id):
        raise ValueError('Invalid fire identities')
    if not train.year.between(1988,2018).all() or not test.year.between(2019,2024).all():raise ValueError('Invalid final year windows')
    if record['test_dataset']['rows']!=len(test):raise ValueError('Test count mismatch')
    full=record['rows']['full_training_models'];capped=record['rows']['capped_crossed_matrix']
    expected={(g,p) for g in plan['feature_groups'] for p in ['logistic','tree']}
    if {(r['group'],r['predictor']) for r in full}!=expected or len(full)!=len(expected):raise ValueError('Full-model comparison missing or duplicated')
    if plan['primary_model'] not in {r['predictor']+' / '+r['group'] for r in full}:raise ValueError('Declared primary model missing')
    for row in full:
        if row['features']!=plan['feature_groups'][row['group']] or row['seed']!=plan['seeds'][0]:raise ValueError('Changed full-model features/seed')
        metric(row,test.target.to_numpy(),True)
        for year,reported in row.get('metrics_by_year',{}).items():
            mask=test.year.eq(int(year)).to_numpy();labels=test.target.to_numpy()[mask]
            if len(set(labels))==2:metric(dict(predictions=np.asarray(row['predictions'])[mask],metric=reported),labels,True)
            elif reported!=dict(status='one_class',rows=len(labels),prevalence=float(labels.mean())):raise ValueError('Invalid single-class year annotation')
        if set(row.get('metrics_by_year',{}))!={str(y) for y in test.year.unique()}:raise ValueError('Missing per-year evidence')
    config=plan['encoding_screen'];predictors={'standard_logistic',*(v+'/'+k for v in config['preprocessing'] for k in config['kernels'])}
    expected={(seed,g,p) for seed in plan['seeds'] for g in plan['selectors'] for p in predictors}
    complete=[r for r in capped if r['status']=='complete']
    if {(r['seed'],r['group'],r['predictor']) for r in complete}!=expected or len(complete)!=len(expected):raise ValueError('Crossed comparison missing or duplicated')
    for row in complete:
        ti=sample_indices(len(train),config['train_cap'],row['seed']);vi=sample_indices(len(test),config['validation_cap'],row['seed'])
        if any(hashlib.sha256(indices.tobytes()).hexdigest()!=row[name+'_indices_sha256'] for name,indices in [('train',ti),('validation',vi)]):
            raise ValueError('Changed capped sample')
        if row['selection_train_rows']!=len(ti) or row['train_rows']!=len(ti) or row['validation_rows']!=len(vi):raise ValueError('Changed label budget')
        if len(row['features'])!=plan['feature_budget'] or not set(row['features']).issubset(plan['features']):raise ValueError('Changed feature budget')
        metric(row,test.iloc[vi].target.to_numpy(),False)
        if row.get('hardware_jobs_submitted',0)!=0:raise ValueError('Unexpected hardware')
    return dict(saved_predictions_recomputed=True,identities_and_years_disjoint=True,full_models=len(full),capped_models=len(complete),
                sample_hashes_and_label_budgets=True,declared_feature_budgets=True,per_year_metrics=True,no_new_hardware=True)

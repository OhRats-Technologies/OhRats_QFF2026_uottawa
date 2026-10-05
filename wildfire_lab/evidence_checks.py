"""Verify saved experiment evidence against its immutable input and budgets."""
import hashlib
import io
import numpy as np
import pandas as pd
from wildfire_lab.evaluation import split, sample_indices
from wildfire_lab.spatial import split as spatial_split


def validate(record,reservation,dataset):
    if record['status']!='complete':raise ValueError('Only completed evidence can be promoted')
    if record['plan']!=reservation['plan'] or record['id']!=reservation['id']:raise ValueError('Reservation/plan mismatch')
    if reservation['plan_sha256'] not in record['code_hashes'].values():raise ValueError('Frozen plan hash missing')
    raw=(dataset/'features.csv').read_bytes()
    if hashlib.sha256(raw).hexdigest()!=record['dataset']['data_sha256']:raise ValueError('Dataset hash mismatch')
    frame=pd.read_csv(io.BytesIO(raw))
    if frame.incident_id.duplicated().any() or frame.year.max()>2018:raise ValueError('Identity or sealed-year violation')
    conditions={};comparisons={}
    plan=record['plan']
    if plan['final_test_sealed'] is not True:raise ValueError('Final test must remain sealed')
    for row in record['rows']:
        if row['status']!='complete':continue
        fold=tuple(row['fold']);spatial=row.get('spatial')
        if list(fold) not in plan['validation_folds'] or row['seed'] not in plan['seeds']:raise ValueError('Undeclared fold/seed')
        key=(fold,spatial['train_side'] if spatial else None)
        if key not in conditions:
            train,valid=split(frame,fold,plan['train_years'])
            if plan.get('exclude_center_water'):
                train=train.loc[train.cover_center_water.eq(0)];valid=valid.loc[valid.cover_center_water.eq(0)]
            if spatial:train,valid,_=spatial_split(train,valid,spatial['train_side'],plan['spatial']['width_m'],plan['spatial']['guard_m'])
            conditions[key]=(train,valid)
        train,valid=conditions[key]
        if row['full_train_rows']!=len(train) or row['full_validation_rows']!=len(valid):raise ValueError('Declared full row count mismatch')
        config=plan.get('encoding_screen') if record['axis'] in {'encoding','combinations'} else plan.get('kernel_screen') if record['axis']=='prediction' else None
        if config:
            ti=sample_indices(len(train),config['train_cap'],row['seed']);vi=sample_indices(len(valid),config['validation_cap'],row['seed'])
            if hashlib.sha256(ti.tobytes()).hexdigest()!=row['train_indices_sha256'] or hashlib.sha256(vi.tobytes()).hexdigest()!=row['validation_indices_sha256']:
                raise ValueError('Sampled row hash mismatch')
            valid=valid.iloc[vi]
        metric=row['metric']
        if metric['rows']!=len(valid) or not np.isclose(metric['prevalence'],valid.target.mean(),atol=1e-12):raise ValueError('Validation labels/count mismatch')
        if any(not np.isfinite(value) or not 0<=value<=1 for name,value in metric.items() if name not in {'rows'}):raise ValueError('Invalid metric')
        if any(c in {'target','reported_size_ha','fire_size','SIZE_HA','response_type'} for c in row['features']):raise ValueError('Leaking predictor field')
        if record['axis']=='selection' and row.get('selector') not in {'all_features','fixed_control'} and len(row['features'])!=plan['feature_budget']:
            raise ValueError('Selector feature budget mismatch')
        if record['axis']=='combinations' and (len(row['features'])!=plan['feature_budget'] or row['selection_train_rows']!=row['train_rows']):
            raise ValueError('Crossed label/feature budget mismatch')
        if row.get('hardware_jobs_submitted',0):raise ValueError('Unexpected hardware use in local screen')
        budget_key=(*key,row['seed'],(spatial or {}).get('control'))
        signature=(row['full_train_rows'],metric['rows'],metric['prevalence'],row.get('train_indices_sha256'),row.get('validation_indices_sha256'))
        if budget_key in comparisons and comparisons[budget_key]!=signature:raise ValueError('Unmatched comparison rows')
        comparisons[budget_key]=signature
    return dict(dataset_hash=True,unique_training_incidents=True,chronological_window=True,
                sampled_hashes_and_prevalence=True,matched_comparison_rows=True,feature_label_budgets=True,
                rows_checked=sum(r['status']=='complete' for r in record['rows']))

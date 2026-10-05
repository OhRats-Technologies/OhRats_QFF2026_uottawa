"""Reconstruct fixed tangent/classical kernels and inherited labelled samples."""
import json
import numpy as np
import pandas as pd
from sklearn.metrics.pairwise import rbf_kernel,euclidean_distances
from wildfire_lab.geometry_inputs import load as geometry_load,sha
from wildfire_lab.evaluation import split,sample_indices
from wildfire_lab.encoding_screen import normalize_kernel
from wildfire_lab.ridge_kernel import normalized_features


def load(root,plan):
    cache=root/plan['parent_geometry_cache'];assert sha(cache/'outcome.json')==plan['parent_geometry_outcome_sha256']
    geometry=json.loads((cache/'outcome.json').read_text());assert geometry['status']=='complete'
    metric=np.asarray(geometry['metric']);parent,conditions=geometry_load(root,geometry['intent']['plan'])
    reference=root/plan['ridge_reference'];assert sha(reference)==plan['ridge_reference_sha256']
    old=json.loads(reference.read_text());parent_plan=parent['parent_plan']
    assert plan['kernel_ridge']==old['plan']['kernel_ridge'] and parent_plan['features']==old['parent_plan']['features']
    source=root/parent_plan['dataset']/'features.csv';assert sha(source)==parent_plan['dataset_sha256']
    frame=pd.read_csv(source,usecols=['incident_id','year','target'])
    assert frame.year.between(1988,2018).all() and frame.incident_id.is_unique
    train,valid=split(frame,parent_plan['fold'],train_window=(1988,2018));eigen,vectors=np.linalg.eigh(metric)
    if eigen.min()<=0:raise ValueError('Frozen tangent metric must be positive definite')
    factor=vectors*np.sqrt(eigen);samples=[]
    for seed in plan['seeds']:
        selected=[item for item in conditions if item[0]['seed']==seed]
        assert {item[0]['angle_scale'] for item in selected}==set(plan['angle_scales'])
        _,x,v,_,_=selected[0]
        ti=sample_indices(len(train),parent_plan['train_cap'],seed);vi=sample_indices(len(valid),parent_plan['validation_cap'],seed)
        y=train.iloc[ti].target.to_numpy();target=valid.iloc[vi].target.to_numpy()
        if len(np.unique(y))!=2 or len(np.unique(target))!=2:raise ValueError('One-class capped cohort')
        distances=euclidean_distances(x,squared=True)[np.triu_indices(len(x),1)]
        gamma=float(1/np.median(distances[distances>0]));tx,tv=x@factor,v@factor
        raw=dict(linear=(x@x.T,v@x.T),tangent=(tx@tx.T,tv@tx.T),
                 rbf=(rbf_kernel(x,gamma=gamma),rbf_kernel(v,x,gamma=gamma)))
        explicit=dict(linear=normalized_features(x,v),tangent=normalized_features(tx,tv));kernels={}
        for name in plan['classical_controls']:
            gram,cross,variance=normalize_kernel(*raw[name]);kernels[name]=(gram,cross,explicit.get(name),variance)
        for row,bx,bv,gram,cross in selected:
            np.testing.assert_array_equal(x,bx);np.testing.assert_array_equal(v,bv)
            g,b,variance=normalize_kernel(gram,cross);kernels[f'ZZ/{row["angle_scale"]}']=(g,b,None,variance)
        prior=next(s for s in old['seeds'] if s['group']=='diagnostic' and s['seed']==seed)
        meta=dict(seed=seed,training_rows=len(y),validation_rows=len(target),train_positive=int(y.sum()),validation_positive=int(target.sum()),
            train_indices_sha256=selected[0][0]['train_indices_sha256'],validation_indices_sha256=selected[0][0]['validation_indices_sha256'],rbf_gamma=gamma)
        assert (prior['train_indices_sha256'],prior['validation_indices_sha256'])==(meta['train_indices_sha256'],meta['validation_indices_sha256'])
        reference_metrics={new:next(row['metric'] for row in prior['rows'] if row['predictor']==previous)
            for new,previous in [('linear','linear/dense'),('rbf','rbf/dense'),('ZZ/0.05','ZZ/dense')]}
        samples.append((meta,kernels,y,target,reference_metrics))
    return parent_plan,samples

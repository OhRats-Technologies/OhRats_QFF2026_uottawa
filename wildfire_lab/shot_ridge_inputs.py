"""Fixed labels and exact reference kernels for a bounded noise-model check."""
import json
import numpy as np
import pandas as pd
from sklearn.metrics.pairwise import rbf_kernel,euclidean_distances
from wildfire_lab.geometry_inputs import load as matrix_load,sha
from wildfire_lab.evaluation import split,sample_indices
from wildfire_lab.encoding_screen import normalize_kernel
from wildfire_lab.landmarks import coordinates,indices


def load(root,plan):
    parent,conditions=matrix_load(root,plan['matrix_parent']);p=parent['parent_plan']
    source=root/p['dataset']/'features.csv';assert sha(source)==p['dataset_sha256']
    frame=pd.read_csv(source,usecols=['incident_id','year','target'])
    assert frame.year.between(1988,2018).all() and frame.incident_id.is_unique
    train,valid=split(frame,p['fold'],train_window=(1988,2018))
    ref=root/plan['ridge_reference'];assert sha(ref)==plan['ridge_reference_sha256']
    old=json.loads(ref.read_text());assert plan['kernel_ridge']==old['plan']['kernel_ridge']
    assert plan['landmark_ridge']==p['landmark_ridge'] and plan['eigenvalue_cutoff']==p['eigenvalue_cutoff']
    samples=[]
    for seed in plan['seeds']:
        selected=[r for r in conditions if r[0]['seed']==seed and r[0]['angle_scale']==plan['angle_scale']];assert len(selected)==1
        source_meta,x,v,gram,cross=selected[0];li=indices(len(x),plan['landmarks'],seed)
        ti=sample_indices(len(train),p['train_cap'],seed);vi=sample_indices(len(valid),p['validation_cap'],seed)
        y=train.iloc[ti].target.to_numpy();target=valid.iloc[vi].target.to_numpy()
        assert len(np.unique(y))==len(np.unique(target))==2
        d=euclidean_distances(x,squared=True)[np.triu_indices(len(x),1)];gamma=float(1/np.median(d[d>0]))
        kernels={}
        for name,(g,b) in dict(rbf=(rbf_kernel(x,gamma=gamma),rbf_kernel(v,x,gamma=gamma)),ZZ=(gram,cross)).items():
            k,c,var=normalize_kernel(g,b);kernels[name+'/dense']=(k,c,None,dict(raw_centered_variance=var))
            ft,fv,diagnostic=coordinates(g[np.ix_(li,li)],g[:,li],b[:,li],ridge=plan['landmark_ridge'],cutoff=plan['eigenvalue_cutoff'])
            kernels[name+'/ideal/16']=(ft@ft.T,fv@ft.T,(ft,fv),diagnostic)
        prior=next(r for r in old['seeds'] if r['group']=='diagnostic' and r['seed']==seed)
        meta=dict(seed=seed,train_rows=len(y),validation_rows=len(target),train_positive=int(y.sum()),validation_positive=int(target.sum()),
            train_indices_sha256=source_meta['train_indices_sha256'],validation_indices_sha256=source_meta['validation_indices_sha256'],landmark_indices=li.tolist(),rbf_gamma=gamma)
        assert all(prior[k]==meta[k] for k in ['train_indices_sha256','validation_indices_sha256'])
        reference={name:next(r['metric'] for r in prior['rows'] if r['predictor']==name) for name in kernels}
        samples.append((meta,gram,cross,kernels,y,target,reference))
    return p,samples

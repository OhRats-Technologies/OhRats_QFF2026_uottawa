"""Reconstruct frozen ideal inputs for fitting or read-only coefficient audits."""
import hashlib
import numpy as np
from sklearn.metrics.pairwise import rbf_kernel,euclidean_distances
from wildfire_lab.evaluation import sample_indices
from wildfire_lab.encoding_screen import preprocess,normalize_kernel
from wildfire_lab.kernel import angle_states,fidelity,angle_product_kernel
from wildfire_lab.landmarks import coordinates,indices
from wildfire_lab.ridge_kernel import normalized_features


def build(train,valid,parent,plan,seed):
    ti=sample_indices(len(train),parent['train_cap'],seed);vi=sample_indices(len(valid),parent['validation_cap'],seed)
    train,valid=train.iloc[ti],valid.iloc[vi];y=train.target.to_numpy();target=valid.target.to_numpy()
    if len(np.unique(y))!=2 or len(np.unique(target))!=2:raise ValueError('One-class capped sample')
    _,_,bx,bv=preprocess(train,valid,parent['features'],parent['preprocessing'])
    distances=euclidean_distances(bx,squared=True)[np.triu_indices(len(bx),1)]
    gamma=float(1/np.median(distances[distances>0]))
    angle=lambda x:np.pi*(.5+parent['angle_scale']*x)
    a,b=angle(bx),angle(bv);ta,tv=angle_states(a,parent['reps']),angle_states(b,parent['reps'])
    raw=dict(linear=(bx@bx.T,bv@bx.T),product=(angle_product_kernel(a,a),angle_product_kernel(b,a)),
        rbf=(rbf_kernel(bx,gamma=gamma),rbf_kernel(bv,bx,gamma=gamma)),ZZ=(fidelity(ta,ta),fidelity(tv,ta)))
    explicit=normalized_features(bx,bv);kernels={}
    for name in plan['dense_kernels']:
        gram,cross,variance=normalize_kernel(*raw[name])
        kernels[f'{name}/dense']=(gram,cross,explicit if name=='linear' else None,
            dict(raw_centered_variance=variance))
    landmarks={}
    for count in plan['landmark_counts']:
        li=indices(len(train),count,seed);landmarks[str(count)]=li.tolist()
        for name in ['rbf','ZZ']:
            gram,cross=raw[name]
            ft,fv,diagnostic=coordinates(gram[np.ix_(li,li)],gram[:,li],cross[:,li],
                ridge=parent['landmark_ridge'],cutoff=parent['eigenvalue_cutoff'])
            kernels[f'{name}/ideal/{count}']=(ft@ft.T,fv@ft.T,(ft,fv),diagnostic)
    meta=dict(seed=seed,train_rows=len(train),validation_rows=len(valid),
        train_positive=int(y.sum()),validation_positive=int(target.sum()),validation_target=target.tolist(),
        train_indices_sha256=hashlib.sha256(ti.tobytes()).hexdigest(),
        validation_indices_sha256=hashlib.sha256(vi.tobytes()).hexdigest(),landmark_indices=landmarks,
        simulated_state_preparations=len(train)+len(valid),new_pair_circuits=0,hardware_jobs_submitted=0,
        rbf_gamma=gamma)
    return kernels,y,target,meta

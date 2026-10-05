"""Aggregate independent pair measurements with shared landmark observations."""
import numpy as np
from wildfire_lab.landmarks import assemble,coordinates,pair_count


def probabilities(gram,cross,li):
    rest=np.setdiff1d(np.arange(len(gram)),li)
    blocks=dict(landmark=gram[np.ix_(li,li)],other=gram[np.ix_(rest,li)],validation=cross[:,li])
    assert all(np.isfinite(a).all() and a.min()>=-1e-10 and a.max()<=1+1e-10 for a in blocks.values())
    return {k:np.clip(v,0,1) for k,v in blocks.items()}


def draw(gram,cross,li,shots,cohort_seed,noise_seed):
    p=probabilities(gram,cross,li);rng=np.random.default_rng(np.random.SeedSequence([cohort_seed,noise_seed,shots]))
    size=len(li);upper=np.triu_indices(size,1);w=np.eye(size,dtype=np.int64)*shots
    values=rng.binomial(shots,p['landmark'][upper]);w[upper]=values;w[(upper[1],upper[0])]=values
    return dict(landmark=w,other=rng.binomial(shots,p['other']),validation=rng.binomial(shots,p['validation']))


def kernels(counts,gram,cross,li,shots,plan):
    p=probabilities(gram,cross,li)
    assert counts.keys()==p.keys()
    for name,a in counts.items():
        assert a.shape==p[name].shape and np.issubdtype(a.dtype,np.integer)
        assert a.min()>=0 and a.max()<=shots
    w=counts['landmark'];assert np.array_equal(w,w.T) and np.all(w.diagonal()==shots)
    measured={k:v/shots for k,v in counts.items()};a,b=assemble(measured['landmark'],measured['other'],measured['validation'],li,len(gram))
    ft,fv,diagnostic=coordinates(measured['landmark'],a,b,ridge=plan['landmark_ridge'],cutoff=plan['eigenvalue_cutoff'])
    n=pair_count(len(gram),len(cross),len(li));upper=np.triu_indices(len(li),1)
    error=np.concatenate([(measured['landmark']-p['landmark'])[upper],(measured['other']-p['other']).ravel(),(measured['validation']-p['validation']).ravel()])
    diagnostic.update(binomial_pair_estimates=n,modeled_shot_exposure=n*shots,raw_pair_rmse=float(np.sqrt(np.mean(error**2))))
    return ft@ft.T,fv@ft.T,(ft,fv),diagnostic

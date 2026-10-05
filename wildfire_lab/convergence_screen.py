"""Fixed-tolerance numerical checks without changing kernel design or labels."""
import time
import numpy as np
from sklearn.metrics.pairwise import rbf_kernel,euclidean_distances
from sklearn.svm import SVC
from wildfire_lab.evaluation import sample_indices,scores
from wildfire_lab.encoding_screen import preprocess,normalize_kernel
from wildfire_lab.kernel import angle_states,fidelity
from wildfire_lab.landmarks import coordinates,indices
from wildfire_lab.solver_diagnostics import diagnostics


def run(train,valid,parent,plan,seed,original,checkpoint):
    ti=sample_indices(len(train),parent['train_cap'],seed);vi=sample_indices(len(valid),parent['validation_cap'],seed)
    train,valid=train.iloc[ti],valid.iloc[vi];y=train.target.to_numpy();target=valid.target.to_numpy()
    _,_,bx,bv=preprocess(train,valid,parent['features'],parent['preprocessing'])
    d=euclidean_distances(bx,squared=True)[np.triu_indices(len(bx),1)];gamma=float(1/np.median(d[d>0]))
    angle=lambda x:np.pi*(.5+parent['angle_scale']*x)
    a,b=angle_states(angle(bx),parent['reps']),angle_states(angle(bv),parent['reps'])
    raw=fidelity(a,a);cross=fidelity(b,a)
    kernels={'rbf/dense':normalize_kernel(rbf_kernel(bx,gamma=gamma),rbf_kernel(bv,bx,gamma=gamma))[:2],
             'ZZ/dense':normalize_kernel(raw,cross)[:2]};features={}
    for count in parent['landmark_counts']:
        li=indices(len(train),count,seed)
        ft,fv,_=coordinates(raw[np.ix_(li,li)],raw[:,li],cross[:,li],
            ridge=parent['landmark_ridge'],cutoff=parent['eigenvalue_cutoff'])
        name=f'ZZ/ideal/{count}';kernels[name]=(ft@ft.T,fv@ft.T);features[name]=(ft,fv)
    source={r['predictor']:r for r in original['rows']};rows=[]
    for name in plan['kernels']:
        gram,validation=kernels[name]
        for tol in plan['tolerances']:
            representations=['precomputed','linear'] if name==plan['representation_control'] else \
                (['linear'] if name in features else ['precomputed'])
            for representation in representations:
                checkpoint(dict(seed=seed,status='fitting',rows=rows))
                start=time.perf_counter()
                model=SVC(C=plan['C'],kernel=representation,tol=tol,max_iter=plan['max_solver_iterations'])
                x,v=features[name] if representation=='linear' else (gram,validation)
                model.fit(x,y);prediction=model.decision_function(v)
                row=dict(predictor=name,tolerance=tol,representation=representation,
                    metric=scores(target,prediction,False),predictions=prediction.tolist(),
                    validation_decision_std=float(np.std(prediction)),validation_decision_range=float(np.ptp(prediction)),
                    validation_positive_predictions=int((prediction>0).sum()),seconds=time.perf_counter()-start,
                    **diagnostics(model,gram,y))
                if tol==plan['tolerances'][0] and representation==('linear' if name in features else 'precomputed'):
                    row['parent_prediction_max_abs_difference']=float(np.max(np.abs(prediction-source[name]['predictions'])))
                    assert row['parent_prediction_max_abs_difference']<=plan['decision_rules']['default_reproduction_atol']
                rows.append(row)
    return dict(seed=seed,train_rows=len(train),validation_rows=len(valid),train_positive=int(y.sum()),
        validation_positive=int(target.sum()),validation_target=target.tolist(),rows=rows,
        simulated_state_preparations=len(train)+len(valid),new_pair_circuits=0,hardware_jobs_submitted=0)

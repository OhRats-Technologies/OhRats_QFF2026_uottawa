"""Small paired library/shot pilot; caller supplies training-period rows only."""
import hashlib
import time
import numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.metrics.pairwise import rbf_kernel, euclidean_distances
from sklearn.svm import SVC
from qiskit.quantum_info import Statevector
from wildfire_lab.evaluation import sample_indices, scores, transform
from wildfire_lab.encoding_screen import preprocess, normalize_kernel
from wildfire_lab.kernel import angle_states, fidelity
from wildfire_lab.library_kernel import matrices, project_psd
from wildfire_lab.selection import fit_objective
from wildfire_lab.qaoa import select, circuit
from wildfire_lab.sqd_selection import sampled_subspace


def run(train, valid, plan, seed, checkpoint):
    ti=sample_indices(len(train),plan['train_cap'],seed)
    vi=sample_indices(len(valid),plan['validation_cap'],seed)
    train,valid=train.iloc[ti],valid.iloc[vi]
    y,target=train.target.to_numpy(),valid.target.to_numpy()
    if len(np.unique(y))<2 or len(np.unique(target))<2:
        return dict(seed=seed,status='one_class_sample')
    x,v,bx,bv=preprocess(train,valid,plan['features'],plan['preprocessing'])
    angles=np.pi*(.5+plan['angle_scale']*bx)
    val_angles=np.pi*(.5+plan['angle_scale']*bv)
    rows=[]
    def add(name,prediction,**extra):
        rows.append(dict(predictor=name,metric=scores(target,prediction,False),
                         predictions=prediction.tolist(),**extra))
    def svm(name,gram,cross,**extra):
        gram,cross,variance=normalize_kernel(gram,cross)
        start=time.perf_counter()
        model=SVC(C=plan['C'],kernel='precomputed').fit(gram,y)
        prediction=model.decision_function(cross)
        add(name,prediction,centered_variance=variance,
            fit_seconds=time.perf_counter()-start,**extra)
        return prediction
    start=time.perf_counter()
    model=LogisticRegression(C=plan['C'],max_iter=1000).fit(x,y)
    add('logistic',model.decision_function(v),fit_seconds=time.perf_counter()-start)
    distances=euclidean_distances(bx,squared=True)[np.triu_indices(len(bx),1)]
    gamma=float(1/np.median(distances[distances>0]))
    svm('rbf',rbf_kernel(bx,gamma=gamma),rbf_kernel(bv,bx,gamma=gamma),gamma=gamma)
    start=time.perf_counter()
    a,b=angle_states(angles,plan['reps']),angle_states(val_angles,plan['reps'])
    exact,exact_cross=fidelity(a,a),fidelity(b,a)
    direct=svm('cached_statevector',exact,exact_cross,
        kernel_seconds=time.perf_counter()-start,state_preparations=len(a)+len(b))
    for shots in [None,*plan['shots']]:
        checkpoint(dict(seed=seed,status='kernels_running',kernel_rows=rows,
            train_rows=len(train),validation_rows=len(valid),validation_target=target.tolist()))
        gram,cross,cost=matrices(angles,val_angles,shots=shots,seed=seed,reps=plan['reps'])
        diagnostic=dict(max_train_kernel_error=float(np.max(np.abs(gram-exact))),
            max_cross_kernel_error=float(np.max(np.abs(cross-exact_cross))),
            train_kernel_rmse=float(np.sqrt(np.mean((gram-exact)**2))),
            cross_kernel_rmse=float(np.sqrt(np.mean((cross-exact_cross)**2))))
        if shots is None:
            np.testing.assert_allclose(gram,exact,atol=1e-9)
            np.testing.assert_allclose(cross,exact_cross,atol=1e-9)
            prediction=svm('FidelityQuantumKernel/exact',gram,cross,**cost,**diagnostic)
            np.testing.assert_allclose(prediction,direct,atol=1e-7)
        else:
            repaired,repair=project_psd(gram)
            svm(f'FidelityQuantumKernel/{shots}/raw',gram,cross,**cost,**diagnostic,**repair)
            svm(f'FidelityQuantumKernel/{shots}/psd',repaired,cross,
                shared_measurements=True,**diagnostic,**repair)
    checkpoint(dict(seed=seed,status='kernels_complete',kernel_rows=rows,
        train_rows=len(train),validation_rows=len(valid),validation_target=target.tolist()))
    sx,_=transform(train,valid,plan['selection_features'])
    objective=fit_objective(sx,y,plan['sqd']['feature_count'],seed)
    _,qaoa=select(objective,seed=seed,**plan['sqd']['qaoa'])
    probabilities=(Statevector.from_instruction(circuit(objective,qaoa['parameters'])).probabilities()
                   if 'parameters' in qaoa else None)
    sqd=[]
    for source in (['qaoa','uniform'] if probabilities is not None else ['uniform']):
        rng=np.random.default_rng(seed)
        draws=rng.choice(2**len(plan['selection_features']),size=max(plan['sqd']['draw_budgets']),
                         p=probabilities if source=='qaoa' else None)
        for budget in plan['sqd']['draw_budgets']:
            sqd.append(dict(source=source,draw_budget=budget,
                            **sampled_subspace(objective,draws[:budget])))
    return dict(seed=seed,status='complete',train_rows=len(train),validation_rows=len(valid),
        train_positive=int(y.sum()),validation_positive=int(target.sum()),
        train_indices_sha256=hashlib.sha256(ti.tobytes()).hexdigest(),
        validation_indices_sha256=hashlib.sha256(vi.tobytes()).hexdigest(),
        validation_target=target.tolist(),kernel_rows=rows,sqd_rows=sqd,
        relevance=objective['relevance'].tolist(),all_zero_relevance=bool(not objective['relevance'].any()),
        qaoa=qaoa,qaoa_sampling_extra_state_preparations=int(probabilities is not None))

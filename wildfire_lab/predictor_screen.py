"""Small matched predictor screen: same columns, rows, C and train-only scaling."""
import time
import numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.svm import SVC
from sklearn.metrics.pairwise import rbf_kernel
from wildfire_lab.evaluation import scores, transform, sample_indices
from wildfire_lab.kernel import states, fidelity, product_rotation_kernel


def run(train, valid, plan, seed):
    config=plan["kernel_screen"]
    ti=sample_indices(len(train),config["train_cap"],seed)
    vi=sample_indices(len(valid),config["validation_cap"],seed)
    # Fit on precisely the same capped training rows for every predictor.
    train, valid=train.iloc[ti],valid.iloc[vi]
    x,v=transform(train,valid,config["features"])
    y,target=train.target.to_numpy(),valid.target.to_numpy()
    rows=[]
    start=time.perf_counter()
    model=LogisticRegression(C=config["C"],max_iter=1000).fit(x,y)
    rows.append(dict(predictor="logistic",metric=scores(target,model.predict_proba(v)[:,1]),seconds=time.perf_counter()-start))
    matrices={}
    for gamma in config.get("rbf_gamma_grid",[1/x.shape[1]]):
        start=time.perf_counter()
        name="rbf" if "rbf_gamma_grid" not in config else f"rbf_gamma_{gamma}"
        matrices[name]=(rbf_kernel(x,gamma=gamma),rbf_kernel(v,x,gamma=gamma),time.perf_counter()-start)
    for scale in config.get("angle_scale_grid",[.5]):
        start=time.perf_counter()
        suffix="" if "angle_scale_grid" not in config else f"_scale_{scale}"
        matrices["product_rotation"+suffix]=(product_rotation_kernel(x,x,scale),product_rotation_kernel(v,x,scale),time.perf_counter()-start)
        start=time.perf_counter()
        a,b=states(x,scale),states(v,scale)
        matrices["qiskit_ZZ_fidelity"+suffix]=(fidelity(a,a),fidelity(b,a),time.perf_counter()-start)
    for name,(gram,cross,kernel_seconds) in matrices.items():
        start=time.perf_counter()
        model=SVC(C=config["C"],kernel="precomputed").fit(gram,y)
        off=gram[np.triu_indices(len(gram),k=1)]
        rows.append(dict(predictor=name,metric=scores(target,model.decision_function(cross),probability=False),
                         kernel_seconds=kernel_seconds,fit_seconds=time.perf_counter()-start,
                         gram=dict(off_diagonal_mean=float(off.mean()),off_diagonal_std=float(off.std()),
                                   effective_rank=float(np.exp(-np.sum((p:=np.maximum(np.linalg.eigvalsh(gram),0)/np.trace(gram))[p>0]*np.log(p[p>0]))))),
                         quantum_circuits=len(x)+len(v) if name.startswith("qiskit_ZZ_fidelity") else 0))
    for row in rows:
        row.update(status="complete",seed=seed,features=config["features"],train_rows=len(train),validation_rows=len(valid),
                   train_indices_sha256=__import__("hashlib").sha256(ti.tobytes()).hexdigest(),
                   validation_indices_sha256=__import__("hashlib").sha256(vi.tobytes()).hexdigest())
    return rows

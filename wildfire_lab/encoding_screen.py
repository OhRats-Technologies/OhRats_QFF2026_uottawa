"""Bounded preprocessing ablation with equal rows and matched encoded kernels."""
import hashlib
import time
import numpy as np
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import StandardScaler, RobustScaler
from sklearn.linear_model import LogisticRegression
from sklearn.metrics.pairwise import rbf_kernel, euclidean_distances
from sklearn.svm import SVC
from wildfire_lab.evaluation import scores, sample_indices
from wildfire_lab.kernel import angle_states, fidelity, angle_product_kernel


def preprocess(train, valid, columns, variant):
    imputer=SimpleImputer(strategy='median',keep_empty_features=True)
    x=imputer.fit_transform(train[columns]);v=imputer.transform(valid[columns])
    scaler=RobustScaler() if variant=='robust_tanh' else StandardScaler()
    x=scaler.fit_transform(x);v=scaler.transform(v)
    bound=lambda a:np.clip(a/2,-1,1) if variant=='standard_clip' else np.tanh(a/2)
    return x,v,bound(x),bound(v)


def normalize_kernel(gram, cross):
    """Center from training means and match average centered training variance."""
    mean=gram.mean(axis=0);grand=mean.mean()
    centered=gram-mean[None,:]-mean[:,None]+grand
    variance=float(np.trace(centered)/len(gram))
    if variance<=1e-12:raise ValueError('Degenerate kernel variance')
    return centered/variance,(cross-cross.mean(axis=1)[:,None]-mean[None,:]+grand)/variance,variance


def run(train, valid, plan, seed):
    config=plan['encoding_screen'];columns=config['features']
    ti=sample_indices(len(train),config['train_cap'],seed)
    vi=sample_indices(len(valid),config['validation_cap'],seed)
    train,valid=train.iloc[ti],valid.iloc[vi]
    y,target=train.target.to_numpy(),valid.target.to_numpy();rows=[]
    def add(name,prediction,**extra):
        rows.append(dict(predictor=name,status='complete',seed=seed,features=columns,
                         metric=scores(target,prediction,probability=False),**extra))
        if plan.get('save_predictions'):rows[-1]['predictions']=prediction.tolist()
    start=time.perf_counter()
    x,v,_,_=preprocess(train,valid,columns,'standard_tanh')
    model=LogisticRegression(C=config['C'],max_iter=1000).fit(x,y)
    add('standard_logistic',model.decision_function(v),fit_seconds=time.perf_counter()-start)
    for variant in config['preprocessing']:
        start=time.perf_counter()
        x,v,bx,bv=preprocess(train,valid,columns,variant)
        prep_seconds=time.perf_counter()-start
        angles=np.pi*(.5+config['angle_scale']*bx)
        val_angles=np.pi*(.5+config['angle_scale']*bv)
        distances=euclidean_distances(bx,squared=True)[np.triu_indices(len(bx),1)]
        positive=distances[distances>0]
        gamma=float(1/np.median(positive))
        for kernel in config.get('kernels',['rbf','product_rotation','qiskit_ZZ']):
            start=time.perf_counter()
            if kernel=='rbf':
                gram,cross=rbf_kernel(bx,gamma=gamma),rbf_kernel(bv,bx,gamma=gamma)
            elif kernel=='product_rotation':
                gram,cross=angle_product_kernel(angles,angles),angle_product_kernel(val_angles,angles)
            else:
                a,b=angle_states(angles,config['reps']),angle_states(val_angles,config['reps'])
                gram,cross=fidelity(a,a),fidelity(b,a)
            off=gram[np.triu_indices(len(gram),1)]
            gram,cross,variance=normalize_kernel(gram,cross)
            kernel_seconds=time.perf_counter()-start
            start=time.perf_counter();model=SVC(C=config['C'],kernel='precomputed').fit(gram,y)
            simulated=len(x)+len(v) if kernel=='qiskit_ZZ' else 0
            add(variant+'/'+kernel,model.decision_function(cross),preprocess_seconds=prep_seconds,
                kernel_seconds=kernel_seconds,fit_seconds=time.perf_counter()-start,
                train_centered_variance=variance,raw_off_diagonal_mean=float(off.mean()),
                rbf_gamma=gamma if kernel=='rbf' else None,
                simulated_state_preparations=simulated,
                hardware_fidelity_pairs_if_naive=len(x)*(len(x)-1)//2+len(x)*len(v) if simulated else 0,
                hardware_jobs_submitted=0)
    for row in rows:
        row.update(train_rows=len(train),validation_rows=len(valid),
                   train_indices_sha256=hashlib.sha256(ti.tobytes()).hexdigest(),
                   validation_indices_sha256=hashlib.sha256(vi.tobytes()).hexdigest())
    return rows

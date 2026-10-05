"""Matched dense/landmark/shot prediction with explicit local query accounting."""
import hashlib
import time
import numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.metrics.pairwise import rbf_kernel,euclidean_distances
from sklearn.svm import SVC
from wildfire_lab.evaluation import sample_indices,scores
from wildfire_lab.encoding_screen import preprocess,normalize_kernel
from wildfire_lab.kernel import angle_states,fidelity
from wildfire_lab.library_kernel import matrices
from wildfire_lab.landmarks import coordinates,indices,pair_count,assemble


def run(train,valid,plan,seed,checkpoint,remaining_pairs):
    ti=sample_indices(len(train),plan['train_cap'],seed)
    vi=sample_indices(len(valid),plan['validation_cap'],seed)
    train,valid=train.iloc[ti],valid.iloc[vi]
    y,target=train.target.to_numpy(),valid.target.to_numpy()
    if len(np.unique(y))<2 or len(np.unique(target))<2:raise ValueError('One-class capped sample')
    start=time.perf_counter()
    x,v,bx,bv=preprocess(train,valid,plan['features'],plan['preprocessing'])
    prep_seconds=time.perf_counter()-start
    rows=[]
    def add(name,prediction,probability=False,**extra):
        rows.append(dict(predictor=name,metric=scores(target,prediction,probability),
                         probability=probability,predictions=prediction.tolist(),**extra))
    for name,model in dict(logistic=LogisticRegression(C=plan['C'],max_iter=1000),
        tree=HistGradientBoostingClassifier(max_iter=100,max_leaf_nodes=15,learning_rate=.05,
            l2_regularization=1.,early_stopping=False,random_state=seed)).items():
        start=time.perf_counter();model.fit(x,y)
        add(name,model.predict_proba(v)[:,1],probability=True,fit_seconds=time.perf_counter()-start)
    distance=euclidean_distances(bx,squared=True)[np.triu_indices(len(bx),1)]
    gamma=float(1/np.median(distance[distance>0]))
    angle=np.pi*(.5+plan['angle_scale']*bx)
    val_angle=np.pi*(.5+plan['angle_scale']*bv)
    start=time.perf_counter();a,b=angle_states(angle,plan['reps']),angle_states(val_angle,plan['reps'])
    state_seconds=time.perf_counter()-start
    kernel_pairs=dict(rbf=(rbf_kernel(bx,gamma=gamma),rbf_kernel(bv,bx,gamma=gamma)),
                      ZZ=(fidelity(a,a),fidelity(b,a)))
    dense={}
    for name,(gram,cross) in kernel_pairs.items():
        normalized,normalized_cross,_=normalize_kernel(gram,cross);dense[name]=(normalized,normalized_cross)
        start=time.perf_counter();model=SVC(C=plan['C'],kernel='precomputed').fit(normalized,y)
        add(name+'/dense',model.decision_function(normalized_cross),fit_seconds=time.perf_counter()-start)
    def landmark_model(name,w,ct,cv,reference,cost=None):
        start=time.perf_counter()
        ft,fv,diagnostic=coordinates(w,ct,cv,ridge=plan['landmark_ridge'],cutoff=plan['eigenvalue_cutoff'])
        gram,cross=ft@ft.T,fv@ft.T
        normalized,normalized_cross=reference
        diagnostic.update(train_relative_frobenius_error=float(np.linalg.norm(gram-normalized)/np.linalg.norm(normalized)),
            validation_relative_frobenius_error=float(np.linalg.norm(cross-normalized_cross)/np.linalg.norm(normalized_cross)))
        model=SVC(C=plan['C'],kernel='linear').fit(ft,y)
        add(name,model.decision_function(fv),feature_and_fit_seconds=time.perf_counter()-start,
            **diagnostic,**(cost or {}))
    landmarks={}
    for count in plan['landmark_counts']:
        li=indices(len(train),count,seed);landmarks[str(count)]=li.tolist()
        for name,(gram,cross) in kernel_pairs.items():
            landmark_model(f'{name}/ideal/{count}',gram[np.ix_(li,li)],gram[:,li],cross[:,li],dense[name])
    count=plan['shot_landmarks'];li=np.array(landmarks[str(count)])
    rest=np.setdiff1d(np.arange(len(train)),li);used=0
    expected=pair_count(len(train),len(valid),count)
    for shots in plan['shots']:
        checkpoint(dict(seed=seed,status='shot_kernels_running',rows=rows))
        if expected>remaining_pairs-used:raise ValueError('Declared pair-circuit cap exhausted')
        w,cross,cost=matrices(angle[li],np.vstack([angle[rest],val_angle]),shots=shots,seed=seed,reps=plan['reps'])
        assert cost['pair_circuits']==expected
        used+=cost['pair_circuits']
        ct,cv=assemble(w,cross[:len(rest)],cross[len(rest):],li,len(train))
        landmark_model(f'ZZ/{shots}/{count}',w,ct,cv,dense['ZZ'],cost)
    return dict(seed=seed,train_rows=len(train),validation_rows=len(valid),
        train_positive=int(y.sum()),validation_positive=int(target.sum()),validation_target=target.tolist(),
        train_indices_sha256=hashlib.sha256(ti.tobytes()).hexdigest(),
        validation_indices_sha256=hashlib.sha256(vi.tobytes()).hexdigest(),landmark_indices=landmarks,
        pair_circuits=used,dense_pair_reference=len(train)*(len(train)-1)//2+len(train)*len(valid),
        per_shot_pair_fraction=expected/(len(train)*(len(train)-1)//2+len(train)*len(valid)),
        simulated_state_preparations=len(train)+len(valid),state_seconds=state_seconds,
        preprocess_seconds=prep_seconds,rbf_gamma=gamma,rows=rows)

"""Same-label selector controls and one fixed downstream logistic model."""
import hashlib
import numpy as np
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LogisticRegression
from wildfire_lab.evaluation import sample_indices,scores
from wildfire_lab.selection import fit_objective,configurations,energies,exact_subset
from wildfire_lab.constrained_qaoa import select


def sampled(train,valid,parent,seed):
    ti=sample_indices(len(train),parent['train_cap'],seed);vi=sample_indices(len(valid),parent['validation_cap'],seed)
    return train.iloc[ti],valid.iloc[vi],dict(train_indices_sha256=hashlib.sha256(ti.tobytes()).hexdigest(),
        validation_indices_sha256=hashlib.sha256(vi.tobytes()).hexdigest())


def run(train,valid,parent,plan,seed,group,checkpoint):
    train,valid,hashes=sampled(train,valid,parent,seed);columns=plan['features'];y=train.target.to_numpy()
    if set(np.unique(y))!={0,1} or set(valid.target.unique())!={0,1}:raise ValueError('Frozen sample needs both classes')
    imputer=SimpleImputer(strategy='median',keep_empty_features=True);x=imputer.fit_transform(train[columns]);v=imputer.transform(valid[columns])
    scaler=StandardScaler().fit(x);x,v=scaler.transform(x),scaler.transform(v)
    preprocessing=dict(median=imputer.statistics_.tolist(),mean=scaler.mean_.tolist(),scale=scaler.scale_.tolist())
    objective=fit_objective(x,y,plan['feature_count'],seed);bits=configurations(len(columns));cost=energies(objective,bits)
    feasible=np.flatnonzero(bits.sum(axis=1)==plan['feature_count']);exact,minimum=exact_subset(objective)
    rows=[];quantum=[]
    def add(name,indices,**extra):
        if indices is None:
            rows.append(dict(selector=name,status='no_feasible_draw',**extra));return
        model=LogisticRegression(**plan['logistic']).fit(x[:,indices],y)
        prediction=model.decision_function(v[:,indices]);b=np.zeros(len(columns));b[indices]=1
        rows.append(dict(selector=name,status='complete',indices=indices,features=[columns[i] for i in indices],
            selected_objective=float(energies(objective,b[None,:])[0]),objective_gap=float(energies(objective,b[None,:])[0]-minimum),
            coefficient=model.coef_[0].tolist(),intercept=float(model.intercept_[0]),iterations=int(model.n_iter_[0]),
            predictions=prediction.tolist(),metric=scores(valid.target.to_numpy(),prediction,False),**extra))
    add('exact',exact)
    l1=LogisticRegression(**plan['l1'],random_state=seed).fit(x,y)
    add('l1',np.argsort(-np.abs(l1.coef_[0]),kind='stable')[:plan['feature_count']].tolist(),
        l1_iterations=int(l1.n_iter_[0]),l1_coefficient=l1.coef_[0].tolist())
    for name in ['uniform_all','uniform_feasible']:
        rng=np.random.default_rng(seed);draws=rng.choice(len(bits) if name=='uniform_all' else feasible,size=plan['shots'])
        eligible=draws[bits[draws].sum(axis=1)==plan['feature_count']]
        chosen=int(eligible[np.argmin(cost[eligible])]) if len(eligible) else None
        add(name,np.flatnonzero(bits[chosen]).tolist() if chosen is not None else None,draws=draws.tolist(),feasible_draws=len(eligible))
    for initial in plan['initial_states']:
        for mixer in plan['mixers']:
            checkpoint(dict(seed=seed,group=group,quantum=quantum,rows=rows))
            diagnostic=select(objective,initial,mixer,seed,plan);quantum.append(diagnostic)
            add(initial+'/'+mixer,diagnostic['selected_indices'])
            checkpoint(dict(seed=seed,group=group,quantum=quantum,rows=rows))
    return dict(seed=seed,group=group,train_rows=len(train),validation_rows=len(valid),train_positive=int(y.sum()),
        validation_positive=int(valid.target.sum()),**hashes,preprocessing=preprocessing,
        objective={k:v.tolist() if isinstance(v,np.ndarray) else v for k,v in objective.items()},
        exact_objective=minimum,quantum=quantum,rows=rows)

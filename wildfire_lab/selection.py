"""Matched relevance/redundancy subset objective and exact classical control."""
import numpy as np
from sklearn.feature_selection import mutual_info_classif


def fit_objective(x, y, k, seed=7, redundancy_weight=.5, penalty=2.):
    relevance = np.asarray(mutual_info_classif(x, y, random_state=seed), dtype=float)
    relevance /= max(float(relevance.max()), 1e-12)
    redundancy = np.nan_to_num(np.abs(np.corrcoef(x, rowvar=False)), nan=0.)
    np.fill_diagonal(redundancy, 0.)
    pairs = max(1, k * (k-1) / 2)
    linear = -relevance/k + penalty*(1-2*k)
    pair = np.triu(redundancy_weight*redundancy/pairs + 2*penalty, k=1)
    return dict(relevance=relevance, redundancy=redundancy, linear=linear,
                pair=pair, constant=penalty*k*k, k=k, penalty=penalty)


def configurations(n):
    return ((np.arange(2**n)[:, None] >> np.arange(n)) & 1).astype(float)


def energies(objective, bits):
    return bits @ objective["linear"] + np.einsum("bi,ij,bj->b", bits, objective["pair"], bits) + objective["constant"]


def exact_subset(objective):
    bits = configurations(len(objective["linear"]))
    eligible = np.flatnonzero(bits.sum(axis=1) == objective["k"])
    cost = energies(objective, bits)
    best = eligible[np.argmin(cost[eligible])]
    return np.flatnonzero(bits[best]).tolist(), float(cost[best])


def ising(objective):
    """x=(1-Z)/2 with each off-diagonal pair represented once."""
    pair = objective["pair"]
    single = -.5*objective["linear"] -.25*(pair.sum(axis=0)+pair.sum(axis=1))
    coupled = .25*pair
    constant = objective["constant"] + .5*objective["linear"].sum() + .25*pair.sum()
    return single, coupled, float(constant)


def subset_choices(x,y,k,seed,qaoa_config):
    """Use one training array for every classical/quantum selector."""
    import time
    from sklearn.linear_model import LogisticRegression
    from wildfire_lab.qaoa import select
    start=time.perf_counter();objective=fit_objective(x,y,k,seed=seed)
    objective_seconds=time.perf_counter()-start
    start=time.perf_counter();exact,cost=exact_subset(objective)
    exact_seconds=time.perf_counter()-start
    quantum,diagnostic=select(objective,seed=seed,**qaoa_config)
    rng=np.random.default_rng(seed)
    subsets=dict(all_features=list(range(x.shape[1])),
        mutual_information=np.argsort(-objective['relevance'],kind='stable')[:k].tolist(),
        classical_qubo=exact,qaoa_same_qubo=quantum,
        random_subset=np.sort(rng.choice(x.shape[1],k,replace=False)).tolist())
    bits=configurations(x.shape[1]);draws=np.random.default_rng(seed).integers(len(bits),size=qaoa_config['shots'])
    feasible=draws[bits[draws].sum(axis=1)==k];costs=energies(objective,bits)
    subsets['uniform_shot_search']=np.flatnonzero(bits[feasible[np.argmin(costs[feasible])]]).tolist() if len(feasible) else None
    l1=LogisticRegression(C=.1,solver='liblinear',l1_ratio=1.,max_iter=1000,random_state=seed).fit(x,y)
    subsets['l1_ranking']=np.argsort(-np.abs(l1.coef_[0]),kind='stable')[:k].tolist()
    return subsets,objective,dict(exact_objective=cost,objective_fit_seconds=objective_seconds,
                                 exact_seconds=exact_seconds,qaoa=diagnostic)

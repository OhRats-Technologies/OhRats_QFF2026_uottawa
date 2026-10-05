"""Equal-budget selectors evaluated with the same logistic predictor."""
import time
import numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import HistGradientBoostingClassifier
from wildfire_lab.evaluation import scores, transform
from wildfire_lab.selection import subset_choices, energies


def run(train, valid, plan, seed):
    columns, k = plan["features"], plan["feature_budget"]
    x, v = transform(train, valid, columns)
    y, target = train.target.to_numpy(), valid.target.to_numpy()
    subsets,objective,metadata=subset_choices(x,y,k,seed,plan['qaoa'])
    cost,objective_seconds=metadata['exact_objective'],metadata['objective_fit_seconds']
    exact_seconds,diagnostic=metadata['exact_seconds'],metadata['qaoa']
    rows = []
    for selector, chosen in subsets.items():
        if chosen is None:
            rows.append(dict(selector=selector, status="no_feasible_sample", qaoa=diagnostic))
            continue
        started = time.perf_counter()
        model = LogisticRegression(C=1., max_iter=1000, random_state=seed).fit(x[:,chosen],y)
        bit = np.zeros((1,len(columns))); bit[0,chosen] = 1
        rows.append(dict(selector=selector, predictor="logistic_C1", status="complete", seed=seed,
                         features=[columns[i] for i in chosen], metric=scores(target, model.predict_proba(v[:,chosen])[:,1]),
                         fit_seconds=time.perf_counter()-started, objective=float(energies(objective,bit)[0]),
                         exact_objective=cost, objective_fit_seconds=objective_seconds,
                         selector_seconds=exact_seconds if selector=="classical_qubo" else diagnostic["seconds"] if selector=="qaoa_same_qubo" else None,
                         qaoa=diagnostic if selector=="qaoa_same_qubo" else None))
    # Full-input prediction controls; these are not equal-feature-budget selector comparisons.
    for name, chosen, model in [
        ("seasonal_logistic", [columns.index(c) for c in ["month_sin","month_cos","latitude","longitude"]], LogisticRegression(C=1.,max_iter=1000)),
        ("tree_all", list(range(len(columns))), HistGradientBoostingClassifier(max_iter=100,max_leaf_nodes=15,learning_rate=.05,l2_regularization=1.,early_stopping=False,random_state=seed)),
    ]:
        started=time.perf_counter(); model.fit(x[:,chosen],y)
        rows.append(dict(selector="fixed_control",predictor=name,status="complete",seed=seed,
                         features=[columns[i] for i in chosen],metric=scores(target,model.predict_proba(v[:,chosen])[:,1]),fit_seconds=time.perf_counter()-started))
    return rows

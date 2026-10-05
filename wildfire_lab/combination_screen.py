"""Cross selectors/predictors under the same capped training-label budget."""
import copy
import hashlib
import time
import numpy as np
from wildfire_lab.evaluation import sample_indices, transform
from wildfire_lab.selection import subset_choices, energies
from wildfire_lab.encoding_screen import run as predictors


def run(train,valid,plan,seed):
    config=plan['encoding_screen'];columns=plan['features']
    ti=sample_indices(len(train),config['train_cap'],seed)
    vi=sample_indices(len(valid),config['validation_cap'],seed)
    train,valid=train.iloc[ti],valid.iloc[vi]
    x,_=transform(train,valid,columns)
    start=time.perf_counter()
    subsets,objective,diagnostics=subset_choices(x,train.target.to_numpy(),plan['feature_budget'],seed,plan['qaoa'])
    total_seconds=time.perf_counter()-start
    rows=[];cache={}
    for selector in plan['selectors']:
        chosen=subsets[selector]
        if chosen is None:
            rows.append(dict(selector=selector,status='no_feasible_sample',seed=seed))
            continue
        key=tuple(sorted(chosen));reused=key in cache
        if not reused:
            local=dict(plan,encoding_screen=dict(config,features=[columns[j] for j in key]))
            cache[key]=predictors(train,valid,local,seed)
        bit=np.zeros((1,len(columns)));bit[0,chosen]=1
        for row in copy.deepcopy(cache[key]):
            row.update(group=selector,selection_train_rows=len(train),selection_features=columns,
                       selection_objective=float(energies(objective,bit)[0]),selection=diagnostics,
                       all_selectors_seconds=total_seconds,prediction_reused=reused,
                       train_indices_sha256=hashlib.sha256(ti.tobytes()).hexdigest(),
                       validation_indices_sha256=hashlib.sha256(vi.tobytes()).hexdigest())
            if reused:
                row['simulated_state_preparations']=0
                row['hardware_fidelity_pairs_if_naive']=0
            rows.append(row)
    return rows

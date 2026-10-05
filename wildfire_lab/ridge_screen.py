"""Matched ideal kernel prediction under one fixed smooth objective."""
import time
from wildfire_lab.evaluation import scores
from wildfire_lab.ridge_inputs import build
from wildfire_lab.ridge_kernel import predict


def run(train,valid,parent,plan,seed,group,checkpoint):
    start=time.perf_counter();kernels,y,target,meta=build(train,valid,parent,plan,seed);rows=[]
    for name,(gram,cross,features,extra) in kernels.items():
        checkpoint(dict(seed=seed,status='solving',rows=rows));before=time.perf_counter()
        prediction,diagnostic=predict(gram,cross,y,ridge=plan['kernel_ridge'],features=features)
        rows.append(dict(predictor=name,metric=scores(target,prediction,False),predictions=prediction.tolist(),
            solve_seconds=time.perf_counter()-before,**diagnostic,**extra))
    return dict(**meta,group=group,seconds=time.perf_counter()-start,rows=rows)

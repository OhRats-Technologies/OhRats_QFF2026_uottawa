"""Covariate ablations with fixed model settings and chronological rows."""
import time
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import HistGradientBoostingClassifier
from wildfire_lab.evaluation import transform, scores


def run(train, valid, plan, seed):
    rows=[]
    y,target=train.target.to_numpy(),valid.target.to_numpy()
    for group,columns in plan['feature_groups'].items():
        start=time.perf_counter()
        x,v=transform(train,valid,columns)
        prep_seconds=time.perf_counter()-start
        models=dict(logistic=LogisticRegression(C=1.,max_iter=1000,random_state=seed),
                    tree=HistGradientBoostingClassifier(max_iter=100,max_leaf_nodes=15,learning_rate=.05,l2_regularization=1.,early_stopping=False,random_state=seed))
        for name,model in models.items():
            start=time.perf_counter();model.fit(x,y)
            prediction=model.predict_proba(v)[:,1]
            row=dict(predictor=name,group=group,status='complete',seed=seed,features=columns,
                     metric=scores(target,prediction),preprocess_seconds=prep_seconds,fit_seconds=time.perf_counter()-start)
            if plan.get('save_predictions'):row['predictions']=prediction.tolist()
            if plan.get('report_per_year'):
                row['metrics_by_year']={}
                for year in sorted(valid.year.unique()):
                    mask=valid.year.eq(year).to_numpy();labels=target[mask]
                    metric=scores(labels,prediction[mask]) if len(set(labels))==2 else dict(status='one_class',rows=len(labels),prevalence=float(labels.mean()))
                    row['metrics_by_year'][str(year)]=metric
            rows.append(row)
    return rows

"""Fixed shot-noise ridge experiment and read-only coefficient reconstruction."""
import numpy as np
from wildfire_lab.evaluation import scores
from wildfire_lab.geometry_inputs import sha
from wildfire_lab.ridge_kernel import predict
from wildfire_lab.ridge_checks import verify
from wildfire_lab.landmark_noise import draw,kernels as noisy_kernels


def check(row,kernel,y,target,plan):
    gram,cross,features,diagnostic=kernel;checks=verify(row,gram,cross,features,y,target,plan['kernel_ridge'])
    assert checks['relative_solve_residual']<=plan['relative_solve_residual_max']
    if features is not None:
        assert checks['primal_relative_solve_residual']<=plan['relative_solve_residual_max']
        assert checks['primal_dual_prediction_max_abs_difference']<=plan['primal_dual_difference_max']
    assert row['validation_score_std']>=plan['score_std_min']
    for k,v in diagnostic.items():np.testing.assert_allclose(row['kernel_diagnostic'][k],v,rtol=1e-9,atol=1e-12)
    return checks


def fit(name,kernel,y,target,plan,**extra):
    gram,cross,features,diagnostic=kernel;p,certificate=predict(gram,cross,y,ridge=plan['kernel_ridge'],features=features)
    row=dict(predictor=name,metric=scores(target,p,False),predictions=p.tolist(),kernel_diagnostic=diagnostic,**certificate,**extra)
    check(row,kernel,y,target,plan);return row


def run(sample,plan,cache):
    meta,gram,cross,controls,y,target,reference=sample;rows=[]
    for name,kernel in controls.items():
        row=fit(name,kernel,y,target,plan)
        for key,value in reference[name].items():np.testing.assert_allclose(row['metric'][key],value,rtol=0,atol=plan['reference_metric_tolerance'])
        rows.append(row)
    li=np.asarray(meta['landmark_indices'])
    for shots in plan['shots']:
        for seed in plan['noise_seeds']:
            counts=draw(gram,cross,li,shots,meta['seed'],seed);name=f'counts-{meta["seed"]}-{shots}-{seed}.npz';path=cache/name
            with path.open('xb') as f:np.savez_compressed(f,**counts)
            kernel=noisy_kernels(counts,gram,cross,li,shots,plan)
            rows.append(fit(f'ZZ/shot/{shots}/{seed}',kernel,y,target,plan,shots=shots,noise_seed=seed,matrix_file=name,matrix_sha256=sha(path)))
    return dict(**meta,rows=rows,reference_metrics_match=True)


def audit(sample,record,plan,cache):
    meta,gram,cross,controls,y,target,reference=sample
    for k,v in meta.items():assert record[k]==v,k
    expected=set(controls)|{f'ZZ/shot/{s}/{n}' for s in plan['shots'] for n in plan['noise_seeds']}
    rows={r['predictor']:r for r in record['rows']};assert len(rows)==len(record['rows']) and set(rows)==expected
    checks=[]
    for name,kernel in controls.items():
        checks.append(check(rows[name],kernel,y,target,plan))
        for k,v in reference[name].items():np.testing.assert_allclose(rows[name]['metric'][k],v,rtol=0,atol=plan['reference_metric_tolerance'])
    li=np.asarray(meta['landmark_indices'])
    for shots in plan['shots']:
        for seed in plan['noise_seeds']:
            row=rows[f'ZZ/shot/{shots}/{seed}'];assert row['shots']==shots and row['noise_seed']==seed
            path=cache/row['matrix_file'];assert path.parent==cache and sha(path)==row['matrix_sha256']
            with np.load(path,allow_pickle=False) as arrays:counts={k:arrays[k].copy() for k in arrays.files}
            checks.append(check(row,noisy_kernels(counts,gram,cross,li,shots,plan),y,target,plan))
    assert record['reference_metrics_match']
    return dict(predictor_conditions=len(rows),primal_reference_solves=sum('primal_relative_solve_residual' in c for c in checks),
        max_relative_solve_residual=max(max(c['relative_solve_residual'],c.get('primal_relative_solve_residual',0)) for c in checks),
        max_primal_dual_difference=max(c.get('primal_dual_prediction_max_abs_difference',0) for c in checks))


def review(records,plan):
    def ap(row):return row['metric']['average_precision']
    controls={name:float(np.mean([ap(next(r for r in s['rows'] if r['predictor']==name)) for s in records]))
              for name in ['rbf/dense','rbf/ideal/16','ZZ/dense','ZZ/ideal/16']}
    summary={}
    for shots in plan['shots']:
        cohorts=[]
        for record in records:
            ideal=ap(next(r for r in record['rows'] if r['predictor']=='ZZ/ideal/16'))
            rows=[r for r in record['rows'] if r.get('shots')==shots];assert len(rows)==len(plan['noise_seeds'])
            values=[ap(r) for r in rows];cohorts.append(dict(seed=record['seed'],mean_ap=float(np.mean(values)),ap_range=[min(values),max(values)],ideal_ap=ideal,mean_loss=ideal-float(np.mean(values))))
        summary[str(shots)]=dict(mean_ap=float(np.mean([r['mean_ap'] for r in cohorts])),mean_loss=float(np.mean([r['mean_loss'] for r in cohorts])),cohorts=cohorts)
    gate=plan['quality_gate'];primary=summary[str(gate['shots'])]
    checks=dict(mean_loss=primary['mean_loss']<=gate['mean_ap_loss_max'],cohort_tolerance=sum(r['mean_loss']<=gate['cohort_mean_ap_loss_max'] for r in primary['cohorts'])>=gate['cohorts_within_min'])
    return dict(control_mean_ap=controls,noise=summary,quality_checks=checks,quality_gate=all(checks.values()),interpretation=plan['interpretation'])

"""Matched ridge predictions and a deterministic kernel perturbation bound."""
import time
import numpy as np
from scipy.stats import spearmanr
from wildfire_lab.evaluation import scores
from wildfire_lab.ridge_kernel import predict
from wildfire_lab.ridge_checks import verify


def comparison(exact,tangent,exact_kernels,tangent_kernels,ridge):
    ke,be=exact_kernels[:2];kt,bt=tangent_kernels[:2]
    f=np.asarray(exact['predictions']);g=np.asarray(tangent['predictions']);a=np.asarray(tangent['coefficients'])
    minimum=float(np.linalg.eigvalsh((ke+ke.T)/2).min()+ridge)
    if minimum<=0:raise ValueError('Unstable regularized exact kernel')
    delta_k=float(np.linalg.norm(kt-ke,2));delta_b=float(np.linalg.norm(bt-be,2));cross=float(np.linalg.norm(be,2))
    bound=(cross*delta_k/minimum+delta_b)*np.linalg.norm(a);actual=np.linalg.norm(f-g)
    assert actual<=bound*(1+1e-9)+1e-8
    centered=np.linalg.norm(f-exact['training_intercept'])
    return dict(ZZ_minus_tangent_ap=exact['metric']['average_precision']-tangent['metric']['average_precision'],
        prediction_rmse=float(np.sqrt(np.mean((f-g)**2))),prediction_max_abs_difference=float(np.max(np.abs(f-g))),
        prediction_relative_l2_vs_exact_centered=float(actual/centered),prediction_spearman=float(spearmanr(f,g).statistic),
        prediction_l2_difference=float(actual),prediction_l2_bound=float(bound),regularized_exact_min_eigenvalue=minimum,
        normalized_train_delta_spectral_norm=delta_k,normalized_cross_delta_spectral_norm=delta_b)


def run(sample,plan):
    meta,kernels,y,target,reference=sample;rows=[];start=time.perf_counter()
    for name,(gram,cross,features,variance) in kernels.items():
        before=time.perf_counter();prediction,diagnostic=predict(gram,cross,y,ridge=plan['kernel_ridge'],features=features)
        row=dict(predictor=name,metric=scores(target,prediction,False),predictions=prediction.tolist(),
            raw_centered_variance=variance,solve_seconds=time.perf_counter()-before,**diagnostic)
        checks=verify(row,gram,cross,features,y,target,plan['kernel_ridge'])
        assert checks['relative_solve_residual']<=plan['numerical_checks']['relative_solve_residual_max']
        if features is not None:
            assert checks['primal_relative_solve_residual']<=plan['numerical_checks']['relative_solve_residual_max']
            assert checks['primal_dual_prediction_max_abs_difference']<=plan['numerical_checks']['primal_dual_prediction_difference_max']
        assert row['validation_score_std']>=plan['numerical_checks']['validation_score_std_min'];rows.append(row)
    indexed={r['predictor']:r for r in rows}
    for name,metrics in reference.items():
        for key,value in metrics.items():np.testing.assert_allclose(indexed[name]['metric'][key],value,atol=plan['numerical_checks']['reference_metric_tolerance'],rtol=0)
    comparisons=[dict(angle_scale=a,**comparison(indexed[f'ZZ/{a}'],indexed['tangent'],kernels[f'ZZ/{a}'],kernels['tangent'],plan['kernel_ridge'])) for a in plan['angle_scales']]
    return dict(**meta,rows=rows,comparisons=comparisons,reference_metrics_match=True,seconds=time.perf_counter()-start)


def review(records,plan):
    names=[r['predictor'] for r in records[0]['rows']]
    means={name:float(np.mean([next(r['metric']['average_precision'] for r in s['rows'] if r['predictor']==name) for s in records])) for name in names}
    per_scale={}
    for scale in plan['angle_scales']:
        pairs=[next(r for r in s['comparisons'] if r['angle_scale']==scale) for s in records]
        per_scale[str(scale)]=dict(mean_ZZ_minus_tangent_ap=float(np.mean([r['ZZ_minus_tangent_ap'] for r in pairs])),
            mean_absolute_ap_difference=float(np.mean([abs(r['ZZ_minus_tangent_ap']) for r in pairs])),
            max_seed_absolute_ap_difference=max(abs(r['ZZ_minus_tangent_ap']) for r in pairs),
            min_prediction_spearman=min(r['prediction_spearman'] for r in pairs),
            mean_prediction_rmse=float(np.mean([r['prediction_rmse'] for r in pairs])))
    gate=plan['narrow_closeness_gate'];narrow=per_scale[str(gate['angle_scale'])]
    checks=dict(mean_ap=narrow['mean_absolute_ap_difference']<=gate['mean_absolute_ap_difference_max'],
        each_seed_ap=narrow['max_seed_absolute_ap_difference']<=gate['seed_absolute_ap_difference_max'],
        rank_agreement=narrow['min_prediction_spearman']>=gate['prediction_spearman_min'])
    return dict(mean_ap=means,per_scale=per_scale,narrow_closeness_checks=checks,narrow_closeness_gate=all(checks.values()),
        interpretation='Operational tolerances on three dependent reused-year samples, not statistical equivalence or model selection.')

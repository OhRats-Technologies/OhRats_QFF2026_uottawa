"""Audit saved ridge coefficients and comparisons without solving or fitting."""
import numpy as np
from wildfire_lab.ridge_checks import verify
from wildfire_lab.tangent_prediction import comparison


def validate(sample,record,plan):
    meta,kernels,y,target,reference=sample
    for key,value in meta.items():assert record[key]==value,key
    rows={row['predictor']:row for row in record['rows']};assert len(rows)==len(record['rows']) and rows.keys()==kernels.keys()
    residuals=[];primal=[];differences=[]
    for name,(gram,cross,features,variance) in kernels.items():
        row=rows[name];np.testing.assert_allclose(row['raw_centered_variance'],variance,atol=1e-12)
        checks=verify(row,gram,cross,features,y,target,plan['kernel_ridge']);residuals.append(checks['relative_solve_residual'])
        if features is not None:
            primal.append(checks['primal_relative_solve_residual']);differences.append(checks['primal_dual_prediction_max_abs_difference'])
        assert row['validation_score_std']>=plan['numerical_checks']['validation_score_std_min']
    assert max(residuals+primal)<=plan['numerical_checks']['relative_solve_residual_max']
    assert max(differences)<=plan['numerical_checks']['primal_dual_prediction_difference_max']
    for name,metrics in reference.items():
        for key,value in metrics.items():np.testing.assert_allclose(rows[name]['metric'][key],value,atol=plan['numerical_checks']['reference_metric_tolerance'],rtol=0)
    assert record['reference_metrics_match'] and len(record['comparisons'])==len(plan['angle_scales'])
    for scale,row in zip(plan['angle_scales'],record['comparisons']):
        assert row['angle_scale']==scale
        actual=comparison(rows[f'ZZ/{scale}'],rows['tangent'],kernels[f'ZZ/{scale}'],kernels['tangent'],plan['kernel_ridge'])
        for key,value in actual.items():np.testing.assert_allclose(row[key],value,atol=1e-9,rtol=1e-9)
    return dict(predictor_conditions=len(rows),primal_reference_solves=len(primal),
        max_relative_solve_residual=max(residuals+primal),max_primal_dual_prediction_difference=max(differences))

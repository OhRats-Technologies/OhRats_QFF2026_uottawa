"""Verify stored ridge coefficients against reconstructed inputs; never solve or fit."""
import numpy as np
from wildfire_lab.evaluation import scores


def verify(row,gram,cross,features,y,target,ridge):
    signed=2*np.asarray(y,dtype=float)-1;mean=float(signed.mean());centered=signed-mean
    matrix=(gram+gram.T)/2;alpha=np.asarray(row['coefficients']);prediction=np.asarray(row['predictions'])
    assert alpha.shape==(len(y),) and prediction.shape==(len(target),)
    np.testing.assert_allclose(cross@alpha+mean,prediction,atol=1e-10,rtol=1e-10)
    recomputed=scores(target,prediction,False)
    for key,value in row['metric'].items():np.testing.assert_allclose(value,recomputed[key],atol=1e-12)
    residual=float(np.linalg.norm((matrix+ridge*np.eye(len(y)))@alpha-centered)/np.linalg.norm(centered))
    np.testing.assert_allclose(residual,row['relative_solve_residual'],atol=1e-12)
    fitted=matrix@alpha+mean
    for key,value in dict(training_score_std=np.std(fitted),validation_score_std=np.std(prediction),
        validation_score_range=np.ptp(prediction),training_intercept=mean,
        training_squared_error=np.sum((signed-fitted)**2),squared_feature_weight_norm=alpha@matrix@alpha).items():
        np.testing.assert_allclose(value,row[key],atol=1e-10)
    assert row['kernel_ridge']==ridge
    report=dict(relative_solve_residual=residual)
    if features is not None:
        x,v=features;weight=np.asarray(row['primal_coefficients'])
        assert weight.shape==(x.shape[1],)
        rhs=x.T@centered
        primal=float(np.linalg.norm((x.T@x+ridge*np.eye(x.shape[1]))@weight-rhs)/max(np.linalg.norm(rhs),1e-15))
        difference=float(np.max(np.abs(v@weight+mean-prediction)))
        np.testing.assert_allclose(primal,row['primal_relative_solve_residual'],atol=1e-12)
        np.testing.assert_allclose(difference,row['primal_dual_prediction_max_abs_difference'],atol=1e-10)
        report.update(primal_relative_solve_residual=primal,primal_dual_prediction_max_abs_difference=difference)
    return report

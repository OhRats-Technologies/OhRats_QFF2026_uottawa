"""Double-precision smooth kernel prediction with explicit solve certificates."""
import numpy as np
from scipy.linalg import cho_factor,cho_solve


def solve(matrix,right):
    matrix=np.asarray(matrix,dtype=np.float64);right=np.asarray(right,dtype=np.float64)
    answer=cho_solve(cho_factor(matrix,lower=True),right)
    residual=np.linalg.norm(matrix@answer-right)/max(np.linalg.norm(right),1e-15)
    return answer,float(residual)


def predict(gram,cross,y,*,ridge=1.,features=None):
    """Minimize sum squared errors + ridge * squared feature norm; no n scaling."""
    if ridge<=0:raise ValueError('Ridge must be positive')
    target=2*np.asarray(y,dtype=np.float64)-1;mean=float(target.mean());centered=target-mean
    kernel=np.asarray((gram+gram.T)/2,dtype=np.float64)
    alpha,residual=solve(kernel+ridge*np.eye(len(y)),centered)
    prediction=np.asarray(cross,dtype=np.float64)@alpha+mean
    fitted=kernel@alpha+mean
    diagnostic=dict(relative_solve_residual=residual,training_score_std=float(np.std(fitted)),
        validation_score_std=float(np.std(prediction)),validation_score_range=float(np.ptp(prediction)),
        training_intercept=mean,training_squared_error=float(np.sum((target-fitted)**2)),
        squared_feature_weight_norm=float(alpha@kernel@alpha),kernel_ridge=ridge,coefficients=alpha.tolist())
    if features is not None:
        x,v=features
        weight,primal_residual=solve(x.T@x+ridge*np.eye(x.shape[1]),x.T@centered)
        diagnostic.update(primal_coefficients=weight.tolist(),primal_relative_solve_residual=primal_residual,
            primal_dual_prediction_max_abs_difference=float(np.max(np.abs(v@weight+mean-prediction))))
    if not np.isfinite(prediction).all():raise ValueError('Nonfinite ridge predictions')
    return prediction,diagnostic


def normalized_features(train,valid):
    mean=train.mean(axis=0);train,valid=train-mean,valid-mean
    variance=float(np.mean(np.sum(train**2,axis=1)))
    if variance<=1e-12:raise ValueError('Degenerate explicit features')
    return train/np.sqrt(variance),valid/np.sqrt(variance)

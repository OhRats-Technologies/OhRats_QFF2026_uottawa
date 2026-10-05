"""Expected centered fidelity-estimation error under independent shots."""
import math
import numpy as np


def centered(gram,cross):
    mean=gram.mean(axis=0);grand=mean.mean()
    return gram-mean[None,:]-mean[:,None]+grand, cross-cross.mean(axis=1)[:,None]-mean[None,:]+grand


def error_coefficients(gram,cross):
    """Expected squared Frobenius error = coefficient / shots."""
    n=len(gram);m=len(cross)
    if n<2 or gram.shape!=(n,n) or cross.shape!=(m,n) or not m:
        raise ValueError('Requires square train and matching nonempty cross matrices')
    if not np.isfinite(gram).all() or not np.isfinite(cross).all():raise ValueError('Nonfinite fidelity')
    if not np.allclose(gram,gram.T,atol=1e-12) or not np.allclose(np.diag(gram),1,atol=1e-12):
        raise ValueError('Requires symmetric Gram with known unit diagonal')
    if min(gram.min(),cross.min()) < -1e-12 or max(gram.max(),cross.max()) > 1+1e-12:
        raise ValueError('Fidelity outside probability range')
    p=np.clip(gram,0,1);q=np.clip(cross,0,1)
    pairs=float(np.sum((p*(1-p))[np.triu_indices(n,1)]))
    train=2*((1-1/n)**2+1/n**2)*pairs
    cross_samples=(1-1/n)*float(np.sum(q*(1-q)))
    cross_training_means=m*(2-4/n)/n**2*pairs
    return dict(train=train,cross=cross_samples+cross_training_means,
                cross_sample_component=cross_samples,cross_training_mean_component=cross_training_means)


def describe(gram,cross,shots,targets):
    a,b=centered(gram,cross);coefficients=error_coefficients(gram,cross)
    variance=float(np.trace(a)/len(a));signals=dict(train=float(np.linalg.norm(a)),cross=float(np.linalg.norm(b)))
    if variance<=1e-12 or min(signals.values())<=1e-12:raise ValueError('Degenerate centered signal')
    return dict(training_centered_variance=variance,raw_mean_off_diagonal=float(gram[np.triu_indices(len(gram),1)].mean()),
        centered_signal_frobenius=signals,expected_squared_error_coefficients=coefficients,
        fixed_exact_variance_normalization=True,
        shot_conditions=[dict(shots=s,expected_relative_frobenius_error={key:math.sqrt(coefficients[key]/s)/signals[key] for key in signals},
            expected_normalized_entry_rmse=dict(train=math.sqrt(coefficients['train']/s/gram.size)/variance,
                                                cross=math.sqrt(coefficients['cross']/s/cross.size)/variance)) for s in shots],
        shots_for_relative_error=[dict(target=t,minimum_shots={key:math.ceil(coefficients[key]/(t*signals[key])**2) for key in signals}) for t in targets])

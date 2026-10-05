"""Phase-invariant local fidelity metric and its centered tangent kernel."""
import numpy as np
from wildfire_lab.encoding_screen import normalize_kernel
from wildfire_lab.shot_noise import centered


def derivative_points(anchor,step):
    anchor=np.asarray(anchor,dtype=float);delta=np.eye(len(anchor))*step
    return np.vstack([anchor,anchor+delta,anchor-delta])


def quantum_metric(states,step):
    """Real QGT from central state differences; remove the global-phase term."""
    n=(len(states)-1)//2
    if len(states)!=2*n+1 or step<=0:raise ValueError('Invalid central differences')
    np.testing.assert_allclose(np.sum(np.abs(states)**2,axis=1),1,atol=1e-10)
    derivative=(states[1:n+1]-states[n+1:])/(2*step)
    overlap=derivative.conj()@states[0]
    qgt=derivative.conj()@derivative.T-np.outer(overlap,overlap.conj())
    metric=qgt.real
    np.testing.assert_allclose(metric,metric.T,atol=1e-10)
    if np.linalg.eigvalsh(metric).min()<-1e-8:raise ValueError('Indefinite local metric')
    return metric


def tangent_kernel(train,valid,metric):
    """Angles are pi*(.5+alpha*b); center b with the training mean only."""
    mean=train.mean(axis=0);x=np.pi*(train-mean);v=np.pi*(valid-mean)
    return x@metric@x.T,v@metric@x.T


def relative_error(reference,approximation):
    norm=np.linalg.norm(reference)
    if norm<=1e-12:raise ValueError('Degenerate centered signal')
    return float(np.linalg.norm(reference-approximation)/norm)


def cosine(a,b):return float(np.sum(a*b)/(np.linalg.norm(a)*np.linalg.norm(b)))


def describe(gram,cross,train,valid,metric,scale):
    exact_train,exact_cross=centered(gram,cross)
    tangent_train,tangent_cross=tangent_kernel(train,valid,metric)
    predicted_train,predicted_cross=2*scale**2*tangent_train,2*scale**2*tangent_cross
    exact_normalized_train,exact_normalized_cross,variance=normalize_kernel(gram,cross)
    tangent_variance=float(np.trace(tangent_train)/len(train))
    if tangent_variance<=1e-12:raise ValueError('Degenerate tangent variance')
    eigen=np.linalg.eigvalsh(exact_train);positive=np.maximum(eigen,0)
    if eigen.min()<-1e-8:raise ValueError('Exact kernel has significant negative eigenvalue')
    # Tiny negative roundoff is ignored only for variance-share reporting, not repaired.
    rank=int(np.linalg.matrix_rank(metric,tol=1e-9))
    return dict(tangent_metric_rank=rank,exact_top_input_dimension_variance_fraction=float(positive[-metric.shape[0]:].sum()/positive.sum()),
        raw_centered_train_relative_error=relative_error(exact_train,predicted_train),
        raw_centered_cross_relative_error=relative_error(exact_cross,predicted_cross),
        normalized_train_shape_relative_error=relative_error(exact_normalized_train,tangent_train/tangent_variance),
        normalized_cross_shape_relative_error=relative_error(exact_normalized_cross,tangent_cross/tangent_variance),
        train_frobenius_cosine=cosine(exact_train,tangent_train),cross_frobenius_cosine=cosine(exact_cross,tangent_cross),
        exact_training_variance=variance,tangent_predicted_training_variance=2*scale**2*tangent_variance,
        training_variance_over_scale_squared=variance/scale**2,
        tangent_prediction_variance_over_scale_squared=2*tangent_variance)

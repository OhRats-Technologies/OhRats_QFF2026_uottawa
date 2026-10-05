"""Regularized Nyström coordinates with a shared train/cross feature space."""
import numpy as np


def coordinates(landmark_gram, train_cross, validation_cross, *, ridge=.001, cutoff=1e-10):
    values,vectors=np.linalg.eigh((landmark_gram+landmark_gram.T)/2)
    keep=values>cutoff
    if not keep.any():raise ValueError('No positive landmark eigenvalues')
    basis=vectors[:,keep]/np.sqrt(values[keep]+ridge)
    train,valid=train_cross@basis,validation_cross@basis
    mean=train.mean(axis=0)
    train,valid=train-mean,valid-mean
    variance=float(np.mean(np.sum(train**2,axis=1)))
    if variance<=1e-12:raise ValueError('Degenerate centered landmark features')
    return train/np.sqrt(variance),valid/np.sqrt(variance),dict(
        retained_rank=int(keep.sum()),negative_landmark_eigenvalues=int((values < -cutoff).sum()),
        min_landmark_eigenvalue=float(values.min()),centered_variance=variance,
        largest_inverse_scale=float(1/np.sqrt(values[keep].min()+ridge)))


def indices(train_rows,count,seed):
    return np.sort(np.random.default_rng(seed).permutation(train_rows)[:count])


def pair_count(train_rows,validation_rows,landmarks):
    # Known unit diagonals; landmark block symmetric and reused for those training rows.
    return landmarks*(landmarks-1)//2+(train_rows-landmarks+validation_rows)*landmarks


def assemble(landmark_gram,other_cross,validation_cross,landmark_indices,train_rows):
    rest=np.setdiff1d(np.arange(train_rows),landmark_indices)
    full=np.empty((train_rows,len(landmark_indices)))
    full[landmark_indices]=landmark_gram
    full[rest]=other_cross
    return full,validation_cross

"""Explicit known gate-algebra priors, without providing physical transition matrices."""
import torch


def gate_algebra_penalty(raw_generator):
    a=(raw_generator-raw_generator.transpose(-1,-2))/2
    eye=torch.eye(a.shape[-1],dtype=a.dtype,device=a.device)
    involution=(torch.matrix_exp(2*a[:4])-eye).square().mean()
    commute=(a[4]@a[5]-a[5]@a[4]).square().mean()
    return involution+commute

"""Independent evaluation metrics for representation collapse and distribution regularizers."""

from typing import Dict, Any
import numpy as np
import torch
from .mmd import full_mmd2, rbf_kernel_fn, energy_distance, quantum_kernel_fn


def compute_covariance(z: torch.Tensor) -> torch.Tensor:
    """Sample covariance matrix of shape (D, D)."""
    mu = z.mean(dim=0, keepdim=True)
    centered = z - mu
    n = z.shape[0]
    return (centered.T @ centered) / (n - 1)


def effective_rank(cov: torch.Tensor, eps: float = 1e-12) -> float:
    """Effective rank based on normalized singular value entropy: exp( - sum p_i ln p_i )."""
    evals = torch.linalg.eigvalsh(cov).clamp(min=eps)
    p = evals / evals.sum()
    entropy = -(p * torch.log(p)).sum().item()
    return float(np.exp(entropy))


def evaluate_embedding_quality(
    z: torch.Tensor,
    reference_gaussian: torch.Tensor = None,
    rbf_bandwidth: float = 1.0,
) -> Dict[str, float]:
    """Compute independent non-training metrics for embedding distribution z ~ (N, D)."""
    with torch.no_grad():
        z_f64 = z.to(torch.float64)
        cov = compute_covariance(z_f64)
        evals = torch.linalg.eigvalsh(cov)
        evals_np = evals.cpu().numpy()

        lambda_min = float(evals_np[0])
        lambda_max = float(evals_np[-1])
        cond_num = float(lambda_max / max(lambda_min, 1e-12))
        eff_rank = effective_rank(cov)
        mean_std = float(z_f64.std(dim=0).mean().item())
        mean_norm = float(z_f64.mean(dim=0).norm().item())
        cov_error = float((cov - torch.eye(z.shape[-1], dtype=torch.float64, device=z.device)).norm().item())

        metrics = {
            "effective_rank": eff_rank,
            "min_eigenvalue": lambda_min,
            "max_eigenvalue": lambda_max,
            "condition_number": cond_num,
            "mean_feature_std": mean_std,
            "mean_norm": mean_norm,
            "covariance_frobenius_error": cov_error,
        }

        if reference_gaussian is None:
            reference_gaussian = torch.randn_like(z_f64)
        else:
            reference_gaussian = reference_gaussian.to(torch.float64)

        # Held-out classical RBF-MMD
        rbf_fn = rbf_kernel_fn(bandwidth=rbf_bandwidth)
        metrics["held_out_rbf_mmd2"] = float(full_mmd2(rbf_fn, z_f64, reference_gaussian).item())

        # Multivariate Energy Distance
        metrics["energy_distance"] = float(energy_distance(z_f64, reference_gaussian).item())

        # Held-out Quantum MMD
        q_fn = quantum_kernel_fn(scale=1.0)
        eval_size = min(z_f64.shape[0], 64)
        metrics["held_out_q_mmd2"] = float(
            full_mmd2(q_fn, z_f64[:eval_size], reference_gaussian[:eval_size]).item()
        )

        return metrics

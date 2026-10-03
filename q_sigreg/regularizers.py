"""Regularizers for LeJEPA embedding space distribution matching."""

import torch
import torch.nn as nn
from typing import Dict, Any, Optional

from .mmd import linear_mmd2_from_kernel, quantum_kernel_fn, rbf_kernel_fn, moment_penalty

# Slicing univariate test from vendored lejepa
from lejepa.lejepa.multivariate.slicing import SlicingUnivariateTest
from lejepa.lejepa.univariate.epps_pulley import EppsPulley


class StandardSIGReg(nn.Module):
    """Canonical SIGReg from Balestriero & LeCun (2025)."""
    def __init__(self, num_slices: int = 128, knots: int = 17):
        super().__init__()
        self.test = SlicingUnivariateTest(
            univariate_test=EppsPulley(n_points=knots),
            num_slices=num_slices,
            reduction="mean",
            sampler="gaussian",
        )

    def forward(self, z: torch.Tensor, g: Optional[torch.Tensor] = None) -> torch.Tensor:
        # SIGReg takes (*, N, D)
        return self.test(z)


class CovariancePenalty(nn.Module):
    """Covariance and mean anchor regularizer."""
    def __init__(self, lambda_m: float = 1.0):
        super().__init__()
        self.lambda_m = lambda_m

    def forward(self, z: torch.Tensor, g: Optional[torch.Tensor] = None) -> torch.Tensor:
        return self.lambda_m * moment_penalty(z)


class RBFMMDRegularizer(nn.Module):
    """Classical RBF-MMD with moment penalty anchor."""
    def __init__(self, bandwidth: float = 1.0, lambda_rbf: float = 1.0, lambda_m: float = 1.0):
        super().__init__()
        self.bandwidth = bandwidth
        self.lambda_rbf = lambda_rbf
        self.lambda_m = lambda_m
        self.kernel_fn = rbf_kernel_fn(bandwidth=bandwidth)

    def forward(self, z: torch.Tensor, g: Optional[torch.Tensor] = None) -> torch.Tensor:
        if g is None:
            g = torch.randn_like(z)
        loss_mmd = linear_mmd2_from_kernel(self.kernel_fn, z, g)
        if self.lambda_m > 0:
            loss_mom = moment_penalty(z)
            return self.lambda_rbf * loss_mmd + self.lambda_m * loss_mom
        return self.lambda_rbf * loss_mmd


class QuantumMMDRegularizer(nn.Module):
    """Quantum-kernel MMD regularizer (Q-SIGReg), with or without moment anchoring."""
    def __init__(
        self,
        scale: float = 1.0,
        lambda_q: float = 1.0,
        lambda_m: float = 1.0,
        counter: Optional[Dict[str, int]] = None,
    ):
        super().__init__()
        self.scale = scale
        self.lambda_q = lambda_q
        self.lambda_m = lambda_m
        self.counter = counter if counter is not None else {"kernel_evals": 0}
        self.kernel_fn = quantum_kernel_fn(scale=scale, counter=self.counter)

    def forward(self, z: torch.Tensor, g: Optional[torch.Tensor] = None) -> torch.Tensor:
        if g is None:
            g = torch.randn_like(z)
        loss_q = linear_mmd2_from_kernel(self.kernel_fn, z, g)
        if self.lambda_m > 0:
            loss_m = moment_penalty(z)
            return self.lambda_q * loss_q + self.lambda_m * loss_m
        return self.lambda_q * loss_q


class NoRegularizer(nn.Module):
    """Null regularizer for collapse baseline."""
    def forward(self, z: torch.Tensor, g: Optional[torch.Tensor] = None) -> torch.Tensor:
        return torch.tensor(0.0, device=z.device, dtype=z.dtype, requires_grad=True)


def build_regularizer(
    name: str,
    lambda_q: float = 1.0,
    lambda_m: float = 1.0,
    counter: Optional[Dict[str, int]] = None,
) -> nn.Module:
    name_lower = name.lower().replace("-", "_").replace(" ", "_")
    if "q_sigreg" in name_lower or "qsigreg" in name_lower or ("quantum" in name_lower and "moments" in name_lower):
        return QuantumMMDRegularizer(scale=1.0, lambda_q=lambda_q, lambda_m=lambda_m, counter=counter)
    elif "only" in name_lower or "q_mmd_only" in name_lower or ("quantum" in name_lower and "only" in name_lower):
        return QuantumMMDRegularizer(scale=1.0, lambda_q=lambda_q, lambda_m=0.0, counter=counter)
    elif "quantum" in name_lower:
        return QuantumMMDRegularizer(scale=1.0, lambda_q=lambda_q, lambda_m=lambda_m, counter=counter)
    elif "rbf" in name_lower:
        return RBFMMDRegularizer(bandwidth=1.0, lambda_rbf=lambda_q, lambda_m=lambda_m)
    elif "sigreg" in name_lower and "q" not in name_lower:
        return StandardSIGReg(num_slices=128)
    elif "cov" in name_lower or "moment" in name_lower:
        return CovariancePenalty(lambda_m=lambda_m)
    elif "none" in name_lower or "no_reg" in name_lower or "no_regularizer" in name_lower or "collapse" in name_lower:
        return NoRegularizer()
    else:
        raise ValueError(f"Unknown regularizer: {name}")

"""Distribution discrepancies and anchors for Q-SIGReg and its controls."""

import torch

from .kernel import bounded_angles, exact_states, pair_kernel


def linear_mmd2_from_kernel(kernel_fn, z: torch.Tensor, g: torch.Tensor) -> torch.Tensor:
    """Linear-time paired MMD^2.

    ``kernel_fn(a, b)`` returns aligned-pair kernel values. With m = B/2 pairs:
    mean[ k(z_2i, z_2i+1) + k(g_2i, g_2i+1) - k(z_2i, g_2i+1) - k(z_2i+1, g_2i) ].
    """
    if z.shape != g.shape or z.shape[0] % 2:
        raise ValueError("z and g must have equal shape with an even batch size")
    z0, z1, g0, g1 = z[0::2], z[1::2], g[0::2], g[1::2]
    return (kernel_fn(z0, z1) + kernel_fn(g0, g1) - kernel_fn(z0, g1) - kernel_fn(z1, g0)).mean()


def quantum_kernel_fn(scale: float = 1.0, counter=None):
    """Aligned-pair quantum kernel on raw embeddings (angles are bounded inside)."""

    def fn(a, b):
        if counter is not None:
            counter["kernel_evals"] += a.shape[0]
        return pair_kernel(exact_states(bounded_angles(a, scale)), exact_states(bounded_angles(b, scale)))

    return fn


def rbf_kernel_fn(bandwidth: float):
    def fn(a, b):
        return torch.exp(-(a - b).square().sum(-1) / (2 * bandwidth**2))

    return fn


def full_mmd2(kernel_fn, z: torch.Tensor, g: torch.Tensor) -> torch.Tensor:
    """Unbiased full-matrix MMD^2 (testing and held-out evaluation only)."""

    def gram(a, b):
        n, m = a.shape[0], b.shape[0]
        return kernel_fn(a.repeat_interleave(m, 0), b.repeat(n, 1)).reshape(n, m)

    kzz, kgg, kzg = gram(z, z), gram(g, g), gram(z, g)
    n, m = z.shape[0], g.shape[0]
    return (
        (kzz.sum() - kzz.diag().sum()) / (n * (n - 1))
        + (kgg.sum() - kgg.diag().sum()) / (m * (m - 1))
        - 2 * kzg.mean()
    )


def moment_penalty(z: torch.Tensor) -> torch.Tensor:
    """||mean||^2 + ||Cov - I||_F^2 with the unbiased covariance."""
    mu = z.mean(0)
    centered = z - mu
    cov = centered.T @ centered / (z.shape[0] - 1)
    eye = torch.eye(z.shape[1], dtype=z.dtype, device=z.device)
    return mu.square().sum() + (cov - eye).square().sum()


def covariance_penalty(z: torch.Tensor) -> torch.Tensor:
    return moment_penalty(z)


def energy_distance(z: torch.Tensor, g: torch.Tensor) -> torch.Tensor:
    """Multivariate energy distance 2E|Z-G| - E|Z-Z'| - E|G-G'| (V-statistic)."""
    return 2 * torch.cdist(z, g).mean() - torch.cdist(z, z).mean() - torch.cdist(g, g).mean()

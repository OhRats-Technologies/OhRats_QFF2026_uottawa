"""Phase 1: Standalone latent-distribution optimization and recovery tests."""

import json
import time
from pathlib import Path
from typing import Dict, List, Any
import numpy as np
import torch
import torch.optim as optim

from .metrics import evaluate_embedding_quality
from .regularizers import build_regularizer


REGULARIZERS = [
    "No Regularizer",
    "Covariance Penalty",
    "Standard SIGReg",
    "Classical RBF-MMD",
    "Quantum MMD Only",
    "Q-SIGReg (Q-MMD + Moments)",
]

CORRUPTIONS = [
    "Complete Collapse",
    "Low-Rank (1D Subspace)",
    "Anisotropic Covariance",
    "Shifted Mean (mu=[2,2,2,2])",
    "Heavy-Tailed (Student-t)",
]


def generate_corrupted_latents(corruption: str, n_samples: int = 256, dim: int = 4, seed: int = 2026) -> torch.Tensor:
    rng = torch.Generator().manual_seed(seed)
    if corruption == "Complete Collapse":
        return 0.01 * torch.randn(n_samples, dim, generator=rng, dtype=torch.float32)
    elif corruption == "Low-Rank (1D Subspace)":
        u = torch.randn(n_samples, 1, generator=rng, dtype=torch.float32)
        v = torch.tensor([[1.0, 0.5, -0.5, 0.2]], dtype=torch.float32)
        v = v / v.norm()
        noise = 0.01 * torch.randn(n_samples, dim, generator=rng, dtype=torch.float32)
        return u @ v + noise
    elif corruption == "Anisotropic Covariance":
        scales = torch.tensor([np.sqrt(10.0), 1.0, np.sqrt(0.1), np.sqrt(0.01)], dtype=torch.float32)
        return torch.randn(n_samples, dim, generator=rng, dtype=torch.float32) * scales
    elif corruption == "Shifted Mean (mu=[2,2,2,2])":
        return torch.randn(n_samples, dim, generator=rng, dtype=torch.float32) + 2.0
    elif corruption == "Heavy-Tailed (Student-t)":
        # Student-t with df=3
        g = torch.randn(n_samples, dim, generator=rng, dtype=torch.float32)
        chi2 = torch.sum(torch.randn(n_samples, 3, generator=rng, dtype=torch.float32)**2, dim=1, keepdim=True)
        return g / torch.sqrt(chi2 / 3.0)
    else:
        raise ValueError(f"Unknown corruption: {corruption}")


def run_standalone_optimization(
    corruption: str,
    reg_name: str,
    n_samples: int = 128,
    steps: int = 150,
    lr: float = 0.05,
    seed: int = 2026,
    subsample_b_q: int = 8,
) -> Dict[str, Any]:
    torch.manual_seed(seed)
    counter = {"kernel_evals": 0}
    reg = build_regularizer(reg_name, lambda_q=1.0, lambda_m=1.0, counter=counter)

    z_init = generate_corrupted_latents(corruption, n_samples=n_samples, dim=4, seed=seed)
    z = z_init.clone().detach().requires_grad_(True)
    optimizer = optim.Adam([z], lr=lr)

    initial_metrics = evaluate_embedding_quality(z_init)

    start_time = time.perf_counter()
    loss_history = []

    for step in range(steps):
        optimizer.zero_grad()
        # Linear estimator on mini-batches of size subsample_b_q
        if "Quantum" in reg_name or "Q-SIGReg" in reg_name:
            perm = torch.randperm(z.shape[0])[:subsample_b_q]
            z_sub = z[perm]
            g_sub = torch.randn(subsample_b_q, 4, dtype=z.dtype, device=z.device)
            loss = reg(z_sub, g_sub)
        elif "RBF" in reg_name:
            perm = torch.randperm(z.shape[0])[:subsample_b_q]
            z_sub = z[perm]
            g_sub = torch.randn(subsample_b_q, 4, dtype=z.dtype, device=z.device)
            loss = reg(z_sub, g_sub)
        elif "Covariance" in reg_name:
            loss = reg(z)
        elif "SIGReg" in reg_name:
            loss = reg(z.unsqueeze(0)).squeeze()
        else:
            loss = reg(z)

        if loss.requires_grad:
            loss.backward()
            optimizer.step()
        loss_history.append(float(loss.item()))

    elapsed = time.perf_counter() - start_time
    final_metrics = evaluate_embedding_quality(z.detach())

    return {
        "corruption": corruption,
        "regularizer": reg_name,
        "initial_metrics": initial_metrics,
        "final_metrics": final_metrics,
        "elapsed_seconds": elapsed,
        "kernel_evals": counter["kernel_evals"],
        "final_loss": loss_history[-1] if loss_history else 0.0,
    }


def run_all_standalone_ablations(output_dir: Path = None, n_samples: int = 128, steps: int = 150) -> List[Dict[str, Any]]:
    results = []
    print(f"Starting standalone latent optimization sweep across {len(CORRUPTIONS)} corruptions x {len(REGULARIZERS)} regularizers...")
    for c_idx, corruption in enumerate(CORRUPTIONS):
        for r_idx, reg_name in enumerate(REGULARIZERS):
            res = run_standalone_optimization(
                corruption=corruption,
                reg_name=reg_name,
                n_samples=n_samples,
                steps=steps,
                seed=2026 + c_idx * 10 + r_idx,
            )
            results.append(res)
            im = res["initial_metrics"]
            fm = res["final_metrics"]
            print(f"[{corruption[:12]:12s} | {reg_name[:18]:18s}] EffRank: {im['effective_rank']:.2f}->{fm['effective_rank']:.2f} | RBF-MMD2: {im['held_out_rbf_mmd2']:.4f}->{fm['held_out_rbf_mmd2']:.4f} | Energy: {im['energy_distance']:.4f}->{fm['energy_distance']:.4f} | ({res['elapsed_seconds']:.2f}s, {res['kernel_evals']} evals)")

    if output_dir:
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        (output_dir / "standalone_results.json").write_text(json.dumps(results, indent=2))
        print(f"Saved standalone results to {output_dir / 'standalone_results.json'}")

    return results


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=str, default="results/q_sigreg")
    parser.add_argument("--steps", type=int, default=150)
    parser.add_argument("--samples", type=int, default=128)
    args = parser.parse_args()
    run_all_standalone_ablations(output_dir=Path(args.output), n_samples=args.samples, steps=args.steps)

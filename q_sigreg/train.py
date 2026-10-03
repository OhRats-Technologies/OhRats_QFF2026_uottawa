"""Phase 2: LeJEPA 6-way ablation experiment with representation collapse metrics and linear probing."""

import json
import time
from pathlib import Path
from typing import Dict, List, Any, Tuple
import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F
import torch.optim as optim
from torch.utils.data import TensorDataset, DataLoader

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


class SyntheticMultiViewDataset:
    """Multi-view representation manifold with 10 classes and positive augmented views."""
    def __init__(self, n_samples: int = 1024, in_dim: int = 16, n_classes: int = 10, noise: float = 0.15, seed: int = 2026):
        rng = torch.Generator().manual_seed(seed)
        self.centers = torch.randn(n_classes, in_dim, generator=rng)
        self.labels = torch.randint(0, n_classes, (n_samples,), generator=rng)
        
        # Base samples around class centroids
        base = self.centers[self.labels] + 0.3 * torch.randn(n_samples, in_dim, generator=rng)
        # Two positive views with non-linear distortion and noise
        v1 = base + noise * torch.randn(n_samples, in_dim, generator=rng)
        v2 = base + noise * torch.randn(n_samples, in_dim, generator=rng)
        
        self.v1 = v1
        self.v2 = v2
        self.targets = self.labels

    def get_loaders(self, batch_size: int = 64) -> Tuple[DataLoader, DataLoader]:
        dataset = TensorDataset(self.v1, self.v2, self.targets)
        train_size = int(0.8 * len(dataset))
        test_size = len(dataset) - train_size
        train_ds, test_ds = torch.utils.data.random_split(dataset, [train_size, test_size])
        train_loader = DataLoader(train_ds, batch_size=batch_size, shuffle=True)
        test_loader = DataLoader(test_ds, batch_size=batch_size, shuffle=False)
        return train_loader, test_loader


class LeJEPAEncoder(nn.Module):
    """Classical encoder backbone with dedicated 4-dimensional projection head."""
    def __init__(self, in_dim: int = 16, rep_dim: int = 32, proj_dim: int = 4):
        super().__init__()
        self.backbone = nn.Sequential(
            nn.Linear(in_dim, 64),
            nn.BatchNorm1d(64),
            nn.ReLU(),
            nn.Linear(64, rep_dim),
            nn.BatchNorm1d(rep_dim),
        )
        self.projector = nn.Sequential(
            nn.Linear(rep_dim, 32),
            nn.ReLU(),
            nn.Linear(32, proj_dim),
        )

    def forward(self, x: torch.Tensor) -> Tuple[torch.Tensor, torch.Tensor]:
        h = self.backbone(x)
        z = self.projector(h)
        return h, z


def train_linear_probe(
    encoder: nn.Module,
    train_loader: DataLoader,
    test_loader: DataLoader,
    n_classes: int = 10,
    rep_dim: int = 32,
    epochs: int = 40,
    lr: float = 0.01,
) -> float:
    """Train a linear classifier on frozen representations h to evaluate downstream utility."""
    encoder.eval()
    probe = nn.Linear(rep_dim, n_classes)
    opt = optim.Adam(probe.parameters(), lr=lr)
    
    # Collect frozen representations
    with torch.no_grad():
        x_tr, y_tr = [], []
        for v1, _, y in train_loader:
            h, _ = encoder(v1)
            x_tr.append(h)
            y_tr.append(y)
        x_tr = torch.cat(x_tr, dim=0)
        y_tr = torch.cat(y_tr, dim=0)

        x_te, y_te = [], []
        for v1, _, y in test_loader:
            h, _ = encoder(v1)
            x_te.append(h)
            y_te.append(y)
        x_te = torch.cat(x_te, dim=0)
        y_te = torch.cat(y_te, dim=0)

    # Train probe
    for _ in range(epochs):
        opt.zero_grad()
        logits = probe(x_tr)
        loss = F.cross_entropy(logits, y_tr)
        loss.backward()
        opt.step()

    # Test accuracy
    with torch.no_grad():
        preds = probe(x_te).argmax(dim=-1)
        acc = (preds == y_te).float().mean().item() * 100.0

    return float(acc)


def train_lejepa_variant(
    reg_name: str,
    seed: int = 2026,
    epochs: int = 25,
    b_q: int = 8,
    q_freq: int = 4,
    lambda_reg: float = 2.0,
    lambda_m: float = 1.0,
) -> Dict[str, Any]:
    torch.manual_seed(seed)
    data = SyntheticMultiViewDataset(n_samples=1024, in_dim=16, n_classes=10, seed=seed)
    train_loader, test_loader = data.get_loaders(batch_size=64)

    encoder = LeJEPAEncoder(in_dim=16, rep_dim=32, proj_dim=4)
    optimizer = optim.Adam(encoder.parameters(), lr=0.003, weight_decay=1e-4)

    counter = {"kernel_evals": 0}
    regularizer = build_regularizer(reg_name, lambda_q=lambda_reg, lambda_m=lambda_m, counter=counter)

    start_time = time.perf_counter()
    step_count = 0
    jepa_losses = []
    reg_losses = []

    for epoch in range(epochs):
        encoder.train()
        for v1, v2, _ in train_loader:
            step_count += 1
            optimizer.zero_grad()

            h1, z1 = encoder(v1)
            h2, z2 = encoder(v2)

            # Invariance / alignment loss between positive views
            l_jepa = F.mse_loss(z1, z2)

            # Apply regularizer
            if "Quantum" in reg_name or "Q-SIGReg" in reg_name:
                if step_count % q_freq == 0:
                    perm = torch.randperm(z1.shape[0])[:b_q]
                    z_sub = z1[perm]
                    g_sub = torch.randn(b_q, 4, dtype=z1.dtype, device=z1.device)
                    l_reg = regularizer(z_sub, g_sub)
                else:
                    l_reg = torch.tensor(0.0, device=z1.device)
            elif "RBF" in reg_name:
                if step_count % q_freq == 0:
                    perm = torch.randperm(z1.shape[0])[:b_q]
                    z_sub = z1[perm]
                    g_sub = torch.randn(b_q, 4, dtype=z1.dtype, device=z1.device)
                    l_reg = regularizer(z_sub, g_sub)
                else:
                    l_reg = torch.tensor(0.0, device=z1.device)
            elif "SIGReg" in reg_name:
                l_reg = lambda_reg * regularizer(z1.unsqueeze(0)).squeeze()
            elif "Covariance" in reg_name:
                l_reg = regularizer(z1)
            else:
                l_reg = regularizer(z1)

            total_loss = l_jepa + l_reg
            total_loss.backward()
            optimizer.step()

            jepa_losses.append(float(l_jepa.item()))
            reg_losses.append(float(l_reg.item()))

    elapsed = time.perf_counter() - start_time

    # Evaluate representation quality on full test set
    encoder.eval()
    with torch.no_grad():
        all_z = []
        for v1, _, _ in test_loader:
            _, z = encoder(v1)
            all_z.append(z)
        all_z = torch.cat(all_z, dim=0)

    quality_metrics = evaluate_embedding_quality(all_z)
    probe_acc = train_linear_probe(encoder, train_loader, test_loader)

    return {
        "regularizer": reg_name,
        "seed": seed,
        "probe_accuracy": probe_acc,
        "final_jepa_loss": float(np.mean(jepa_losses[-20:])),
        "quality_metrics": quality_metrics,
        "elapsed_seconds": elapsed,
        "circuit_evals": counter["kernel_evals"],
    }


def run_full_lejepa_study(output_dir: Path = None, seeds: List[int] = [2026, 2027, 2028]) -> Dict[str, Any]:
    all_runs = []
    summary_by_reg = {}

    print(f"Starting LeJEPA 6-way ablation study across {len(REGULARIZERS)} variants x {len(seeds)} seeds ({len(REGULARIZERS)*len(seeds)} runs total)...")

    for reg_name in REGULARIZERS:
        runs_for_reg = []
        for seed in seeds:
            res = train_lejepa_variant(reg_name=reg_name, seed=seed)
            runs_for_reg.append(res)
            all_runs.append(res)
            qm = res["quality_metrics"]
            print(f"[{reg_name[:20]:20s} | Seed {seed}] ProbeAcc: {res['probe_accuracy']:.1f}% | EffRank: {qm['effective_rank']:.2f} | RBF-MMD: {qm['held_out_rbf_mmd2']:.4f} | Energy: {qm['energy_distance']:.4f} | ({res['elapsed_seconds']:.2f}s, {res['circuit_evals']} evals)")

        # Aggregate across seeds
        accs = [r["probe_accuracy"] for r in runs_for_reg]
        ranks = [r["quality_metrics"]["effective_rank"] for r in runs_for_reg]
        rbfs = [r["quality_metrics"]["held_out_rbf_mmd2"] for r in runs_for_reg]
        energies = [r["quality_metrics"]["energy_distance"] for r in runs_for_reg]
        times = [r["elapsed_seconds"] for r in runs_for_reg]
        evals = [r["circuit_evals"] for r in runs_for_reg]

        summary_by_reg[reg_name] = {
            "probe_accuracy_mean": float(np.mean(accs)),
            "probe_accuracy_std": float(np.std(accs)),
            "effective_rank_mean": float(np.mean(ranks)),
            "effective_rank_std": float(np.std(ranks)),
            "held_out_rbf_mmd2_mean": float(np.mean(rbfs)),
            "held_out_rbf_mmd2_std": float(np.std(rbfs)),
            "energy_distance_mean": float(np.mean(energies)),
            "energy_distance_std": float(np.std(energies)),
            "elapsed_seconds_mean": float(np.mean(times)),
            "total_circuit_evals": int(np.sum(evals)),
        }

    results_payload = {
        "summary": summary_by_reg,
        "runs": all_runs,
    }

    if output_dir:
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        (output_dir / "lejepa_ablation_results.json").write_text(json.dumps(results_payload, indent=2))
        print(f"Saved full LeJEPA ablation results to {output_dir / 'lejepa_ablation_results.json'}")

    return results_payload


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=str, default="results/q_sigreg")
    args = parser.parse_args()
    run_full_lejepa_study(output_dir=Path(args.output))

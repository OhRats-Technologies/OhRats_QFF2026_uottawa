import json
import time
import argparse
import numpy as np
from pathlib import Path
from typing import Dict, Any, List, Tuple
from collections import defaultdict
import scipy.stats

import torch
import torch.nn as nn
import torch.nn.functional as F
import torch.optim as optim
from torch.utils.data import TensorDataset, DataLoader

# Import building blocks from q_sigreg
from q_sigreg.train import SyntheticMultiViewDataset, LeJEPAEncoder
from q_sigreg.regularizers import StandardSIGReg, CovariancePenalty, RBFMMDRegularizer, QuantumMMDRegularizer
from q_sigreg.mmd import full_mmd2, rbf_kernel_fn, energy_distance, quantum_kernel_fn, moment_penalty, linear_mmd2_from_kernel

def train_probe_fraction(
    encoder: nn.Module,
    train_loader: DataLoader,
    test_loader: DataLoader,
    fraction: float,
    seed: int,
    n_classes: int = 10,
    rep_dim: int = 32,
    epochs: int = 40,
    lr: float = 0.01,
) -> float:
    encoder.eval()
    probe = nn.Linear(rep_dim, n_classes)
    opt = optim.Adam(probe.parameters(), lr=lr)
    
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

    # Subsample training data
    n_total = x_tr.shape[0]
    n_sub = max(int(n_total * fraction), 1)
    rng = torch.Generator().manual_seed(seed + 999) # different seed for shuffling
    perm = torch.randperm(n_total, generator=rng)[:n_sub]
    x_tr_sub = x_tr[perm]
    y_tr_sub = y_tr[perm]

    # Train probe
    for _ in range(epochs):
        opt.zero_grad()
        logits = probe(x_tr_sub)
        loss = F.cross_entropy(logits, y_tr_sub)
        loss.backward()
        opt.step()

    with torch.no_grad():
        preds = probe(x_te).argmax(dim=-1)
        acc = (preds == y_te).float().mean().item() * 100.0

    return acc

def eval_5nn(
    encoder: nn.Module,
    train_loader: DataLoader,
    test_loader: DataLoader,
    k: int = 5
) -> float:
    encoder.eval()
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
        
        # Exact KNN
        dist = torch.cdist(x_te, x_tr) # (N_te, N_tr)
        topk = dist.topk(k, dim=1, largest=False).indices # (N_te, k)
        topk_y = y_tr[topk] # (N_te, k)
        
        preds = []
        for row in topk_y:
            val, counts = torch.unique(row, return_counts=True)
            preds.append(val[counts.argmax()].item())
        preds = torch.tensor(preds, device=y_te.device)
        acc = (preds == y_te).float().mean().item() * 100.0
    return acc

def full_mmd2_biased_unbiased(kernel_fn, z: torch.Tensor, g: torch.Tensor) -> Tuple[float, float]:
    def gram(a, b):
        n, m = a.shape[0], b.shape[0]
        return kernel_fn(a.repeat_interleave(m, 0), b.repeat(n, 1)).reshape(n, m)

    kzz, kgg, kzg = gram(z, z), gram(g, g), gram(z, g)
    n, m = z.shape[0], g.shape[0]
    
    biased = kzz.mean() + kgg.mean() - 2 * kzg.mean()
    unbiased = ((kzz.sum() - kzz.diag().sum()) / (n * (n - 1))
                + (kgg.sum() - kgg.diag().sum()) / (m * (m - 1))
                - 2 * kzg.mean())
    return float(biased.item()), float(unbiased.item())


def matched_eval_metrics(z: torch.Tensor, z_train: torch.Tensor = None) -> Dict[str, Any]:
    with torch.no_grad():
        z_f64 = z.to(torch.float64)
        
        # Effective rank without artificial flooring
        mu = z_f64.mean(dim=0, keepdim=True)
        centered = z_f64 - mu
        cov = (centered.T @ centered) / (z_f64.shape[0] - 1)
        evals = torch.linalg.eigvalsh(cov) # EXACT, NO CLAMPING
        lambda_min = float(evals[0].item())
        lambda_max = float(evals[-1].item())
        cond_num = float(lambda_max / max(lambda_min, 1e-12))
        
        # eff rank
        # avoid log(0) for entropy but do not floor evals directly
        p = evals / evals.sum()
        p_safe = p[p > 0]
        entropy = -(p_safe * torch.log(p_safe)).sum().item()
        eff_rank = float(np.exp(entropy))
        
        mean_std = float(z_f64.std(dim=0).mean().item())
        cov_error = float((cov - torch.eye(z_f64.shape[-1], dtype=torch.float64, device=z.device)).norm().item())
        
        metrics = {
            "effective_rank_exact": eff_rank,
            "min_eigenvalue": lambda_min,
            "max_eigenvalue": lambda_max,
            "condition_number": cond_num,
            "mean_feature_std": mean_std,
            "covariance_frobenius_error": cov_error,
        }
        
        # Fixed reference Gaussian
        rng_ref = torch.Generator().manual_seed(4242)
        ref_g = torch.randn(500, z.shape[1], dtype=torch.float64, generator=rng_ref, device=z.device)
        
        metrics["energy_distance"] = float(energy_distance(z_f64, ref_g).item())
        
        # Multi-scale RBF-MMD2
        dist_g = torch.cdist(ref_g, ref_g)
        # Median distance of strictly upper triangle
        triu_idx = torch.triu_indices(500, 500, offset=1)
        sigma = float(torch.median(dist_g[triu_idx[0], triu_idx[1]]).item())
        
        for scale_factor, name in [(0.25, "sigma_0.25"), (0.5, "sigma_0.5"), (1.0, "sigma_1.0"), (2.0, "sigma_2.0"), (4.0, "sigma_4.0")]:
            bandwidth = sigma * scale_factor
            fn = rbf_kernel_fn(bandwidth=bandwidth)
            biased, unbiased = full_mmd2_biased_unbiased(fn, z_f64, ref_g)
            metrics[f"held_out_rbf_mmd2_{name}_biased"] = biased
            metrics[f"held_out_rbf_mmd2_{name}_unbiased"] = unbiased
            
            # also save default
            if scale_factor == 1.0:
                metrics["held_out_rbf_mmd2"] = unbiased

        # Held-out Q-MMD2
        q_fn = quantum_kernel_fn(scale=1.0)
        eval_size = min(z_f64.shape[0], 64)
        metrics["held_out_q_mmd2"] = float(full_mmd2(q_fn, z_f64[:eval_size], ref_g[:eval_size]).item())
        
        # Gram matrix diagnostics
        z100 = z_f64[:100]
        def gram(a):
            n = a.shape[0]
            return q_fn(a.repeat_interleave(n, 0), a.repeat(n, 1)).reshape(n, n)
        
        G_z = gram(z100)
        evals_G = torch.linalg.eigvalsh(G_z)
        p_G = evals_G / evals_G.sum()
        p_G_safe = p_G[p_G > 0]
        eff_rank_G = float(np.exp(-(p_G_safe * torch.log(p_G_safe)).sum().item()))
        
        metrics["q_gram_min_eig"] = float(evals_G[0].item())
        metrics["q_gram_max_eig"] = float(evals_G[-1].item())
        metrics["q_gram_cond_num"] = metrics["q_gram_max_eig"] / max(metrics["q_gram_min_eig"], 1e-12)
        metrics["q_gram_eff_rank"] = eff_rank_G
        metrics["q_gram_mean_off_diag"] = float((G_z.sum() - G_z.diag().sum()) / (100 * 99))

        return metrics

def train_matched_variant(variant_name: str, seed: int, b_q=8, q_freq=4, epochs=25):
    torch.manual_seed(seed)
    data = SyntheticMultiViewDataset(n_samples=1024, in_dim=16, n_classes=10, seed=seed)
    train_loader, test_loader = data.get_loaders(batch_size=64)

    encoder = LeJEPAEncoder(in_dim=16, rep_dim=32, proj_dim=4)
    if variant_name == "Untrained":
        encoder.eval()
        with torch.no_grad():
            all_z = []
            for v1, _, _ in test_loader:
                _, z = encoder(v1)
                all_z.append(z)
            all_z = torch.cat(all_z, dim=0)
        
        metrics = matched_eval_metrics(all_z)
        probes = {
            "probe_1pct": train_probe_fraction(encoder, train_loader, test_loader, 0.01, seed, epochs=0),
            "probe_5pct": train_probe_fraction(encoder, train_loader, test_loader, 0.05, seed, epochs=0),
            "probe_10pct": train_probe_fraction(encoder, train_loader, test_loader, 0.10, seed, epochs=0),
            "probe_100pct": train_probe_fraction(encoder, train_loader, test_loader, 1.0, seed, epochs=0),
            "knn_5": eval_5nn(encoder, train_loader, test_loader, 5)
        }
        return {"metrics": metrics, "probes": probes, "grad_cos_sim": 0.0}

    optimizer = optim.Adam(encoder.parameters(), lr=0.003, weight_decay=1e-4)

    # Set up regularizers components manually to track gradients explicitly if needed
    sigreg = StandardSIGReg(num_slices=128)
    q_kernel = quantum_kernel_fn(scale=1.0)
    rbf_kernel = rbf_kernel_fn(bandwidth=1.0)

    grad_cos_sims = []

    encoder.train()
    step_count = 0
    for epoch in range(epochs):
        for v1, v2, _ in train_loader:
            step_count += 1
            optimizer.zero_grad()

            h1, z1 = encoder(v1)
            h2, z2 = encoder(v2)
            l_jepa = F.mse_loss(z1, z2)

            l_reg = torch.tensor(0.0, device=z1.device)
            l_mmd = torch.tensor(0.0, device=z1.device)
            l_mom = torch.tensor(0.0, device=z1.device)

            if variant_name == "SIGReg":
                l_reg = sigreg(z1.unsqueeze(0)).squeeze()
            else:
                if step_count % q_freq == 0:
                    perm = torch.randperm(z1.shape[0])[:b_q]
                    z_sub = z1[perm]
                    g_sub = torch.randn(b_q, 4, dtype=z1.dtype, device=z1.device)
                    
                    if variant_name == "Moments Only":
                        l_reg = moment_penalty(z_sub)
                    elif variant_name == "RBF Pure":
                        l_reg = linear_mmd2_from_kernel(rbf_kernel, z_sub, g_sub)
                    elif variant_name == "RBF+Moments":
                        l_mmd = linear_mmd2_from_kernel(rbf_kernel, z_sub, g_sub)
                        l_mom = moment_penalty(z_sub)
                        l_reg = l_mmd + l_mom
                    elif variant_name == "Q Pure":
                        l_reg = linear_mmd2_from_kernel(q_kernel, z_sub, g_sub)
                    elif variant_name == "Q+Moments":
                        l_mmd = linear_mmd2_from_kernel(q_kernel, z_sub, g_sub)
                        l_mom = moment_penalty(z_sub)
                        l_reg = l_mmd + l_mom
            
            total_loss = l_jepa + l_reg
            
            # Gradient cosine similarity tracking
            if l_mmd.item() > 0 and l_mom.item() > 0:
                optimizer.zero_grad()
                l_mmd.backward(retain_graph=True)
                g_mmd = []
                for p in encoder.parameters():
                    if p.grad is not None:
                        g_mmd.append(p.grad.view(-1).clone())
                g_mmd = torch.cat(g_mmd)
                
                optimizer.zero_grad()
                l_mom.backward(retain_graph=True)
                g_mom = []
                for p in encoder.parameters():
                    if p.grad is not None:
                        g_mom.append(p.grad.view(-1).clone())
                g_mom = torch.cat(g_mom)
                
                cos_sim = F.cosine_similarity(g_mmd.unsqueeze(0), g_mom.unsqueeze(0)).item()
                grad_cos_sims.append(cos_sim)
                
                optimizer.zero_grad()
                total_loss = l_jepa + l_mmd + l_mom
            
            total_loss.backward()
            optimizer.step()

    mean_grad_cos = np.mean(grad_cos_sims) if grad_cos_sims else 0.0

    encoder.eval()
    with torch.no_grad():
        all_z = []
        for v1, _, _ in test_loader:
            _, z = encoder(v1)
            all_z.append(z)
        all_z = torch.cat(all_z, dim=0)

    metrics = matched_eval_metrics(all_z)
    probes = {
        "probe_1pct": train_probe_fraction(encoder, train_loader, test_loader, 0.01, seed),
        "probe_5pct": train_probe_fraction(encoder, train_loader, test_loader, 0.05, seed),
        "probe_10pct": train_probe_fraction(encoder, train_loader, test_loader, 0.10, seed),
        "probe_100pct": train_probe_fraction(encoder, train_loader, test_loader, 1.0, seed),
        "knn_5": eval_5nn(encoder, train_loader, test_loader, 5)
    }

    return {"metrics": metrics, "probes": probes, "grad_cos_sim": float(mean_grad_cos)}


def main():
    seeds = [2026, 2027, 2028, 2029, 2030, 2031, 2032, 2033, 2034, 2035]
    variants = [
        "Moments Only",
        "RBF Pure",
        "RBF+Moments",
        "Q Pure",
        "Q+Moments",
        "SIGReg",
        "Untrained"
    ]
    
    results = {v: {} for v in variants}
    
    print("Starting matched 10-seed evaluation...")
    for seed in seeds:
        print(f"Seed {seed}")
        for v in variants:
            print(f"  Training {v}...")
            res = train_matched_variant(v, seed)
            results[v][seed] = res

    # Compute paired stats
    # ds = Q+Moments - RBF+Moments
    # dpure = Q Pure - RBF Pure
    # dsig = Q+Moments - SIGReg
    paired_stats = {}
    def calc_stats(name, d_vals):
        d_vals = np.array(d_vals)
        mean = np.mean(d_vals)
        se = np.std(d_vals) / np.sqrt(len(d_vals))
        boot = [np.mean(np.random.choice(d_vals, size=len(d_vals), replace=True)) for _ in range(10000)]
        ci_lower, ci_upper = np.percentile(boot, [2.5, 97.5])
        wins = np.sum(d_vals < 0)  # Lower MMD is better
        ties = np.sum(d_vals == 0)
        losses = np.sum(d_vals > 0)
        
        # Wilcoxon signed-rank
        if np.all(d_vals == 0):
            p_val = 1.0
        else:
            _, p_val = scipy.stats.wilcoxon(d_vals)
            
        return {
            "mean_diff": float(mean),
            "se": float(se),
            "ci_95": [float(ci_lower), float(ci_upper)],
            "wins": int(wins),
            "ties": int(ties),
            "losses": int(losses),
            "p_value": float(p_val)
        }

    q_mom_mmd = [results["Q+Moments"][s]["metrics"]["held_out_rbf_mmd2"] for s in seeds]
    rbf_mom_mmd = [results["RBF+Moments"][s]["metrics"]["held_out_rbf_mmd2"] for s in seeds]
    q_pure_mmd = [results["Q Pure"][s]["metrics"]["held_out_rbf_mmd2"] for s in seeds]
    rbf_pure_mmd = [results["RBF Pure"][s]["metrics"]["held_out_rbf_mmd2"] for s in seeds]
    sig_mmd = [results["SIGReg"][s]["metrics"]["held_out_rbf_mmd2"] for s in seeds]

    paired_stats["Q+Moments_vs_RBF+Moments"] = calc_stats("d_s", np.array(q_mom_mmd) - np.array(rbf_mom_mmd))
    paired_stats["Q_Pure_vs_RBF_Pure"] = calc_stats("d_pure", np.array(q_pure_mmd) - np.array(rbf_pure_mmd))
    paired_stats["Q+Moments_vs_SIGReg"] = calc_stats("d_sigreg", np.array(q_mom_mmd) - np.array(sig_mmd))

    output = {
        "seeds": seeds,
        "variants": variants,
        "results": results,
        "paired_stats": paired_stats
    }
    
    with open("results/q_sigreg/matched_10seed_results.json", "w") as f:
        json.dump(output, f, indent=2)
        
    print("Writing markdown report...")
    with open("artifacts/q-sigreg-10seed/REPORT.md", "w") as f:
        f.write("# Matched 10-Seed Ablation Protocol for Q-SIGReg\n\n")
        f.write("## Paired Statistics (10 seeds)\n\n")
        for comp, stats in paired_stats.items():
            f.write(f"### {comp}\n")
            f.write(f"- **Mean Diff**: {stats['mean_diff']:.6f} +/- {stats['se']:.6f}\n")
            f.write(f"- **95% Bootstrap CI**: [{stats['ci_95'][0]:.6f}, {stats['ci_95'][1]:.6f}]\n")
            f.write(f"- **Wins/Ties/Losses**: {stats['wins']} / {stats['ties']} / {stats['losses']}\n")
            f.write(f"- **Wilcoxon p-value**: {stats['p_value']:.4e}\n\n")

        f.write("## Aggregated Metrics\n\n")
        
        # Aggregate table
        f.write("| Variant | Probe 1% | Probe 5% | Probe 100% | 5-NN | Eff Rank | Cov Frobenius | Energy Dist | MMD^2 (1.0 \\sigma) | Q-MMD^2 |\n")
        f.write("|---------|----------|----------|------------|------|----------|---------------|-------------|--------------------|---------|\n")
        for v in variants:
            p1 = np.mean([results[v][s]["probes"]["probe_1pct"] for s in seeds])
            p5 = np.mean([results[v][s]["probes"]["probe_5pct"] for s in seeds])
            p100 = np.mean([results[v][s]["probes"]["probe_100pct"] for s in seeds])
            knn = np.mean([results[v][s]["probes"]["knn_5"] for s in seeds])
            er = np.mean([results[v][s]["metrics"]["effective_rank_exact"] for s in seeds])
            cov_err = np.mean([results[v][s]["metrics"]["covariance_frobenius_error"] for s in seeds])
            ed = np.mean([results[v][s]["metrics"]["energy_distance"] for s in seeds])
            mmd = np.mean([results[v][s]["metrics"]["held_out_rbf_mmd2"] for s in seeds])
            qmmd = np.mean([results[v][s]["metrics"]["held_out_q_mmd2"] for s in seeds])
            f.write(f"| {v} | {p1:.2f}% | {p5:.2f}% | {p100:.2f}% | {knn:.2f}% | {er:.2f} | {cov_err:.4f} | {ed:.4f} | {mmd:.4f} | {qmmd:.4f} |\n")

        f.write("\n## Quantum Kernel Diagnostics\n\n")
        f.write("| Variant | Grad Cos Sim | G Min Eig | G Max Eig | G Cond Num | G Eff Rank | G Mean Off-Diag |\n")
        f.write("|---------|--------------|-----------|-----------|------------|------------|-----------------|\n")
        for v in variants:
            gcs = np.mean([results[v][s]["grad_cos_sim"] for s in seeds])
            gmin = np.mean([results[v][s]["metrics"]["q_gram_min_eig"] for s in seeds])
            gmax = np.mean([results[v][s]["metrics"]["q_gram_max_eig"] for s in seeds])
            gcond = np.mean([results[v][s]["metrics"]["q_gram_cond_num"] for s in seeds])
            ger = np.mean([results[v][s]["metrics"]["q_gram_eff_rank"] for s in seeds])
            gmod = np.mean([results[v][s]["metrics"]["q_gram_mean_off_diag"] for s in seeds])
            f.write(f"| {v} | {gcs:.4f} | {gmin:.4f} | {gmax:.4f} | {gcond:.4e} | {ger:.2f} | {gmod:.4f} |\n")

    print("Done!")

if __name__ == "__main__":
    main()


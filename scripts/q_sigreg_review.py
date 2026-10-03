"""Independent reproduction and fairness audit of the synthetic Q-SIGReg study."""

import hashlib
import json
import time
import warnings
from pathlib import Path

import numpy as np
import torch

from q_sigreg.metrics import effective_rank
from q_sigreg.train import run_full_lejepa_study, train_lejepa_variant


def moment_bias_pilot():
    rng = np.random.default_rng(818)
    rows = []
    for batch in [8, 64]:
        d = 4
        optimum = (1 - 1 / (2 * batch)) / (1 + (d + 1) / (batch - 1))
        x = rng.normal(size=(20000, batch, d))
        mu = x.mean(1)
        centered = x - mu[:, None, :]
        cov = np.einsum("nbi,nbj->nij", centered, centered) / (batch - 1)
        for variance in [0.4, optimum, 0.7, 1.0]:
            loss = variance * np.square(mu).sum(1) + np.square(
                variance * cov - np.eye(d)
            ).sum((1, 2))
            exact = (
                d * (variance - 1) ** 2
                + d * (d + 1) * variance**2 / (batch - 1)
                + d * variance / batch
            )
            rows.append(
                {
                    "batch": batch,
                    "population_variance": variance,
                    "expected_penalty_analytic": exact,
                    "expected_penalty_monte_carlo": float(loss.mean()),
                    "monte_carlo_sem": float(loss.std(ddof=1) / np.sqrt(len(loss))),
                    "minimizing_isotropic_variance": optimum,
                }
            )
    return rows


def main():
    torch.set_num_threads(1)
    start = time.perf_counter()
    output = Path("artifacts/q-sigreg-review-20261003")
    output.mkdir(exist_ok=True)
    study = run_full_lejepa_study()
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", RuntimeWarning)
        zero = [
            train_lejepa_variant("No Regularizer", seed=seed, epochs=0)
            for seed in [2026, 2027, 2028]
        ]
    # Empty training history means NaN final loss; omit it, rather than invalid JSON.
    for row in zero:
        row.pop("final_jepa_loss")
    result = {
        "synthetic_study": study,
        "zero_epoch_probes": zero,
        "expected_moment_penalty": moment_bias_pilot(),
        "zero_covariance_reported_effective_rank": effective_rank(
            torch.zeros((4, 4), dtype=torch.float64)
        ),
        "torch_threads": torch.get_num_threads(),
        "elapsed_seconds": time.perf_counter() - start,
        "scope": "Independent exact-statevector synthetic reproduction; no QPU or shot-based training",
    }
    (output / "results.json").write_text(
        json.dumps(result, indent=2, allow_nan=False) + "\n"
    )
    paths = [
        "scripts/q_sigreg_review.py",
        "q_sigreg/train.py",
        "q_sigreg/kernel.py",
        "q_sigreg/mmd.py",
        "q_sigreg/regularizers.py",
        "q_sigreg/metrics.py",
    ]
    manifest = {
        "files_sha256": {
            "results.json": hashlib.sha256(
                (output / "results.json").read_bytes()
            ).hexdigest()
        },
        "source_sha256": {
            p: hashlib.sha256(Path(p).read_bytes()).hexdigest() for p in paths
        },
    }
    (output / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    print("Zero-epoch probe accuracy:", [r["probe_accuracy"] for r in zero])
    print(
        "Zero covariance effective rank:",
        result["zero_covariance_reported_effective_rank"],
    )
    print("Elapsed:", result["elapsed_seconds"])


if __name__ == "__main__":
    main()

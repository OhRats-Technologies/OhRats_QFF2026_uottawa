"""Independent corrections to matched-study probes and statistical interpretation."""

import hashlib
import json
from pathlib import Path
from unittest.mock import patch

import numpy as np
import torch
from scipy.stats import wilcoxon

from scripts import run_matched_ablation as study


def holm_adjust(pvalues):
    p = np.asarray(pvalues, dtype=float)
    order = np.argsort(p)
    adjusted = np.empty(len(p))
    running = 0.0
    for rank, index in enumerate(order):
        running = max(running, (len(p) - rank) * p[index])
        adjusted[index] = min(1.0, running)
    return adjusted.tolist()


def recompute_stats(document, bootstrap_seed=761):
    pairs = [
        ("Q+Moments", "RBF+Moments"),
        ("Q Pure", "RBF Pure"),
        ("Q+Moments", "SIGReg"),
    ]
    rng = np.random.default_rng(bootstrap_seed)
    rows = []
    for a, b in pairs:
        differences = np.array(
            [
                document["results"][a][str(seed)]["metrics"]["held_out_rbf_mmd2"]
                - document["results"][b][str(seed)]["metrics"]["held_out_rbf_mmd2"]
                for seed in document["seeds"]
            ]
        )
        bootstrap = differences[
            rng.integers(len(differences), size=(10000, len(differences)))
        ].mean(1)
        rows.append(
            {
                "quantum": a,
                "comparison": b,
                "differences": differences.tolist(),
                "mean_difference": float(differences.mean()),
                "sample_standard_error": float(
                    differences.std(ddof=1) / np.sqrt(len(differences))
                ),
                "bootstrap_95_percent": np.quantile(bootstrap, [0.025, 0.975]).tolist(),
                "wilcoxon_p": float(wilcoxon(differences).pvalue),
                "wins": int((differences < 0).sum()),
                "losses": int((differences > 0).sum()),
            }
        )
    for row, adjusted in zip(rows, holm_adjust([r["wilcoxon_p"] for r in rows])):
        row["holm_p_three_reported_comparisons"] = adjusted
    return rows


def corrected_untrained(seed, epochs=40):
    original = study.train_probe_fraction
    records = []

    def trained_classifier(*args, **kwargs):
        requested = kwargs.get("epochs", 40)
        kwargs["epochs"] = epochs
        encoder = args[0]
        before = {name: value.clone() for name, value in encoder.state_dict().items()}
        result = original(*args, **kwargs)
        if any(
            not torch.equal(value, encoder.state_dict()[name])
            for name, value in before.items()
        ):
            raise RuntimeError("Frozen random encoder changed during supervised probe")
        records.append(
            {
                "fraction": args[3],
                "original_requested_epochs": requested,
                "actual_classifier_epochs": epochs,
                "encoder_unchanged": True,
            }
        )
        return result

    with patch.object(study, "train_probe_fraction", trained_classifier):
        result = study.train_matched_variant("Untrained", seed)
    result["seed"] = seed
    result["probe_training_audit"] = records
    return result


def main():
    torch.set_num_threads(1)
    source = Path("results/q_sigreg/matched_10seed_results.json")
    original = json.loads(source.read_text())
    corrected = [corrected_untrained(seed) for seed in original["seeds"]]
    result = {
        "original_results_sha256": hashlib.sha256(source.read_bytes()).hexdigest(),
        "paired_statistics": recompute_stats(original),
        "corrected_frozen_random_encoder": corrected,
        "scope": "Original trained variants preserved; corrected random-encoder classifier epochs and recomputed statistics only",
    }
    output = Path("artifacts/q-sigreg-matched-audit-20261003")
    output.mkdir(exist_ok=True)
    (output / "results.json").write_text(
        json.dumps(result, indent=2, allow_nan=False) + "\n"
    )
    files = [
        "scripts/q_sigreg_matched_audit.py",
        "scripts/run_matched_ablation.py",
        "q_sigreg/train.py",
    ]
    (output / "manifest.json").write_text(
        json.dumps(
            {
                "files_sha256": {
                    "results.json": hashlib.sha256(
                        (output / "results.json").read_bytes()
                    ).hexdigest()
                },
                "source_sha256": {
                    p: hashlib.sha256(Path(p).read_bytes()).hexdigest() for p in files
                },
            },
            indent=2,
        )
        + "\n"
    )
    print(
        "Corrected untrained means:",
        {
            name: float(np.mean([r["probes"][name] for r in corrected]))
            for name in corrected[0]["probes"]
        },
    )
    print("Paired statistics:", result["paired_statistics"])


if __name__ == "__main__":
    main()

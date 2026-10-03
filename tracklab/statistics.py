"""Uncertainty summaries for fixed experiments; no selection using final test scores."""

import csv, json
import numpy as np
from flybrain.data import REPO
from flybrain.progress import record


def bootstrap_rmse_ratio(a, b, seed=2026, repeats=2000):
    """Ratio RMSE(b)/RMSE(a), paired resampling of experiment replicates."""
    a, b = np.asarray(a), np.asarray(b)
    if a.shape != b.shape or len(a) < 20:
        raise ValueError("At least 20 paired estimates needed")
    rng = np.random.default_rng(seed)
    indices = rng.integers(0, len(a), (repeats, len(a)))
    ratios = np.sqrt(
        np.mean(b[indices] ** 2, axis=1) / np.mean(a[indices] ** 2, axis=1)
    )
    return {
        "rmse_ratio": float(np.sqrt(np.mean(b**2) / np.mean(a**2))),
        "bootstrap95": np.quantile(ratios, [0.025, 0.975]).tolist(),
        "interpretation": "Conditional Monte Carlo uncertainty on this fixed state and sampling model, not hardware or model uncertainty",
    }


def main():
    rows = list(csv.DictReader((REPO / "results/eigenbudget/samples.csv").open()))
    comparisons = []
    for offset in [0.0, 0.2, 0.6, 1.2]:
        for budget in [2048, 8192]:
            selected = [
                r
                for r in rows
                if float(r["offset"]) == offset and int(r["budget"]) == budget
            ]

            def errors(method):
                group = sorted(
                    (r for r in selected if r["method"] == method),
                    key=lambda r: int(r["repeat"]),
                )
                return [float(r["error_from_prepared_state"]) for r in group]

            for method in ["pilot_adaptive", "regularized_adaptive"]:
                comparisons.append(
                    {
                        "offset": offset,
                        "paid_budget": budget,
                        "method": method,
                        **bootstrap_rmse_ratio(errors("uniform"), errors(method)),
                    }
                )
    runs = [json.loads((REPO / "results/kernelforge/metrics.json").read_text())]
    runs += [
        json.loads(p.read_text())
        for p in sorted(
            (REPO / "results/kernelforge-replications").glob("*/metrics.json")
        )
    ]
    qml = []
    for r in runs:
        scores = {
            s["model"]: s["test_accuracy"]
            for s in r["scores"]
            if s["shots_per_observable"] == 0
        }
        qml.append(
            {
                "seed": r["seed"],
                "selected": r["selected"]["name"],
                "test_size": len(r["test_labels"]),
                **scores,
            }
        )
    aggregate = {
        name: {
            "mean_accuracy": float(np.mean([r[name] for r in qml])),
            "split_standard_deviation": float(np.std([r[name] for r in qml], ddof=1)),
        }
        for name in [
            "classical_PCA3_linear",
            "classical_PCA3_RBF",
            "classical_full13_RBF",
            "synthetic_noise_exact",
        ]
    }
    out = REPO / "results/statistics"
    out.mkdir(parents=True, exist_ok=True)
    report = {
        "eigenbudget_comparisons": comparisons,
        "qml_splits": qml,
        "qml_aggregate": aggregate,
        "qml_uncertainty": "Five overlapping stratified splits are sensitivity analysis, not five independent datasets or a valid population confidence interval.",
    }
    (out / "summary.json").write_text(json.dumps(report, indent=2) + "\n")
    record(
        "sprint",
        "statistical_validation",
        "passed",
        paired_bootstrap_comparisons=len(comparisons),
        qml_fixed_split_replications=len(runs),
        test_selection_leakage=False,
    )
    print(
        json.dumps({"eigenbudget_comparisons": comparisons, "qml_aggregate": aggregate})
    )


if __name__ == "__main__":
    main()

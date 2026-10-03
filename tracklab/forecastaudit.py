"""Shot-matched diagnostic of returned FlyWalk counts and a local forecast."""

import csv, json
import numpy as np
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from flybrain.data import REPO
from flybrain.progress import timed_stage


def compare(actual, forecast, repeats=4000, seed=2026):
    """Conditional predictive envelope, not a calibration-uncertainty interval."""
    reference = np.asarray(forecast["observed"], dtype=float)
    ideal = np.asarray(actual["expected"], dtype=float)
    observed = np.asarray(actual["observed"], dtype=float)
    if reference.shape != ideal.shape or observed.shape != ideal.shape:
        raise ValueError("Mismatched probability vectors")
    for p in [reference, ideal, observed]:
        if np.any(p < 0) or not np.isclose(p.sum(), 1):
            raise ValueError("Invalid probability distribution")
    samples = (
        np.random.default_rng(seed).multinomial(
            actual["actual_shots"], reference, size=repeats
        )
        / actual["actual_shots"]
    )
    tv = np.abs(samples - ideal).sum(axis=1) / 2
    return {
        "case": actual["case"],
        "predictive_seed": seed,
        "hardware_shots": actual["actual_shots"],
        "forecast_probability_estimation_shots": forecast["actual_shots"],
        "hardware_tv_from_ideal": float(np.abs(observed - ideal).sum() / 2),
        "forecast_probability_tv_from_ideal": float(
            np.abs(reference - ideal).sum() / 2
        ),
        "hardware_tv_from_forecast": float(np.abs(observed - reference).sum() / 2),
        "shot_matched_forecast_mean_tv": float(tv.mean()),
        "conditional_predictive_95": np.quantile(tv, [0.025, 0.975]).tolist(),
    }, tv


def main():
    ev = json.loads((REPO / "results/evidence/summary.json").read_text())
    rows, samples = [], []
    with timed_stage("forecastaudit", "shot_matched_returned_fly_counts") as checks:
        for i, actual in enumerate(
            r
            for r in ev["physical_metrics"]
            if r["project"] == "FlyWalk" and r["origin"] == "REAL_IBM_HARDWARE"
        ):
            forecast = next(
                r
                for r in ev["physical_metrics"]
                if r["project"] == "FlyWalk"
                and r["origin"] == "LOCAL_CALIBRATION_FORECAST"
                and r["case"] == actual["case"]
            )
            row, tv = compare(actual, forecast, seed=2026 + i)
            rows.append(row)
            samples.append(tv)
        if len(rows) != 4:
            raise ValueError("Requires all four returned FlyWalk circuits")
        checks.update(
            cases=len(rows),
            predictive_repeats_per_case=4000,
            hardware_shots_per_case=1024,
            new_hardware_jobs=0,
        )
    out = REPO / "results/forecastaudit"
    out.mkdir(exist_ok=True)
    (out / "metrics.json").write_text(
        json.dumps(
            {
                "evidence": "REAL_IBM_HARDWARE_compared_with_LOCAL_CALIBRATION_FORECAST",
                "seed": 2026,
                "repeats": 4000,
                "rows": rows,
                "interpretation": "Exploratory diagnostic chosen after counts returned. Each local forecast was sampled at 8192 shots; its empirical frequencies are treated as fixed probabilities for 4000 shot-matched multinomial predictions at 1024 shots. Envelopes condition on this finite empirical reference and omit uncertainty in its estimation, calibration, device drift and correlated noise. They are not hardware confidence intervals, p-values or guarantees of forecast accuracy. No result identifies a unique error mechanism.",
            },
            indent=2,
        )
        + "\n"
    )
    with (out / "predictions.csv").open("w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["case", "repeat", "tv_from_ideal"])
        for row, draws in zip(rows, samples):
            writer.writerows((row["case"], i, float(v)) for i, v in enumerate(draws))
    fig, axs = plt.subplots(1, 2, figsize=(11, 4), layout="constrained")
    x = np.arange(4)
    axs[0].bar(
        x - 0.18,
        [r["forecast_probability_tv_from_ideal"] for r in rows],
        0.36,
        label="Local forecast frequencies",
        color="#107d73",
    )
    axs[0].bar(
        x + 0.18,
        [r["hardware_tv_from_ideal"] for r in rows],
        0.36,
        label="Returned IBM frequencies",
        color="#7044bd",
    )
    axs[0].set_ylabel("Plug-in TV from ideal")
    axs[0].legend(fontsize=8)
    for i, r in enumerate(rows):
        low, high = r["conditional_predictive_95"]
        mean = r["shot_matched_forecast_mean_tv"]
        axs[1].plot([i, i], [low, high], color="#107d73", linewidth=5)
        axs[1].plot(i, mean, "o", color="#107d73")
        axs[1].plot(i, r["hardware_tv_from_ideal"], "x", color="#7044bd", markersize=9)
    axs[1].set_ylabel("TV from ideal at 1024 shots")
    axs[1].set_title("Conditional forecast envelope / IBM crosses", fontsize=10)
    for ax in axs:
        ax.set_xticks(x, ["Zero time", "Intact t4", "Intact t8", "Lesion t8"])
        ax.set_ylim(bottom=0)
        ax.spines[["top", "right"]].set_visible(False)
    fig.suptitle("A calibration forecast is a model, not a measurement", fontsize=13)
    fig.savefig(out / "forecastaudit.png", dpi=160)
    plt.close(fig)
    print(json.dumps({"cases": 4, "new_hardware_jobs": 0, "rows": rows}))


if __name__ == "__main__":
    main()

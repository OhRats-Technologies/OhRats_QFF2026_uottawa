"""Derive physical metrics while preserving the origin of every count sample."""

import json
from flybrain.data import REPO
from .chemistry import energy_from_counts
from .scheduling import distribution_metrics
from .spinweave import measured_energy
from .spinshield import hoeffding_margin


def analyze(cases, origin):
    import numpy as np

    output = []
    for case in cases:
        if case["name"] in ["zero_time_control", "intact_t4", "intact_t8", "lesion_t8"]:
            expected = np.asarray(case["expected"])
            observed = np.asarray(case["observed"])
            output.append(
                {
                    "project": "FlyWalk",
                    "origin": origin,
                    "case": case["name"],
                    "actual_shots": case["actual_shots"],
                    "expected": expected.tolist(),
                    "observed": observed.tolist(),
                    "total_variation_from_ideal": float(
                        np.abs(observed - expected).sum() / 2
                    ),
                    "source_return_probability": float(observed[0]),
                    "ideal_source_return_probability": float(expected[0]),
                }
            )
    for distance in [0.735, 1.4]:
        pair = [c for c in cases if c.get("distance") == distance and "model" in c]
        if len(pair) != 2:
            continue
        z = next(c for c in pair if c["basis"] == "z")
        bell = next(c for c in pair if c["basis"] == "bell")
        raw = energy_from_counts(z["model"], z["counts"], bell["counts"])
        filtered = energy_from_counts(z["model"], z["counts"], bell["counts"], True)
        output.append(
            {
                "project": "BondBench",
                "origin": origin,
                "distance": distance,
                "exact_energy": z["model"]["exact_total"],
                "raw": raw,
                "filtered": filtered,
                "paid_shots": z["actual_shots"] + bell["actual_shots"],
            }
        )
    for c in cases:
        if c["name"].startswith("gridguard"):
            output.append(
                {
                    "project": "GridGuard",
                    "origin": origin,
                    "case": c["name"],
                    **distribution_metrics(np.array(c["observed"])),
                }
            )
    spin = [c for c in cases if c["name"].startswith("spinweave")]
    if len(spin) == 3:
        ordered = [next(c for c in spin if c["basis"] == axis) for axis in "xyz"]
        model = ordered[0]["spin_model"]
        estimate = measured_energy(model["couplings"], [c["counts"] for c in ordered])
        upper = estimate["energy"] + 1.96 * estimate["standard_error"]
        fixed_upper = estimate["energy"] + hoeffding_margin(
            [sum(c["counts"].values()) for c in ordered],
            [sum(model["couplings"]) / 2] * 3,
        )
        output.append(
            {
                "project": "SpinWeave",
                "origin": origin,
                "delta": model["delta"],
                "exact_energy": model["exact_energy"],
                **estimate,
                "approx95_upper": upper,
                "hoeffding_sampling_upper": fixed_upper,
                "hoeffding_alpha": 0.05,
                "separable_bound": model["separable_energy_bound"],
                "witness_detected_sampling_model": bool(
                    fixed_upper < model["separable_energy_bound"]
                ),
                "systematic_measurement_bias_covered": False,
            }
        )
    return output


def main():
    rows = []
    statuses = []
    for folder in ["hardware", "chemistry-hardware", "scheduling-hardware"]:
        root = REPO / "results" / folder
        if (root / "collected.json").exists():
            r = json.loads((root / "collected.json").read_text())
            rows.extend(analyze(r["cases"], "REAL_IBM_HARDWARE"))
            statuses.append(
                {"folder": folder, "status": "COLLECTED", "backend": r["backend"]}
            )
        elif (root / "submitted.json").exists():
            r = json.loads((root / "submitted.json").read_text())
            status = (
                json.loads((root / "status.json").read_text())
                if (root / "status.json").exists()
                else r
            )
            statuses.append(
                {"folder": folder, "status": status["status"], "backend": r["backend"]}
            )
    forecast = REPO / "results/calibrated/forecast.json"
    if forecast.exists():
        rows.extend(
            analyze(
                json.loads(forecast.read_text())["cases"], "LOCAL_CALIBRATION_FORECAST"
            )
        )
    output = REPO / "results/evidence"
    output.mkdir(parents=True, exist_ok=True)
    (output / "summary.json").write_text(
        json.dumps({"hardware_status": statuses, "physical_metrics": rows}, indent=2)
        + "\n"
    )
    print(json.dumps({"hardware_status": statuses, "physical_metrics": rows}))


if __name__ == "__main__":
    main()

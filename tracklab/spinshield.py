"""Finite-shot entanglement decisions with declared measurement-bias allowances."""

import argparse, csv, json
from pathlib import Path
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from qiskit import QuantumCircuit
from qiskit.quantum_info import DensityMatrix
from flybrain.data import REPO
from flybrain.noise import readout_distribution
from flybrain.progress import timed_stage
from .spinweave import hamiltonian, BONDS, measurement_circuits
from .spintherm import gibbs


def hoeffding_margin(shots, ranges, alpha=0.05):
    """One-sided weighted Hoeffding bound for independent fixed-count groups."""
    shots = np.asarray(shots, dtype=float)
    ranges = np.asarray(ranges, dtype=float)
    if (
        shots.shape != ranges.shape
        or np.any(shots <= 0)
        or np.any(shots != np.floor(shots))
        or np.any(ranges < 0)
    ):
        raise ValueError(
            "Positive shot counts and matching nonnegative ranges required"
        )
    if (
        not np.all(np.isfinite(shots))
        or not np.all(np.isfinite(ranges))
        or not 0 < alpha < 1
    ):
        raise ValueError("Finite inputs and alpha in (0,1) required")
    return float(np.sqrt(0.5 * np.log(1 / alpha) * np.sum(ranges**2 / shots)))


def readout_bias_bound(couplings, max_flip):
    """Absolute total-energy bias under independent symmetric flips <= max_flip."""
    if (
        not 0 <= max_flip <= 0.5
        or not np.all(np.isfinite(couplings))
        or np.any(np.asarray(couplings) < 0)
    ):
        raise ValueError("Invalid readout bound or coupling")
    return float(3 * sum(couplings) / 4 * (1 - (1 - 2 * max_flip) ** 2))


def values(couplings):
    return np.array(
        [
            sum(
                j * (1 - 2 * ((bits >> a) & 1)) * (1 - 2 * ((bits >> b) & 1)) / 4
                for (a, b), j in zip(BONDS, couplings)
            )
            for bits in range(16)
        ]
    )


def planned_shots(expected_measured_energy, bias_allowance, alpha=0.05, beta=0.05):
    """Sufficient equal shots per basis for a fixed test with detection power >=1-beta.

    Assumes the expected measured energy is known independently before sampling;
    three basis ranges are two and the separable threshold is minus one.
    """
    if (
        not np.isfinite(expected_measured_energy)
        or not np.isfinite(bias_allowance)
        or bias_allowance < 0
    ):
        raise ValueError("Finite expectation and nonnegative bias allowance required")
    if not 0 < alpha < 1 or not 0 < beta < 1:
        raise ValueError("Alpha and beta must be in (0,1)")
    gap = -1 - expected_measured_energy - bias_allowance
    if gap <= 0:
        return None
    # Both the confidence margin and an upper-fluctuation power margin must fit the gap.
    return (
        int(
            np.floor(
                6
                * (np.sqrt(np.log(1 / alpha)) + np.sqrt(np.log(1 / beta))) ** 2
                / gap**2
            )
        )
        + 1
    )


def run(args):
    rows = []
    cases = []
    detail = []
    plans = []
    with timed_stage(
        "spinshield", "fixed_decision_confidence_and_bias_controls"
    ) as evidence:
        h0, j0 = hamiltonian(0.0)
        h1, j1 = hamiltonian(1.0)
        neel = np.zeros((16, 16))
        neel[5, 5] = 1
        states = [
            ("Neel product", 0.0, None, neel),
            ("Maximally mixed", 0.0, None, np.eye(16) / 16),
            ("Ring ground", 0.0, 0.0, gibbs(h0.to_matrix(), 0.0)),
            ("Warm ring", 0.0, 0.8, gibbs(h0.to_matrix(), 0.8)),
            ("Hot ring", 0.0, 1.2, gibbs(h0.to_matrix(), 1.2)),
            ("Warm dimers", 1.0, 1.0, gibbs(h1.to_matrix(), 1.0)),
        ]
        rotations = [
            c.remove_final_measurements(inplace=False)
            for c in measurement_circuits(QuantumCircuit(4))
        ]
        for name, delta, temperature, rho in states:
            h, j = hamiltonian(delta)
            truth = float(np.trace(rho @ h.to_matrix()).real)
            v = values(j)
            ideal = [DensityMatrix(rho).evolve(c).probabilities() for c in rotations]
            if abs(sum(p @ v for p in ideal) - truth) > 1e-10:
                raise ValueError("Rotated bases fail energy reconstruction")
            cases.append(
                {
                    "name": name,
                    "delta": delta,
                    "temperature": temperature,
                    "exact_energy": truth,
                    "known_fully_separable": name
                    in ["Neel product", "Maximally mixed"],
                }
            )
            for readout in [0.0, 0.02]:
                ps = [readout_distribution(p, readout) for p in ideal]
                noisy_mean = float(sum(p @ v for p in ps))
                bias = readout_bias_bound(j, readout)
                planned = planned_shots(noisy_mean, bias, args.alpha, 0.05)
                plans.append(
                    {
                        "case": name,
                        "readout": readout,
                        "known_expected_measured_energy": noisy_mean,
                        "bias_allowance": bias,
                        "shots_per_basis_sufficient": planned,
                        "total_shots_sufficient": None
                        if planned is None
                        else 3 * planned,
                        "target_power": 0.95,
                    }
                )
                if abs(noisy_mean - truth) > bias + 1e-12:
                    raise ValueError("Readout bias exceeds analytic bound")
                for shots in [64, 256, 1024]:
                    margin = hoeffding_margin([shots] * 3, [np.ptp(v)] * 3, args.alpha)
                    for repeat in range(args.repeats):
                        rng = np.random.default_rng(args.seed + shots + repeat)
                        counts = [rng.multinomial(shots, p) for p in ps]
                        means = [c @ v / shots for c in counts]
                        variances = [
                            c @ ((v - m) ** 2) / (shots - 1)
                            for c, m in zip(counts, means)
                        ]
                        energy = float(sum(means))
                        se = float(np.sqrt(sum(variances) / shots))
                        upper = energy + margin + bias
                        rows.append(
                            {
                                "case": name,
                                "readout": readout,
                                "shots_per_basis": shots,
                                "repeat": repeat,
                                "energy": energy,
                                "normal95_sampling_only": bool(energy + 1.96 * se < -1),
                                "hoeffding_sampling_only": bool(energy + margin < -1),
                                "hoeffding_with_bias": bool(upper < -1),
                                "upper_with_bias": upper,
                                "true_energy_covered": bool(truth <= upper),
                                "bias_allowance": bias,
                            }
                        )
                        if repeat == 0:
                            detail.append(
                                {
                                    "case": name,
                                    "readout": readout,
                                    "shots_per_basis": shots,
                                    "energy": energy,
                                    "hoeffding_margin": margin,
                                    "readout_bias_allowance": bias,
                                    "upper_with_bias": upper,
                                }
                            )
        evidence.update(
            states=6,
            decisions=len(rows),
            independent_basis_reference=True,
            analytic_readout_bound=True,
            confidence="Pointwise fixed decision; not adaptive stopping",
        )
    summaries = []
    for case in cases:
        for readout in [0.0, 0.02]:
            for shots in [64, 256, 1024]:
                selected = [
                    r
                    for r in rows
                    if r["case"] == case["name"]
                    and r["readout"] == readout
                    and r["shots_per_basis"] == shots
                ]
                summaries.append(
                    {
                        "case": case["name"],
                        "readout": readout,
                        "shots_per_basis": shots,
                        **{
                            key: float(np.mean([r[key] for r in selected]))
                            for key in [
                                "normal95_sampling_only",
                                "hoeffding_sampling_only",
                                "hoeffding_with_bias",
                                "true_energy_covered",
                            ]
                        },
                    }
                )
    report = {
        "origin": "EXACT_CLASSICAL_STATES_AND_INDEPENDENT_MULTINOMIAL_SAMPLING",
        "alpha": args.alpha,
        "repeats": args.repeats,
        "seed": args.seed,
        "cases": cases,
        "first_repeat_controls": detail,
        "summaries": summaries,
        "plans": plans,
        "planning_assumption": "Expected measured energy comes from an independently known classical reference before the trial. Sufficient equal-shot budget fits the alpha confidence margin and beta=0.05 upper-fluctuation margin inside the expected threshold gap. This sufficient power condition yields no finite budget when the expected gap after bias allowance is nonpositive. It does not establish separability. This is not a data-adaptive hardware guarantee.",
        "bound": "E_true <= E_hat + sqrt(log(1/alpha)/2 * sum_a range_a^2/n_a) + b, with probability >= 1-alpha, provided total absolute measurement bias <= b and independent fixed-count bounded samples.",
        "readout_bias": "b=3*sum(J)/4 * [1-(1-2*r_max)^2], assuming independent symmetric per-qubit readout flips <= r_max, correct basis rotations and a common prepared state.",
        "reference": "https://doi.org/10.1080/01621459.1963.10500830",
        "limitations": "Established Hoeffding inequality, not a new certification method. Pointwise confidence for one preselected decision, not a guarantee after repeated peeking, adaptive stopping or searching many states. Readout allowance is assumed, not inferred from IBM calibration. Unknown coherent basis errors, drift and correlated readout are not covered. Thermal states are classical references, not hardware preparations. Failure to detect does not prove separability.",
    }
    args.output.mkdir(parents=True, exist_ok=True)
    (args.output / "metrics.json").write_text(json.dumps(report, indent=2) + "\n")
    with (args.output / "samples.csv").open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=rows[0])
        w.writeheader()
        w.writerows(rows)
    fig, axes = plt.subplots(1, 2, figsize=(12, 5), constrained_layout=True)
    for ax, readout in zip(axes, [0.0, 0.02]):
        for name, color in [
            ("Ring ground", "#16817a"),
            ("Warm ring", "#7044bd"),
            ("Warm dimers", "#3874a2"),
            ("Neel product", "#ba5144"),
        ]:
            selected = [
                r for r in summaries if r["case"] == name and r["readout"] == readout
            ]
            ax.plot(
                [r["shots_per_basis"] for r in selected],
                [r["hoeffding_with_bias"] for r in selected],
                "o-",
                label=name,
                color=color,
            )
        ax.set(
            xscale="log",
            ylim=(-0.02, 1.02),
            xlabel="Shots per basis (three bases)",
            ylabel="Witness detection fraction",
            title=f"Fixed decisions; readout flip bound {readout:.0%}",
        )
        ax.legend(fontsize=8)
    fig.suptitle(
        "SpinShield | Conservative confidence plus an explicit measurement-bias allowance"
    )
    fig.savefig(args.output / "spinshield.png", dpi=160)
    plt.close(fig)
    print(
        json.dumps(
            {
                "cases": cases,
                "minimum_coverage": min(r["true_energy_covered"] for r in summaries),
                "separable_false_detection_max": max(
                    r["hoeffding_with_bias"]
                    for r in summaries
                    if r["case"] in ["Neel product", "Maximally mixed"]
                ),
            }
        )
    )


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--repeats", type=int, default=500)
    p.add_argument("--alpha", type=float, default=0.05)
    p.add_argument("--seed", type=int, default=2026)
    p.add_argument("--output", type=Path, default=REPO / "results/spinshield")
    args = p.parse_args()
    if not 20 <= args.repeats <= 2000 or not 0 < args.alpha < 1:
        p.error("Repeats 20–2000 and alpha in (0,1) required")
    run(args)


if __name__ == "__main__":
    main()

"""BudgetBond: pilot-based shot allocation, including pilot and rejection costs."""

import argparse
import csv
import json
from pathlib import Path
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from qiskit import transpile
from qiskit_aer import AerSimulator

from flybrain.data import REPO
from flybrain.noise import noise_model, readout_distribution
from flybrain.progress import timed_stage
from .chemistry import molecule, measurement_circuits, energy_from_counts, mean_and_se


def basis_values(model):
    c = model["coefficients"]

    def z(bits):
        z0, z1 = 1 - 2 * (bits & 1), 1 - 2 * ((bits >> 1) & 1)
        return c.get("IZ", 0) * z0 + c.get("ZI", 0) * z1 + c.get("ZZ", 0) * z0 * z1

    def bell(bits):
        xx, zz = 1 - 2 * (bits & 1), 1 - 2 * ((bits >> 1) & 1)
        return c.get("XX", 0) * xx - c.get("YY", 0) * xx * zz

    return z, bell


def allocate(pilot_counts, model, remaining, minimum=128):
    """Neyman weights sigma/sqrt(acceptance), estimated only from pilot counts."""
    if remaining < 2 * minimum:
        raise ValueError("Insufficient remaining budget")
    parity = model["parity"]
    accepts = [
        lambda b: b.bit_count() % 2 == parity,
        lambda b: ((b >> 1) & 1) == parity,
    ]
    weights = []
    for counts, value, accept in zip(pilot_counts, basis_values(model), accepts):
        _, se, accepted = mean_and_se(counts, value, accept)
        variance = se**2 * accepted
        acceptance = accepted / sum(counts.values())
        # Small floor guards a finite pilot that happened to observe zero variance.
        weights.append(np.sqrt(max(variance, 1e-6) / acceptance))
    fraction = weights[0] / sum(weights)
    nz = int(np.clip(round(remaining * fraction), minimum, remaining - minimum))
    return [nz, remaining - nz]


def sample(probabilities, shots, rng):
    return {
        format(i, "02b"): int(count)
        for i, count in enumerate(rng.multinomial(shots, probabilities))
        if count
    }


def regularized_allocate(pilot_counts, model, remaining, minimum=128):
    """Jeffreys half-count regularization avoids a pilot's zero-variance trap."""
    if remaining < 2 * minimum:
        raise ValueError("Insufficient remaining budget")
    parity = model["parity"]
    accepts = [
        lambda b: b.bit_count() % 2 == parity,
        lambda b: ((b >> 1) & 1) == parity,
    ]
    weights = []
    for counts, value, accept in zip(pilot_counts, basis_values(model), accepts):
        outcomes = [b for b in range(4) if accept(b)]
        accepted = sum(counts.get(format(b, "02b"), 0) for b in outcomes)
        pseudo = np.array([counts.get(format(b, "02b"), 0) + 0.5 for b in outcomes])
        probabilities = pseudo / pseudo.sum()
        values = np.array([value(b) for b in outcomes])
        variance = probabilities @ (values**2) - (probabilities @ values) ** 2
        acceptance = (accepted + 1) / (sum(counts.values()) + 2)
        weights.append(np.sqrt(max(variance, 1e-12) / acceptance))
    nz = int(
        np.clip(
            round(remaining * weights[0] / sum(weights)), minimum, remaining - minimum
        )
    )
    return [nz, remaining - nz]


def distributions(model, gate, readout, seed):
    circuits = transpile(
        list(measurement_circuits(model["circuit"])),
        basis_gates=["rz", "sx", "x", "cx"],
        optimization_level=1,
        seed_transpiler=seed,
    )
    sim = AerSimulator(
        method="density_matrix",
        noise_model=noise_model(gate, readout),
        max_parallel_threads=2,
    )
    probabilities = []
    for qc in circuits:
        exact = qc.remove_final_measurements(inplace=False)
        exact.save_density_matrix()
        rho = np.asarray(sim.run(exact, shots=1).result().data(0)["density_matrix"])
        p = readout_distribution(np.diag(rho).real, readout)
        if p.min() < -1e-10 or not np.isclose(p.sum(), 1):
            raise ValueError("Invalid exact noisy measurement probabilities")
        probabilities.append(np.maximum(p, 0) / p.sum())
    # One independent Aer sampled check per basis verifies the accelerated multinomial path.
    checks = sim.run(circuits, shots=32768, seed_simulator=seed).result().get_counts()
    for p, counts in zip(probabilities, checks):
        observed = np.array([counts.get(format(i, "02b"), 0) / 32768 for i in range(4)])
        if np.abs(observed - p).sum() / 2 > 0.025:
            raise ValueError("Aer counts disagree with exact measurement reference")
    return probabilities


def run(args):
    rows, references = [], []
    with timed_stage("budgetbond", "matched_budget_allocation") as evidence:
        for distance in [0.735, 1.4, 2.2]:
            model = molecule(distance)
            for case, gate, readout in [
                ("ideal", 0.0, 0.0),
                ("synthetic_noise", 0.01, 0.02),
            ]:
                probabilities = distributions(model, gate, readout, args.seed)
                references.append(
                    {
                        "distance": distance,
                        "case": case,
                        "probabilities": [p.tolist() for p in probabilities],
                    }
                )
                for repeat in range(args.repeats):
                    rng = np.random.default_rng(
                        args.seed + repeat + int(distance * 10000)
                    )
                    uniform = [sample(p, args.budget // 2, rng) for p in probabilities]
                    pilot = [sample(p, args.pilot, rng) for p in probabilities]
                    allocations = allocate(pilot, model, args.budget - 2 * args.pilot)
                    production = [
                        sample(p, n, rng) for p, n in zip(probabilities, allocations)
                    ]
                    for method, counts, filtered in [
                        ("uniform_raw", uniform, False),
                        ("uniform_filtered", uniform, True),
                        ("adaptive_filtered", production, True),
                    ]:
                        estimate = energy_from_counts(
                            model, *counts, postselect=filtered
                        )
                        rows.append(
                            {
                                "distance": distance,
                                "case": case,
                                "repeat": repeat,
                                "method": method,
                                "total_paid_shots": args.budget,
                                "pilot_shots": 2 * args.pilot
                                if method.startswith("adaptive")
                                else 0,
                                "production_z": sum(counts[0].values()),
                                "production_bell": sum(counts[1].values()),
                                "energy": estimate["energy"],
                                "error": estimate["energy"] - model["exact_total"],
                                "standard_error": estimate["standard_error"],
                                "acceptance": estimate["acceptance_fraction"],
                            }
                        )
        evidence.update(
            estimates=len(rows),
            matched_total_paid_shots=True,
            independent_production=True,
            pilot_included=True,
            aer_reference_checked=True,
        )
    summaries = []
    for distance in [0.735, 1.4, 2.2]:
        for case in ["ideal", "synthetic_noise"]:
            for method in ["uniform_raw", "uniform_filtered", "adaptive_filtered"]:
                selected = [
                    r
                    for r in rows
                    if r["distance"] == distance
                    and r["case"] == case
                    and r["method"] == method
                ]
                errors = np.array([r["error"] for r in selected])
                summaries.append(
                    {
                        "distance": distance,
                        "case": case,
                        "method": method,
                        "rmse": float(np.sqrt(np.mean(errors**2))),
                        "bias": float(errors.mean()),
                        "mae": float(np.abs(errors).mean()),
                        "mean_z_shots": float(
                            np.mean([r["production_z"] for r in selected])
                        ),
                    }
                )
    args.output.mkdir(parents=True, exist_ok=True)
    with (args.output / "samples.csv").open("w", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    metrics = {
        "evidence": "exact_Aer_density_matrix_plus_independent_multinomial_sampling",
        "budget": args.budget,
        "pilot_per_basis": args.pilot,
        "repeats": args.repeats,
        "seed": args.seed,
        "summaries": summaries,
        "references": references,
        "method": "Pilot Neyman allocation proportional to conditional sigma/sqrt(acceptance); pilot excluded from estimator but charged to budget; minimum 128 production shots per basis.",
        "limitations": "H2 minimal basis and illustrative noise; adaptive allocation is established statistics. Improvement is empirical, not guaranteed; pilot overhead may lose. No hardware validation of this controller yet.",
    }
    (args.output / "metrics.json").write_text(json.dumps(metrics, indent=2) + "\n")
    fig, axes = plt.subplots(1, 2, figsize=(13, 5), constrained_layout=True)
    colors = ["#c94747", "#16817a", "#784ec2"]
    for ax, case in zip(axes, ["ideal", "synthetic_noise"]):
        for offset, (method, color) in enumerate(
            zip(["uniform_raw", "uniform_filtered", "adaptive_filtered"], colors)
        ):
            selected = [
                s for s in summaries if s["case"] == case and s["method"] == method
            ]
            ax.bar(
                np.arange(3) + (offset - 1) * 0.24,
                [s["rmse"] for s in selected],
                width=0.24,
                label=method,
                color=color,
            )
        ax.set(
            xticks=np.arange(3),
            xticklabels=["0.735", "1.4", "2.2"],
            xlabel="H–H distance (angstrom)",
            ylabel="Energy RMSE (hartree)",
            title=case.replace("_", " "),
        )
        ax.legend(fontsize=8)
    fig.suptitle(
        f"BudgetBond | {args.budget} paid shots per estimate · pilots and rejected shots included"
    )
    fig.savefig(args.output / "budgetbond.png", dpi=160)
    plt.close(fig)
    print(json.dumps({"estimates": len(rows), "summaries": summaries}))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=REPO / "results/budgetbond")
    parser.add_argument("--budget", type=int, default=2048)
    parser.add_argument("--pilot", type=int, default=128)
    parser.add_argument("--repeats", type=int, default=200)
    parser.add_argument("--seed", type=int, default=2026)
    args = parser.parse_args()
    if (
        args.budget % 2
        or args.pilot < 32
        or args.budget - 2 * args.pilot < 256
        or not 20 <= args.repeats <= 2000
    ):
        parser.error(
            "Even budget, pilot >=32, remaining >=256, repeats 20–2000 required"
        )
    run(args)


if __name__ == "__main__":
    main()

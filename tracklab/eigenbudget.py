"""EigenBudget: when an adaptive measurement budget helps, and when it cannot."""

import argparse, csv, json
from pathlib import Path
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from qiskit.quantum_info import Statevector
from flybrain.data import REPO
from flybrain.progress import timed_stage
from .chemistry import molecule, measurement_circuits, energy_from_counts
from .budgetbond import sample, allocate, regularized_allocate, basis_values


def exact_variances(probabilities, values):
    return [float(p @ (v * v) - (p @ v) ** 2) for p, v in zip(probabilities, values)]


def run(args):
    model = molecule(0.735)
    rows = []
    theory = []
    with timed_stage("eigenbudget", "imperfect_state_budget_test") as evidence:
        for offset in [0.0, 0.2, 0.6, 1.2]:
            qc = model["circuit"].copy()
            qc.cx(0, 1)
            qc.ry(offset, 0)
            qc.cx(0, 1)
            probabilities = [
                Statevector.from_instruction(
                    c.remove_final_measurements(inplace=False)
                ).probabilities()
                for c in measurement_circuits(qc)
            ]
            values = [np.array([f(i) for i in range(4)]) for f in basis_values(model)]
            variances = exact_variances(probabilities, values)
            truth = float(
                model["coefficients"]["II"]
                + model["nuclear_energy"]
                + sum(p @ v for p, v in zip(probabilities, values))
            )
            if offset == 0 and not np.isclose(*variances, atol=1e-7):
                raise ValueError("Eigenstate equal-variance identity failed")
            theory.append(
                {
                    "theta_offset": offset,
                    "true_prepared_energy": truth,
                    "variance_z": variances[0],
                    "variance_bell": variances[1],
                    "oracle_z_fraction": float(
                        np.sqrt(variances[0]) / sum(np.sqrt(variances))
                    ),
                }
            )
            for budget in [2048, 8192]:
                for repeat in range(args.repeats):
                    rng = np.random.default_rng(args.seed + repeat + budget)
                    uniform = [sample(p, budget // 2, rng) for p in probabilities]
                    pilot = [sample(p, 64, rng) for p in probabilities]
                    allocation = allocate(pilot, model, budget - 128)
                    adaptive = [
                        sample(p, n, rng) for p, n in zip(probabilities, allocation)
                    ]
                    stable = regularized_allocate(pilot, model, budget - 128)
                    regularized = [
                        sample(p, n, rng) for p, n in zip(probabilities, stable)
                    ]
                    for method, counts in [
                        ("uniform", uniform),
                        ("pilot_adaptive", adaptive),
                        ("regularized_adaptive", regularized),
                    ]:
                        estimate = energy_from_counts(model, *counts, postselect=True)
                        rows.append(
                            {
                                "offset": offset,
                                "budget": budget,
                                "repeat": repeat,
                                "method": method,
                                "error_from_prepared_state": estimate["energy"] - truth,
                                "production_z": sum(counts[0].values()),
                                "paid_shots": budget,
                                "pilot_shots": 0 if method == "uniform" else 128,
                            }
                        )
        evidence.update(
            estimates=len(rows),
            reference="Prepared-state energy, not ground energy",
            equal_variance_identity=True,
            paid_pilot_included=True,
        )
    summaries = []
    for offset in [0.0, 0.2, 0.6, 1.2]:
        for budget in [2048, 8192]:
            for method in ["uniform", "pilot_adaptive", "regularized_adaptive"]:
                errors = np.array(
                    [
                        r["error_from_prepared_state"]
                        for r in rows
                        if r["offset"] == offset
                        and r["budget"] == budget
                        and r["method"] == method
                    ]
                )
                summaries.append(
                    {
                        "offset": offset,
                        "budget": budget,
                        "method": method,
                        "rmse": float(np.sqrt(np.mean(errors**2))),
                        "bias": float(errors.mean()),
                    }
                )
    args.output.mkdir(parents=True, exist_ok=True)
    with (args.output / "samples.csv").open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)
    report = {
        "evidence": "ideal_statevector_probabilities_and_independent_multinomial_sampling",
        "molecule": "H2 at 0.735 angstrom, STO-3G",
        "repeats": args.repeats,
        "seed": args.seed,
        "theory": theory,
        "summaries": summaries,
        "equal_variance_proof": "For H=A+B+cI and H|psi>=E|psi>, (A-<A>)|psi>=-(B-<B>)|psi>. Squared norms give Var(A)=Var(B). Independent group samples therefore minimize Var(A)/n_A+Var(B)/n_B at n_A=n_B for a fixed total. This identity is elementary, not claimed as a new theorem.",
        "interpretation": "A known allocation method has a state-dependent value. Offsets are controlled state-preparation perturbations, not a completed noisy VQE optimization trajectory.",
        "limitations": "Ideal sampling only; statevector ground-state reference available because this molecule is tiny. Adaptive allocation can lose from finite pilots. An oracle allocation is diagnostic, not an implementable performance baseline.",
    }
    (args.output / "metrics.json").write_text(json.dumps(report, indent=2) + "\n")
    fig, axes = plt.subplots(1, 2, figsize=(13, 5), constrained_layout=True)
    for ax, budget in zip(axes, [2048, 8192]):
        for method, color in [
            ("uniform", "#16817a"),
            ("pilot_adaptive", "#c94747"),
            ("regularized_adaptive", "#784ec2"),
        ]:
            s = [
                s for s in summaries if s["budget"] == budget and s["method"] == method
            ]
            ax.plot(
                [r["offset"] for r in s],
                [r["rmse"] for r in s],
                "o-",
                color=color,
                label=method,
            )
        ax.set(
            xlabel="Preparation angle offset from ground state (radians)",
            ylabel="Energy RMSE (hartree)",
            title=f"{budget} paid shots; adaptive pilot costs 128",
        )
        ax.legend()
    fig.suptitle(
        "EigenBudget | Equal variance at the eigenstate; allocation value changes away from it"
    )
    fig.savefig(args.output / "eigenbudget.png", dpi=160)
    plt.close(fig)
    print(json.dumps({"theory": theory, "summaries": summaries}))


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--seed", type=int, default=2026)
    p.add_argument("--repeats", type=int, default=400)
    p.add_argument("--output", type=Path, default=REPO / "results/eigenbudget")
    a = p.parse_args()
    if not 20 <= a.repeats <= 2000:
        p.error("Repeats 20–2000 required")
    run(a)


if __name__ == "__main__":
    main()

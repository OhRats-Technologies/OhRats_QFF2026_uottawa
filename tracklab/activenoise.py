"""Check whether LiH shot-allocation savings survive declared synthetic bias."""

import argparse, csv, json
from pathlib import Path
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from scipy.optimize import minimize
from qiskit import QuantumCircuit, transpile
from qiskit.quantum_info import Statevector, SparsePauliOp
from qiskit_aer import AerSimulator
from flybrain.data import REPO
from flybrain.noise import noise_model, readout_distribution
from flybrain.progress import timed_stage
from .activebudget import model, allocation


def preparation(grouped):
    operator = SparsePauliOp.from_list([term for g in grouped for term in g["terms"]])
    matrix = operator.to_matrix()
    target = float(np.linalg.eigvalsh(matrix).min())

    def circuit(parameters):
        qc = QuantumCircuit(2)
        qc.ry(float(parameters[0]), 0)
        qc.cx(0, 1)
        qc.ry(float(parameters[1]), 0)
        qc.ry(float(parameters[2]), 1)
        return qc

    def objective(parameters):
        return float(
            Statevector.from_instruction(circuit(parameters))
            .expectation_value(operator)
            .real
        )

    rng = np.random.default_rng(2026)
    best = min(
        [
            minimize(
                objective,
                rng.uniform(-np.pi, np.pi, 3),
                method="BFGS",
                options={"maxiter": 200, "gtol": 1e-9},
            )
            for _ in range(4)
        ],
        key=lambda r: r.fun,
    )
    if abs(best.fun - target) > 1e-8:
        raise ValueError("Real two-qubit preparation failed ground-energy check")
    return circuit(best.x), float(best.fun - target)


def run(args):
    rows = []
    references = []
    cases = [("ideal", 0.0, 0.0), ("readout", 0.0, 0.01), ("combined", 0.005, 0.01)]
    with timed_stage("activebudget", "synthetic_bias_control") as evidence:
        exact, constant, grouped, _ = model()
        qc, gap = preparation(grouped)
        circuits = []
        for g in grouped:
            m = qc.copy()
            for q, axis in enumerate(g["basis"][::-1]):
                if axis == "Y":
                    m.sdg(q)
                    m.h(q)
                elif axis == "X":
                    m.h(q)
            circuits.append(
                transpile(
                    m,
                    basis_gates=["rz", "sx", "x", "cx"],
                    optimization_level=1,
                    seed_transpiler=args.seed,
                )
            )
        vs = [g["values"] for g in grouped]
        for case, gate, readout in cases:
            sim = AerSimulator(
                method="density_matrix",
                noise_model=noise_model(gate, 0),
                max_parallel_threads=2,
            )
            ps = []
            for c in circuits:
                density = c.copy()
                density.save_density_matrix()
                rho = np.asarray(
                    sim.run(density, shots=1).result().data(0)["density_matrix"]
                )
                if (
                    not np.isclose(np.trace(rho), 1)
                    or np.linalg.eigvalsh(rho).min() < -1e-10
                ):
                    raise ValueError("Invalid density matrix")
                ps.append(readout_distribution(np.diag(rho).real, readout))
            mean = constant + sum(p @ v for p, v in zip(ps, vs))
            references.append(
                {
                    "case": case,
                    "gate_error": gate,
                    "readout_error": readout,
                    "exact_noisy_mean": mean,
                    "systematic_bias": mean - exact,
                }
            )
            for budget in [2048, 8192]:
                uniform = allocation(np.ones(4), budget, minimum=0)
                for repeat in range(args.repeats):
                    rng = np.random.default_rng(args.seed + budget + repeat)
                    pilot = [rng.multinomial(64, p) for p in ps]
                    posterior = [(c + 0.5) / 66 for c in pilot]
                    weights = [
                        np.sqrt(max(0, p @ (v * v) - (p @ v) ** 2))
                        for p, v in zip(posterior, vs)
                    ]
                    adaptive = allocation(weights, budget - 256)
                    for method, counts in [
                        ("uniform", uniform),
                        ("regularized_adaptive", adaptive),
                    ]:
                        sampled = [
                            rng.multinomial(int(n), p) for n, p in zip(counts, ps)
                        ]
                        energy = constant + sum(
                            c @ v / n for c, v, n in zip(sampled, vs, counts)
                        )
                        rows.append(
                            {
                                "case": case,
                                "budget": budget,
                                "repeat": repeat,
                                "method": method,
                                "error_ground": energy - exact,
                                "error_noisy_mean": energy - mean,
                                "paid_shots": budget,
                            }
                        )
        evidence.update(
            ground_preparation_gap=gap,
            noise_cases=3,
            estimates=len(rows),
            density_checks=True,
        )
    summaries = []
    for case, _, _ in cases:
        for budget in [2048, 8192]:
            summary = {"case": case, "budget": budget, "methods": {}}
            for method in ["uniform", "regularized_adaptive"]:
                selected = [
                    r
                    for r in rows
                    if r["case"] == case
                    and r["budget"] == budget
                    and r["method"] == method
                ]
                summary["methods"][method] = {
                    key: float(np.sqrt(np.mean([r[key] ** 2 for r in selected])))
                    for key in ["error_ground", "error_noisy_mean"]
                }
            summaries.append(summary)
    report = {
        "origin": "LOCAL_SYNTHETIC_DENSITY_MATRIX_AND_MULTINOMIAL_SIMULATION",
        "reference_casci_energy": exact,
        "preparation": "Three real RY angles and one CX, optimized classically against the tiny exact Hamiltonian",
        "preparation_gap": gap,
        "compiled_basis_costs": [dict(c.count_ops()) for c in circuits],
        "repeats": args.repeats,
        "seed": args.seed,
        "references": references,
        "summaries": summaries,
        "noise": "Synthetic CX depolarizing p; sx/x depolarizing p/10; ideal rz; independent symmetric readout flips r. No IBM calibration is claimed.",
        "limitations": "Fixed ideal preparation, not noisy VQE training. No mitigation. Shot allocation targets variance; it cannot remove gate/readout bias. Sampling error around the noisy mean and total error against CASCI are reported separately. This follows earlier exploratory allocation findings.",
    }
    args.output.mkdir(parents=True, exist_ok=True)
    (args.output / "metrics.json").write_text(json.dumps(report, indent=2) + "\n")
    with (args.output / "samples.csv").open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=rows[0])
        w.writeheader()
        w.writerows(rows)
    fig, axes = plt.subplots(1, 2, figsize=(12, 4), constrained_layout=True)
    for ax, key, title in zip(
        axes,
        ["error_noisy_mean", "error_ground"],
        ["Sampling RMSE around noisy mean", "Total RMSE against ideal CASCI"],
    ):
        for method, color in [
            ("uniform", "#16817a"),
            ("regularized_adaptive", "#7044bd"),
        ]:
            selected = [s for s in summaries if s["budget"] == 8192]
            ax.plot(
                [s["case"] for s in selected],
                [s["methods"][method][key] for s in selected],
                "o-",
                label=method,
                color=color,
            )
        ax.set(title=title, ylabel="Energy RMSE (hartree)")
        ax.legend(fontsize=8)
    fig.suptitle(
        "ActiveBudget | 8192 paid shots: variance savings cannot remove systematic bias"
    )
    fig.savefig(args.output / "activenoise.png", dpi=160)
    plt.close(fig)
    print(json.dumps({"references": references, "summaries": summaries}))


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--repeats", type=int, default=400)
    p.add_argument("--seed", type=int, default=2026)
    p.add_argument("--output", type=Path, default=REPO / "results/activenoise")
    args = p.parse_args()
    if not 20 <= args.repeats <= 2000:
        p.error("Repeats must be 20–2000")
    run(args)


if __name__ == "__main__":
    main()

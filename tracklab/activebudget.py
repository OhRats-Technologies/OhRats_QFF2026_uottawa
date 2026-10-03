"""LiH active-space test: paid adaptive shots across more than two groups."""

import argparse
import csv
import json
from pathlib import Path
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from pyscf import gto, scf, mcscf
from qiskit import QuantumCircuit
from qiskit.quantum_info import Statevector
from qiskit_nature.second_q.drivers import PySCFDriver
from qiskit_nature.second_q.mappers import ParityMapper
from qiskit_nature.second_q.transformers import (
    FreezeCoreTransformer,
    ActiveSpaceTransformer,
)
from flybrain.data import REPO
from flybrain.progress import timed_stage


def groups(terms):
    """Deterministic qubit-wise commuting groups; retain within-group covariance."""
    result = []
    for label, coefficient in sorted(terms):
        if label == "II":
            continue
        for group in result:
            if all(
                a == "I" or b == "I" or a == b for a, b in zip(label, group["basis"])
            ):
                group["basis"] = "".join(
                    b if a == "I" else a for a, b in zip(label, group["basis"])
                )
                group["terms"].append((label, float(coefficient.real)))
                break
        else:
            result.append({"basis": label, "terms": [(label, float(coefficient.real))]})
    for group in result:
        group["basis"] = group["basis"].replace("I", "Z")
        group["values"] = np.array(
            [
                sum(
                    c
                    * (-1)
                    ** sum(
                        (bits >> q) & 1 for q, a in enumerate(label[::-1]) if a != "I"
                    )
                    for label, c in group["terms"]
                )
                for bits in range(4)
            ]
        )
    return result


def probabilities(state, basis):
    qc = QuantumCircuit(2)
    for q, a in enumerate(basis[::-1]):
        if a == "Y":
            qc.sdg(q)
            qc.h(q)
        elif a == "X":
            qc.h(q)
    return state.evolve(qc).probabilities()


def allocation(weights, budget, minimum=128):
    if budget < minimum * len(weights):
        raise ValueError("Insufficient production budget")
    weights = np.maximum(np.asarray(weights, dtype=float), 1e-12)
    remaining = budget - minimum * len(weights)
    ideal = remaining * weights / weights.sum()
    counts = np.floor(ideal).astype(int) + minimum
    for i in np.argsort(-(ideal - np.floor(ideal)))[: budget - int(counts.sum())]:
        counts[i] += 1
    return counts


def model():
    atom = "Li 0 0 0; H 0 0 1.6"
    problem = PySCFDriver(atom=atom, basis="sto3g").run()
    problem = FreezeCoreTransformer().transform(problem)
    problem = ActiveSpaceTransformer(2, 2).transform(problem)
    operator = ParityMapper(num_particles=problem.num_particles).map(
        problem.hamiltonian.second_q_op()
    )
    values, vectors = np.linalg.eigh(operator.to_matrix())
    shift = float(sum(problem.hamiltonian.constants.values()))
    mol = gto.M(atom=atom, basis="sto3g", verbose=0)
    hf = scf.RHF(mol).run()
    reference = float(mcscf.CASCI(hf, 2, 2).kernel()[0])
    if abs(values[0] + shift - reference) > 1e-7:
        raise ValueError("Independent CASCI reference disagrees")
    state = Statevector(vectors[:, 0])
    grouped = groups(operator.to_list())
    ps = [probabilities(state, g["basis"]) for g in grouped]
    constant = float(dict(operator.to_list())["II"].real) + shift
    if (
        abs(constant + sum(p @ g["values"] for p, g in zip(ps, grouped)) - reference)
        > 1e-7
    ):
        raise ValueError("Grouped measurements do not reconstruct reference")
    return reference, constant, grouped, ps


def run(args):
    rows = []
    with timed_stage("activebudget", "lih_many_group_paid_pilot") as evidence:
        reference, constant, grouped, ps = model()
        vs = [g["values"] for g in grouped]
        variances = [float(p @ (v * v) - (p @ v) ** 2) for p, v in zip(ps, vs)]
        for budget in [2048, 8192]:
            uniform = allocation(np.ones(len(ps)), budget, minimum=0)
            for repeat in range(args.repeats):
                rng = np.random.default_rng(args.seed + budget + repeat)
                pilot = [rng.multinomial(64, p) for p in ps]
                posterior = [(counts + 0.5) / (64 + 2) for counts in pilot]
                weights = [
                    np.sqrt(max(0, p @ (v * v) - (p @ v) ** 2))
                    for p, v in zip(posterior, vs)
                ]
                adaptive = allocation(weights, budget - 64 * len(ps))
                for method, counts in [
                    ("uniform", uniform),
                    ("regularized_adaptive", adaptive),
                ]:
                    sampled = [rng.multinomial(int(n), p) for n, p in zip(counts, ps)]
                    energy = constant + sum(
                        c @ v / n for c, v, n in zip(sampled, vs, counts)
                    )
                    rows.append(
                        {
                            "budget": budget,
                            "repeat": repeat,
                            "method": method,
                            "error": energy - reference,
                            "paid_shots": budget,
                            "pilot_shots": 0 if method == "uniform" else 64 * len(ps),
                            "production_allocation": ";".join(map(str, counts)),
                        }
                    )
        evidence.update(
            reference="Independent PySCF CASCI(2,2), not full-space FCI",
            groups=len(ps),
            estimates=len(rows),
        )
    summaries = []
    rng = np.random.default_rng(args.seed + 99)
    for budget in [2048, 8192]:
        errors = {
            method: np.array(
                [
                    r["error"]
                    for r in rows
                    if r["budget"] == budget and r["method"] == method
                ]
            )
            for method in ["uniform", "regularized_adaptive"]
        }
        rmse = {m: float(np.sqrt(np.mean(e * e))) for m, e in errors.items()}
        indices = rng.integers(0, args.repeats, (2000, args.repeats))
        ratios = np.sqrt(
            np.mean(errors["regularized_adaptive"][indices] ** 2, axis=1)
            / np.mean(errors["uniform"][indices] ** 2, axis=1)
        )
        summaries.append(
            {
                "budget": budget,
                "rmse": rmse,
                "adaptive_to_uniform_ratio": rmse["regularized_adaptive"]
                / rmse["uniform"],
                "paired_bootstrap_95": np.quantile(ratios, [0.025, 0.975]).tolist(),
            }
        )
    report = {
        "origin": "IDEAL_STATEVECTOR_MULTINOMIAL_SIMULATION",
        "molecule": "LiH at 1.6 angstrom, STO-3G",
        "active_space": "Frozen Li 1s core; two active electrons in two spatial orbitals, fixed RHF orbitals",
        "reference_casci_energy": reference,
        "qubits": 2,
        "groups": [
            {"basis": g["basis"], "terms": g["terms"], "variance": v}
            for g, v in zip(grouped, variances)
        ],
        "repeats": args.repeats,
        "seed": args.seed,
        "summaries": summaries,
        "limitations": "Tiny classically solved active-space approximation, not full-space chemical accuracy or hardware VQE. Grouping is deterministic greedy QWC, not optimized. Adaptive pilots cost 64 shots per group and are excluded from production estimators. Conditional Monte Carlo intervals describe this state and partition only. Known Neyman allocation is not a new algorithm.",
    }
    args.output.mkdir(parents=True, exist_ok=True)
    (args.output / "metrics.json").write_text(json.dumps(report, indent=2) + "\n")
    with (args.output / "samples.csv").open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=rows[0])
        w.writeheader()
        w.writerows(rows)
    fig, axes = plt.subplots(1, 2, figsize=(11, 4), constrained_layout=True)
    axes[0].bar([g["basis"] for g in grouped], variances, color="#16817a")
    axes[0].set(
        title="Unequal ground-state group variances",
        ylabel="Variance (hartree squared)",
    )
    for i, m in enumerate(["uniform", "regularized_adaptive"]):
        axes[1].bar(
            np.arange(2) + (i - 0.5) * 0.35,
            [s["rmse"][m] for s in summaries],
            width=0.35,
            label=m,
        )
    axes[1].set(
        xticks=[0, 1],
        xticklabels=["2048", "8192"],
        xlabel="Total paid shots, including pilots",
        ylabel="Energy RMSE (hartree)",
    )
    axes[1].legend(fontsize=8)
    fig.suptitle("ActiveBudget | LiH CAS(2,2): beyond the two-group identity")
    fig.savefig(args.output / "activebudget.png", dpi=160)
    plt.close(fig)
    print(
        json.dumps({"groups": len(ps), "summaries": summaries, "reference": reference})
    )


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--repeats", type=int, default=400)
    p.add_argument("--seed", type=int, default=2026)
    p.add_argument("--output", type=Path, default=REPO / "results/activebudget")
    args = p.parse_args()
    if not 20 <= args.repeats <= 2000:
        p.error("Repeats must be 20–2000")
    run(args)


if __name__ == "__main__":
    main()

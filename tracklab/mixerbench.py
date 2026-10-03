"""Matched optimizer budgets isolate the paired-versus-Dicke preparation comparison."""

import json, csv
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from qiskit import transpile
from qiskit.quantum_info import Statevector
from scipy.optimize import differential_evolution
from flybrain.data import REPO
from flybrain.progress import timed_stage
from .scheduling import circuit, objective, distribution_metrics


def main():
    rows = []
    costs = np.array([objective(i) for i in range(16)])
    with timed_stage("gridguard", "matched_optimizer_preparation_ablation") as evidence:
        for depth in [1, 2]:
            for seed in [2026, 2027, 2028]:
                for preparation in ["pair", "phase_pair", "dicke"]:
                    result = differential_evolution(
                        lambda p: float(
                            Statevector.from_instruction(
                                circuit(p, "xy", preparation)
                            ).probabilities()
                            @ costs
                        ),
                        [(-6, 6)] * (2 * depth),
                        seed=seed,
                        maxiter=50,
                        popsize=8,
                        polish=False,
                        tol=0,
                        atol=0,
                    )
                    expected_evaluations = (2 * depth) * 8 * 51
                    if result.nfev != expected_evaluations:
                        raise ValueError("Unmatched evaluation count")
                    qc = circuit(result.x, "xy", preparation)
                    compiled = transpile(
                        qc,
                        basis_gates=["rz", "sx", "x", "cx"],
                        optimization_level=1,
                        seed_transpiler=2026,
                    )
                    rows.append(
                        {
                            "depth": depth,
                            "seed": seed,
                            "preparation": preparation,
                            "evaluations": int(result.nfev),
                            "objective": float(result.fun),
                            "parameters": result.x.tolist(),
                            "cx": int(compiled.count_ops().get("cx", 0)),
                            "circuit_depth": compiled.depth(),
                            **distribution_metrics(
                                Statevector.from_instruction(qc).probabilities()
                            ),
                        }
                    )
        evidence.update(
            runs=len(rows),
            identical_optimizer=True,
            identical_bounds=True,
            matched_evaluations_by_depth=True,
            followup_exploratory=True,
        )
    out = REPO / "results/mixerbench"
    out.mkdir(parents=True, exist_ok=True)
    (out / "metrics.json").write_text(
        json.dumps(
            {
                "evidence": "ideal_four_qubit_matched_optimizer_followup",
                "rows": rows,
                "optimizer": "Differential evolution, maxiter50 popsize8 tol0 atol0 polishFalse bounds[-6,6]",
                "interpretation": "The original architecture search used different optimization methods and bounds for the two starts. This follow-up removes those confounders for this one toy instance; three seeds do not establish general superiority.",
            },
            indent=2,
        )
        + "\n"
    )
    with (out / "runs.csv").open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)
    fig, axes = plt.subplots(1, 2, figsize=(12, 4.5), constrained_layout=True)
    for preparation, color in [
        ("pair", "#16817a"),
        ("phase_pair", "#b76636"),
        ("dicke", "#784ec2"),
    ]:
        for depth in [1, 2]:
            group = [
                r
                for r in rows
                if r["preparation"] == preparation and r["depth"] == depth
            ]
            x = depth + {"pair": -0.13, "phase_pair": 0, "dicke": 0.13}[preparation]
            axes[0].scatter(
                [x] * 3,
                [r["optimal_probability"] for r in group],
                color=color,
                label=preparation if depth == 1 else None,
            )
            axes[1].scatter(
                [r["cx"] for r in group],
                [r["optimal_probability"] for r in group],
                color=color,
            )
    axes[0].set(
        xticks=[1, 2],
        xlabel="QAOA layers",
        ylabel="Optimal probability",
        ylim=(0, 1.05),
        title="Matched optimizer and evaluation budget",
    )
    axes[0].legend()
    axes[1].set(
        xlabel="CX gates after local compilation",
        ylabel="Optimal probability",
        ylim=(0, 1.05),
        title="Preparation benefit versus circuit cost",
    )
    fig.suptitle("GridGuard | Controlled preparation ablation · three optimizer seeds")
    fig.savefig(out / "mixerbench.png", dpi=160)
    plt.close(fig)
    print(
        json.dumps(
            {
                "runs": len(rows),
                "results": [
                    {k: v for k, v in r.items() if k != "parameters"} for r in rows
                ],
            }
        )
    )


if __name__ == "__main__":
    main()

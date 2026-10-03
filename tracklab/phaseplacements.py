"""PhaseGuard sensitivity to all six placements of heavy jobs; not a broad benchmark."""

import itertools, json
import numpy as np
from qiskit.quantum_info import Statevector
from scipy.optimize import differential_evolution
from flybrain.data import REPO
from flybrain.progress import timed_stage
from .scheduling import circuit


def generalized_circuit(params, weights, prep):
    # Same paired preparation; update only the problem's Ising weights.
    qc = circuit([], preparation=prep)
    gamma, beta = params
    for i, w in enumerate(weights):
        qc.rz(2 * gamma * 0.23 * w, i)
    for i in range(4):
        for j in range(i + 1, 4):
            qc.rzz(2 * gamma * 0.09 * weights[i] * weights[j] / 2, i, j)
    for i, j in [(0, 1), (2, 3), (1, 2), (3, 0)]:
        qc.rxx(beta, i, j)
        qc.ryy(beta, i, j)
    return qc


def main():
    rows = []
    with timed_stage("phaseguard", "all_heavy_job_placements") as evidence:
        for heavy in itertools.combinations(range(4), 2):
            weights = np.ones(4)
            weights[list(heavy)] = 2
            costs = []
            valid = []
            for bits in range(16):
                late = sum(weights[i] for i in range(4) if (bits >> i) & 1)
                costs.append(
                    3.29 - late + 0.09 * late**2 + 4 * (bits.bit_count() - 2) ** 2
                )
                valid.append(bits.bit_count() == 2)
            costs = np.array(costs)
            optimal = sum(1 << i for i in heavy)
            for seed in [2026, 2027, 2028]:
                for prep in ["pair", "phase_pair"]:
                    result = differential_evolution(
                        lambda p: float(
                            Statevector.from_instruction(
                                generalized_circuit(p, weights, prep)
                            ).probabilities()
                            @ costs
                        ),
                        [(-6, 6)] * 2,
                        seed=seed,
                        maxiter=50,
                        popsize=8,
                        polish=False,
                        tol=0,
                        atol=0,
                    )
                    p = Statevector.from_instruction(
                        generalized_circuit(result.x, weights, prep)
                    ).probabilities()
                    rows.append(
                        {
                            "heavy_positions": list(heavy),
                            "weights": weights.tolist(),
                            "preparation": prep,
                            "seed": seed,
                            "evaluations": int(result.nfev),
                            "objective": float(result.fun),
                            "optimal_bits": format(optimal, "04b"),
                            "optimal_probability": float(p[optimal]),
                            "feasible_probability": float(p[np.array(valid)].sum()),
                            "parameters": result.x.tolist(),
                        }
                    )
        evidence.update(
            placements=6,
            runs=len(rows),
            all_placements_reported=True,
            matched_evaluation_budget=True,
            one_small_problem_family=True,
        )
    out = REPO / "results/phaseguard"
    out.mkdir(parents=True, exist_ok=True)
    (out / "placements.json").write_text(
        json.dumps(
            {
                "evidence": "ideal_permuted_four_job_sensitivity",
                "rows": rows,
                "limitations": "Six weight permutations of the same easy instance, not independent real scheduling workloads. Follow-up selected after observing the original phase benefit; no general superiority claim.",
            },
            indent=2,
        )
        + "\n"
    )
    print(
        json.dumps(
            {
                str(heavy): {
                    prep: float(
                        np.mean(
                            [
                                r["optimal_probability"]
                                for r in rows
                                if r["heavy_positions"] == list(heavy)
                                and r["preparation"] == prep
                            ]
                        )
                    )
                    for prep in ["pair", "phase_pair"]
                }
                for heavy in itertools.combinations(range(4), 2)
            }
        )
    )


if __name__ == "__main__":
    main()

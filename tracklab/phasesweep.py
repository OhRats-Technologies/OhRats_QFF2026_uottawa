"""A causal phase sweep: hold every QAOA parameter fixed while changing only the warm-start phases."""

import json
import numpy as np
from qiskit.quantum_info import Statevector
from flybrain.data import REPO
from flybrain.progress import timed_stage
from .scheduling import circuit, distribution_metrics


def phase_circuit(params, phi):
    prefix = circuit([], preparation="pair")
    qc = prefix.copy()
    qc.rz(float(phi), 1)
    qc.rz(float(phi), 3)
    full = circuit(params, preparation="pair")
    for instruction in full.data[len(prefix.data) :]:
        indices = [full.find_bit(q).index for q in instruction.qubits]
        qc.append(instruction.operation, indices)
    return qc


def main():
    search = json.loads((REPO / "results/mixerbench/metrics.json").read_text())["rows"]
    best = next(
        r
        for r in search
        if r["preparation"] == "phase_pair" and r["depth"] == 1 and r["seed"] == 2026
    )
    rows = []
    with timed_stage("phaseguard", "fixed_parameter_phase_sweep") as evidence:
        for phi in np.linspace(0, np.pi, 73):
            initial = Statevector.from_instruction(phase_circuit([], phi))
            final = Statevector.from_instruction(phase_circuit(best["parameters"], phi))
            rows.append(
                {
                    "phase_degrees": float(phi * 180 / np.pi),
                    "initial_probabilities": initial.probabilities().tolist(),
                    "initial_relative_phases": np.angle(
                        initial.data / initial.data[5]
                    ).tolist(),
                    "final_probabilities": final.probabilities().tolist(),
                    **distribution_metrics(final.probabilities()),
                }
            )
        for row in rows:
            np.testing.assert_allclose(
                row["initial_probabilities"],
                rows[0]["initial_probabilities"],
                atol=1e-12,
            )
        evidence.update(
            points=len(rows),
            qaoa_parameters_fixed=True,
            initial_probabilities_identical=True,
        )
    out = REPO / "results/phaseguard"
    out.mkdir(parents=True, exist_ok=True)
    (out / "phase_sweep.json").write_text(
        json.dumps(
            {
                "evidence": "ideal_fixed_parameter_phase_sweep",
                "qaoa_parameters": best["parameters"],
                "rows": rows,
                "limitations": "Fixed parameters were selected for the corrected 90-degree preparation on the original toy instance. This sweep isolates phase effects after that exploratory selection; it is not an optimizer benchmark.",
            },
            indent=2,
        )
        + "\n"
    )
    print(
        json.dumps(
            {
                "phi0_optimal": rows[0]["optimal_probability"],
                "phi90_optimal": rows[36]["optimal_probability"],
                "phi180_optimal": rows[-1]["optimal_probability"],
            }
        )
    )


if __name__ == "__main__":
    main()

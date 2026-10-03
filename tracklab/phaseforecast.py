"""Local calibration-model comparison for PhaseGuard; no IBM job submitted."""

import json
from datetime import datetime, timezone
import numpy as np
from qiskit import qpy
from qiskit_aer import AerSimulator
from qiskit.transpiler import generate_preset_pass_manager
from flybrain.data import REPO
from flybrain.hardware import service
from flybrain.progress import timed_stage
from .scheduling import circuit, distribution_metrics


def main():
    rows = json.loads((REPO / "results/mixerbench/metrics.json").read_text())["rows"]
    selected = [
        next(
            r
            for r in rows
            if r["preparation"] == prep and r["depth"] == 1 and r["seed"] == 2026
        )
        for prep in ["pair", "phase_pair", "dicke"]
    ]
    backend = service().backend("ibm_quebec")
    with (REPO / "results/scheduling-hardware/circuits.qpy").open("rb") as stream:
        prior = qpy.load(stream)
    layout = prior[2].layout.initial_index_layout()[:4]
    manager = generate_preset_pass_manager(
        backend=backend,
        optimization_level=3,
        seed_transpiler=2026,
        initial_layout=layout,
    )
    circuits = []
    for r in selected:
        qc = circuit(r["parameters"], "xy", r["preparation"])
        qc.measure_all()
        circuits.append(qc)
    compiled = manager.run(circuits)
    sim = AerSimulator.from_backend(
        backend,
        method="density_matrix",
        enable_truncation=True,
        max_parallel_threads=2,
        max_memory_mb=1024,
    )
    results = []
    with timed_stage("phaseguard", "local_calibration_forecast") as evidence:
        for repeat in range(12):
            counts = (
                sim.run(compiled, shots=2048, seed_simulator=2026 + repeat)
                .result()
                .get_counts()
            )
            for r, qc, c in zip(selected, compiled, counts):
                p = np.array([c.get(format(i, "04b"), 0) / 2048 for i in range(16)])
                results.append(
                    {
                        "preparation": r["preparation"],
                        "repeat": repeat,
                        "two_qubit_gates": int(
                            qc.count_ops().get("cz", 0) + qc.count_ops().get("cx", 0)
                        ),
                        "depth": qc.depth(),
                        **distribution_metrics(p),
                    }
                )
        evidence.update(
            runs=len(results), hardware_execution=False, common_initial_layout=True
        )
    out = REPO / "results/phaseguard"
    out.mkdir(parents=True, exist_ok=True)
    report = {
        "evidence": "LOCAL_BACKEND_CALIBRATION_MODEL_NOT_HARDWARE",
        "created_utc": datetime.now(timezone.utc).isoformat(),
        "backend": backend.name,
        "physical_initial_layout": layout,
        "shots_per_circuit": 2048,
        "repeats": 12,
        "results": results,
        "limitations": "Same initial physical layout and compilation policy, but routing may introduce different active qubits. Markovian calibration noise is only a forecast; no IBM counts collected for corrected phases.",
    }
    (out / "calibration_forecast.json").write_text(json.dumps(report, indent=2) + "\n")
    print(
        json.dumps(
            {
                "local_forecast": {
                    prep: {
                        "optimal_mean": float(
                            np.mean(
                                [
                                    r["optimal_probability"]
                                    for r in results
                                    if r["preparation"] == prep
                                ]
                            )
                        ),
                        "two_qubit_gates": next(
                            r["two_qubit_gates"]
                            for r in results
                            if r["preparation"] == prep
                        ),
                    }
                    for prep in ["pair", "phase_pair", "dicke"]
                },
                "hardware_result": False,
            }
        )
    )


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        raise SystemExit(
            f"Phase forecast failed ({type(e).__name__}); no credentials printed."
        )

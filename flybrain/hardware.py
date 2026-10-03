"""Small, explicit, idempotent IBM hardware runs; credentials stay in environment."""

import argparse
from datetime import datetime, timezone
import json
import logging
import os
from pathlib import Path

import numpy as np
from qiskit import qpy
from qiskit.quantum_info import Statevector
from qiskit.transpiler import generate_preset_pass_manager
from qiskit_ibm_runtime import QiskitRuntimeService, SamplerV2

from .data import REPO, load_graph
from .walks import circuit_at, laplacian, undirected

DEFAULT_OUTPUT = REPO / "results/hardware"


def check_sprint_budget():
    # Count durable intents too: an interrupted submission may already be queued.
    folders = {
        p.parent
        for pattern in ["**/submitted.json", "**/submission_intent.json"]
        for p in (REPO / "results").glob(pattern)
    }
    if len(folders) >= 3:
        raise ValueError("Conservative sprint cap of three IBM jobs reached")


def service():
    token = os.environ.get("PINQ_API_TOKEN")
    if not token:
        raise ValueError("Set PINQ_API_TOKEN; run with uv run --env-file .env")
    logging.getLogger("qiskit_ibm_runtime").setLevel(logging.ERROR)
    return QiskitRuntimeService(
        channel="ibm_quantum_platform",
        token=token,
        instance=os.environ.get("IBM_QUANTUM_INSTANCE", "auto"),
    )


def prepare_cases():
    nodes, adjacency, provenance = load_graph()
    weights = undirected(adjacency)
    scale = weights.sum(axis=1).max()
    generator = laplacian(weights, scale)
    lesion = max(range(1, len(nodes)), key=lambda i: (weights[i].sum(), -i))
    damaged = weights.copy()
    damaged[lesion, :] = damaged[:, lesion] = 0
    cases = []
    for name, time, matrix in [
        ("zero_time_control", 0.0, generator),
        ("intact_t4", 4.0, generator),
        ("intact_t8", 8.0, generator),
        ("lesion_t8", 8.0, laplacian(damaged, scale)),
    ]:
        circuit = circuit_at(matrix, 0, time)
        expected = Statevector.from_instruction(circuit).probabilities().tolist()
        circuit.measure_all()
        cases.append(
            (
                circuit,
                {
                    "name": name,
                    "time": time,
                    "source": nodes[0],
                    "lesion": nodes[lesion] if name.startswith("lesion") else None,
                    "expected": expected,
                },
            )
        )
    return cases, nodes, provenance


def submit(args):
    manifest_path = args.output / "submitted.json"
    if manifest_path.exists():
        prior = json.loads(manifest_path.read_text())
        print(
            f"Already submitted job {prior['job_id']}; use collect. No new job submitted."
        )
        return
    if (args.output / "submission_intent.json").exists():
        raise ValueError(
            "Prior submission intent exists without a job ID. Check IBM workload history before retrying."
        )
    check_sprint_budget()
    runtime = service()
    backends = runtime.backends(simulator=False, operational=True, min_num_qubits=3)
    if not backends:
        raise ValueError("No operational backend available")
    backend = min(backends, key=lambda b: (b.status().pending_jobs, b.name))
    if "quebec" not in backend.name and not os.environ.get("IBM_QUANTUM_INSTANCE"):
        raise ValueError(
            "Unexpected allocation; set the organizer-provided IBM_QUANTUM_INSTANCE explicitly"
        )
    cases, nodes, provenance = prepare_cases()
    manager = generate_preset_pass_manager(
        backend=backend, optimization_level=3, seed_transpiler=2026
    )
    compiled = manager.run([case[0] for case in cases])
    summaries = []
    for circuit, (_, case) in zip(compiled, cases):
        summaries.append(
            {**case, "depth": circuit.depth(), "operations": dict(circuit.count_ops())}
        )
    args.output.mkdir(parents=True, exist_ok=True)
    with (args.output / "circuits.qpy").open("wb") as stream:
        qpy.dump(compiled, stream)
    intent = {
        "created_utc": datetime.now(timezone.utc).isoformat(),
        "backend": backend.name,
        "shots_per_circuit": args.shots,
        "max_execution_seconds": 300,
        "nodes": nodes,
        "source_commit": provenance["source_commit"],
        "cases": summaries,
    }
    # A durable intent prevents accidental duplicate submissions after a crash.
    (args.output / "submission_intent.json").write_text(
        json.dumps(intent, indent=2) + "\n"
    )
    sampler = SamplerV2(mode=backend, options={"max_execution_time": 300})
    job = sampler.run(compiled, shots=args.shots)
    manifest = {
        **intent,
        "job_id": job.job_id(),
        "status": str(job.status()),
        "evidence": "hardware_submission",
    }
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n")
    print(
        json.dumps(
            {
                "job_id": manifest["job_id"],
                "backend": backend.name,
                "circuits": len(compiled),
                "shots_per_circuit": args.shots,
                "status": manifest["status"],
            }
        )
    )


def collect(args):
    manifest = json.loads((args.output / "submitted.json").read_text())
    if (args.output / "collected.json").exists():
        print("Hardware results already collected; no API call needed.")
        return
    job = service().job(manifest["job_id"])
    status = str(job.status())
    print(f"Hardware job status: {status}")
    (args.output / "status.json").write_text(
        json.dumps(
            {"status": status, "checked_utc": datetime.now(timezone.utc).isoformat()},
            indent=2,
        )
        + "\n"
    )
    if status.upper() != "DONE":
        return
    result = job.result()
    if len(result) != len(manifest["cases"]):
        raise ValueError("Hardware publication count differs from submitted cases")
    cases = []
    for reference, publication in zip(manifest["cases"], result):
        counts = publication.data.meas.get_counts()
        actual_shots = sum(counts.values())
        if actual_shots <= 0:
            raise ValueError("Empty hardware counts")
        observed = np.zeros(len(manifest["nodes"]))
        for bits, count in counts.items():
            observed[int(bits, 2)] = count / actual_shots
        expected = np.array(reference["expected"])
        cases.append(
            {
                **reference,
                "counts": counts,
                "actual_shots": actual_shots,
                "observed": observed.tolist(),
                "total_variation_from_ideal": float(
                    np.abs(observed - expected).sum() / 2
                ),
            }
        )
    collected = {
        "job_id": manifest["job_id"],
        "backend": manifest["backend"],
        "evidence": "real_ibm_hardware",
        "collected_utc": datetime.now(timezone.utc).isoformat(),
        "nodes": manifest["nodes"],
        "cases": cases,
    }
    (args.output / "collected.json").write_text(json.dumps(collected, indent=2) + "\n")
    print(
        json.dumps(
            {
                "backend": collected["backend"],
                "results": [
                    {
                        "case": c["name"],
                        "shots": c["actual_shots"],
                        "tv": c["total_variation_from_ideal"],
                    }
                    for c in cases
                ],
            }
        )
    )


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=["submit", "collect"])
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--shots", type=int, default=1024)
    args = parser.parse_args()
    if not 128 <= args.shots <= 4096:
        parser.error("Hardware shots must be 128–4096 per circuit")
    try:
        {"submit": submit, "collect": collect}[args.command](args)
    except Exception as error:
        # Third-party HTTP exception messages can contain authentication data.
        parser.exit(
            1,
            f"Hardware action failed ({type(error).__name__}). No credentials printed. Check local status files and IBM workload history.\n",
        )


if __name__ == "__main__":
    main()

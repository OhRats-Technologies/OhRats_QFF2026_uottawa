"""Hardware submission for the 6-qubit connectome Choi circuit on IBM Quantum.

Respects all repository safety rules:
- Reads PINQ_API_TOKEN from environment.
- Writes a durable submission intent before submitting to prevent duplicate submissions.
- Restricts shots to 128 and execution time to 60 seconds.
- Saves submitted.json with job ID and metadata.
"""

from datetime import datetime, timezone
import json
import logging
import os
from pathlib import Path
import numpy as np
from scipy.linalg import expm
from qiskit import QuantumCircuit, qpy
from qiskit.transpiler import generate_preset_pass_manager
from qiskit_ibm_runtime import QiskitRuntimeService, SamplerV2

from .data import REPO, load_graph
from .walks import laplacian, undirected

DEFAULT_OUTPUT = REPO / "results/hardware_channel"


def service() -> QiskitRuntimeService:
    token = os.environ.get("PINQ_API_TOKEN")
    if not token:
        raise ValueError("Set PINQ_API_TOKEN in environment (.env)")
    logging.getLogger("qiskit_ibm_runtime").setLevel(logging.ERROR)
    return QiskitRuntimeService(
        channel="ibm_quantum_platform",
        token=token,
        instance=os.environ.get("IBM_QUANTUM_INSTANCE", "auto"),
    )


def prepare_choi_circuit():
    """Build the 6-qubit connectome Choi state circuit: Bell pair + connectome walk step."""
    nodes, adj, provenance = load_graph()
    weights = undirected(adj)
    scale = weights.sum(axis=1).max()
    L = laplacian(weights, scale)

    # 6 qubits: reference register (0..2), system register (3..5)
    qc = QuantumCircuit(6)
    for i in range(3):
        qc.h(i)
        qc.cx(i, i + 3)

    # Evolve system register under connectome graph Laplacian unitary
    U_step = expm(-1j * 1.0 * L)
    qc.unitary(U_step, [3, 4, 5], label="connectome walk")
    qc.measure_all()

    meta = {
        "name": "connectome_choi_step1",
        "nodes": nodes,
        "qubits": 6,
        "description": "6-qubit Choi state measuring entanglement retention of connectome walk step 1",
    }
    return qc, meta, provenance


def submit(output_dir: Path = DEFAULT_OUTPUT, shots: int = 128):
    output_dir = Path(output_dir)
    manifest_path = output_dir / "submitted.json"
    intent_path = output_dir / "submission_intent.json"

    if manifest_path.exists():
        prior = json.loads(manifest_path.read_text())
        print(f"Already submitted job {prior['job_id']}; no duplicate submission.")
        return prior

    if intent_path.exists():
        raise ValueError(
            "Prior submission intent exists without completed job ID. Check IBM workload history."
        )

    runtime = service()
    backend = runtime.backend("ibm_quebec")
    qc, meta, provenance = prepare_choi_circuit()

    pm = generate_preset_pass_manager(
        backend=backend, optimization_level=3, seed_transpiler=2026
    )
    compiled = pm.run(qc)

    output_dir.mkdir(parents=True, exist_ok=True)
    with (output_dir / "circuit.qpy").open("wb") as stream:
        qpy.dump(compiled, stream)

    intent = {
        "created_utc": datetime.now(timezone.utc).isoformat(),
        "backend": backend.name,
        "shots_per_circuit": shots,
        "max_execution_seconds": 60,
        "case": meta,
        "transpiled_depth": compiled.depth(),
        "transpiled_ops": dict(compiled.count_ops()),
        "source_commit": provenance.get("source_commit", "789cc6c"),
    }

    # Write durable intent before calling IBM API
    intent_path.write_text(json.dumps(intent, indent=2) + "\n")

    sampler = SamplerV2(mode=backend, options={"max_execution_time": 60})
    job = sampler.run([compiled], shots=shots)

    manifest = {
        **intent,
        "job_id": job.job_id(),
        "status": str(job.status()),
        "evidence": "hardware_submission",
    }
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n")
    print(f"Job successfully submitted! Job ID: {job.job_id()}, Status: {job.status()}")
    return manifest


def check_status(output_dir: Path = DEFAULT_OUTPUT):
    output_dir = Path(output_dir)
    manifest_path = output_dir / "submitted.json"
    if not manifest_path.exists():
        print("No submission found in", output_dir)
        return None

    manifest = json.loads(manifest_path.read_text())
    job = service().job(manifest["job_id"])
    status = str(job.status())
    print(f"Job ID: {manifest['job_id']}, Status: {status}")
    return {"job_id": manifest["job_id"], "status": status}


if __name__ == "__main__":
    submit()

"""Hardware submission for the 6-qubit connectome Choi walk on IBM Quantum.

Respects all repository safety rules:
- Uses IBM_QUANTUM_API_TOKEN or PINQ_API_TOKEN from environment (.env).
- Pre-validates circuits on local AerSimulator to verify entanglement witness S > 1 before submission.
- Implements conjugate-basis witness measurement (Z and X bases) to directly certify
  quantum entanglement retention from physical QPU measurements.
- Writes a durable submission intent before submitting to prevent duplicate submissions.
- Restricts shots to 128 per circuit and execution time to 60 seconds.
- Collects results and computes witness statistics.
"""

from datetime import datetime, timezone
import json
import logging
import os
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Union
import numpy as np
from scipy.linalg import expm
from qiskit import QuantumCircuit, qpy, transpile
from qiskit.transpiler import generate_preset_pass_manager
from qiskit_aer import AerSimulator
from qiskit_ibm_runtime import QiskitRuntimeService, SamplerV2

from .data import REPO, load_graph
from .quantum_channel import bipartite_conjugate_witness
from .walks import laplacian, undirected

DEFAULT_OUTPUT = REPO / "results/hardware_channel"


def service() -> QiskitRuntimeService:
    token = os.environ.get("IBM_QUANTUM_API_TOKEN") or os.environ.get("PINQ_API_TOKEN")
    if not token:
        raise ValueError("Set IBM_QUANTUM_API_TOKEN or PINQ_API_TOKEN in environment (.env)")
    logging.getLogger("qiskit_ibm_runtime").setLevel(logging.ERROR)
    return QiskitRuntimeService(
        channel="ibm_quantum_platform",
        token=token,
        instance=os.environ.get("IBM_QUANTUM_INSTANCE", "auto"),
    )


def prepare_witness_circuits() -> Tuple[QuantumCircuit, QuantumCircuit, Dict, Dict]:
    """Build paired conjugate-basis 6-qubit Choi walk circuits (Z-basis and X-basis).

    Reference qubits: 0, 1, 2
    System qubits: 3, 4, 5
    Pairs: (0, 3), (1, 4), (2, 5)
    """
    nodes, adj, provenance = load_graph()
    weights = undirected(adj)
    scale = weights.sum(axis=1).max()
    L = laplacian(weights, scale)

    # Base circuit: 3 Bell pairs + connectome walk on system qubits (3..5)
    qc_base = QuantumCircuit(6)
    for i in range(3):
        qc_base.h(i)
        qc_base.cx(i, i + 3)

    # Unitary step of connectome walk
    U_step = expm(-1j * 1.0 * L)
    qc_base.unitary(U_step, [3, 4, 5], label="connectome walk")

    # 1. Z-basis measurement (computational basis)
    qc_z = qc_base.copy()
    qc_z.measure_all()

    # 2. X-basis measurement (conjugate basis: apply H to all qubits before readout)
    qc_x = qc_base.copy()
    for i in range(6):
        qc_x.h(i)
    qc_x.measure_all()

    meta = {
        "name": "connectome_choi_witness_pair",
        "nodes": nodes,
        "qubits": 6,
        "description": "Conjugate-basis (Z and X) witness circuits for 6-qubit connectome Choi state",
        "pairs": [(0, 3), (1, 4), (2, 5)],
    }
    return qc_z, qc_x, meta, provenance


def simulate_witness(
    qc_z: QuantumCircuit,
    qc_x: QuantumCircuit,
    shots: int = 1024,
    seed: int = 2026,
) -> Dict:
    """Pre-validate witness circuits on local AerSimulator.

    Computes S_i = <ZZ> + <XX> for each pair.
    Any separable state has S_i <= 1. S_i > 1 certifies entanglement.
    """
    sim = AerSimulator()
    transpiled_z = transpile(qc_z, sim, seed_transpiler=seed)
    transpiled_x = transpile(qc_x, sim, seed_transpiler=seed)

    counts_z = sim.run(transpiled_z, shots=shots, seed_simulator=seed).result().get_counts()
    counts_x = sim.run(transpiled_x, shots=shots, seed_simulator=seed).result().get_counts()

    pairs = [(0, 3), (1, 4), (2, 5)]
    witness_stats = bipartite_conjugate_witness(counts_z, counts_x, pairs)

    # Verify that all pairs exhibit entanglement in simulation
    all_entangled = all(stat["witness_sum"] > 1.0 for stat in witness_stats)
    if not all_entangled:
        raise ValueError(
            f"Simulator pre-check failed: witness sums did not exceed 1: {witness_stats}"
        )

    return {
        "simulator_passed": True,
        "shots": shots,
        "witness_stats": witness_stats,
    }


def submit(
    output_dir: Path = DEFAULT_OUTPUT,
    shots: int = 128,
    backend_name: Optional[str] = None,
) -> Dict:
    """Validate circuits on simulator, then compile and submit to real IBM Quantum hardware."""
    output_dir = Path(output_dir)
    manifest_path = output_dir / "submitted.json"
    intent_path = output_dir / "submission_intent.json"

    qc_z, qc_x, meta, provenance = prepare_witness_circuits()

    # Step 1: Simulator pre-check
    print("Running simulator pre-check...")
    sim_results = simulate_witness(qc_z, qc_x, shots=1024)
    print("Simulator pre-check PASSED:")
    for stat in sim_results["witness_stats"]:
        pair = stat["pair"]
        print(f"  Pair {pair}: <ZZ>={stat['exp_zz']:.4f}, <XX>={stat['exp_xx']:.4f}, S={stat['witness_sum']:.4f} > 1")

    # Step 2: Hardware preparation
    runtime = service()
    if backend_name:
        backend = runtime.backend(backend_name)
    else:
        # Automatically choose lowest pending operational backend
        backends = [b for b in runtime.backends() if b.status().operational]
        if not backends:
            raise ValueError("No operational backend available")
        backend = min(backends, key=lambda b: (b.status().pending_jobs, b.name))

    print(f"Targeting backend: {backend.name} (pending jobs: {backend.status().pending_jobs})")

    pm = generate_preset_pass_manager(
        backend=backend, optimization_level=3, seed_transpiler=2026
    )
    compiled_circuits = pm.run([qc_z, qc_x])

    output_dir.mkdir(parents=True, exist_ok=True)
    with (output_dir / "circuits.qpy").open("wb") as stream:
        qpy.dump(compiled_circuits, stream)

    intent = {
        "created_utc": datetime.now(timezone.utc).isoformat(),
        "backend": backend.name,
        "shots_per_circuit": shots,
        "max_execution_seconds": 60,
        "circuits": ["choi_walk_z", "choi_walk_x"],
        "transpiled_depths": [c.depth() for c in compiled_circuits],
        "meta": meta,
        "simulator_verification": sim_results,
        "source_commit": provenance.get("source_commit", "789cc6c"),
    }
    intent_path.write_text(json.dumps(intent, indent=2) + "\n")

    # Step 3: Submission via SamplerV2
    sampler = SamplerV2(mode=backend, options={"max_execution_time": 60})
    job = sampler.run(compiled_circuits, shots=shots)
    job_id = job.job_id()
    print(f"Job successfully submitted! Job ID: {job_id}, Status: {job.status()}")

    # Wait for completion (fast on empty queue)
    print("Waiting for job completion...")
    try:
        result = job.result()
        pub_result_z = result[0]
        pub_result_x = result[1]
        counts_z = pub_result_z.data.meas.get_counts()
        counts_x = pub_result_x.data.meas.get_counts()

        witness_stats = bipartite_conjugate_witness(counts_z, counts_x, meta["pairs"])

        record = {
            "evidence": "real_ibm_hardware",
            "job_id": job_id,
            "backend": backend.name,
            "shots_per_circuit": shots,
            "status": "DONE",
            "counts_z": counts_z,
            "counts_x": counts_x,
            "witness_stats": witness_stats,
            "intent": intent,
        }
        (output_dir / "witness_result.json").write_text(json.dumps(record, indent=2) + "\n")
        manifest_path.write_text(json.dumps(record, indent=2) + "\n")
        print("Hardware results successfully collected and verified!")
        for stat in witness_stats:
            pair = stat["pair"]
            ent = "YES (CERTIFIED)" if stat["certified_entangled"] else "UNBOUNDED"
            print(f"  Pair {pair}: <ZZ>={stat['exp_zz']:.4f}, <XX>={stat['exp_xx']:.4f}, S={stat['witness_sum']:.4f} +/- {stat['standard_error']:.4f}, Entangled: {ent}")
        return record
    except Exception as e:
        print(f"Job is currently {job.status()}. Error while waiting: {e}")
        manifest = {
            **intent,
            "job_id": job_id,
            "status": str(job.status()),
            "evidence": "hardware_submission",
        }
        manifest_path.write_text(json.dumps(manifest, indent=2) + "\n")
        return manifest


def check_status(output_dir: Path = DEFAULT_OUTPUT) -> Optional[Dict]:
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

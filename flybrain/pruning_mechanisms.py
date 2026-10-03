"""Exploratory row/edge interventions: classical bottlenecks versus EB lifetime."""

import hashlib
import itertools
import json
from pathlib import Path

import numpy as np
from qiskit import QuantumCircuit
from qiskit_aer import AerSimulator

from .channel_certificates import analytic_choi, exact_certificate, phase_certificate
from .data import load_graph
from .quantum_channel import ConnectomeQuantumChannel


def interventions(weights, nodes, threshold=1000):
    """Enumerate all one/two-row restorations and explicit witness-edge controls."""
    W = np.asarray(weights, dtype=np.int64)
    pruned = np.where(W >= threshold, W, 0)
    if np.any(pruned.sum(1) == 0):
        raise ValueError("Pruning creates empty rows; no implicit repair")
    held = pruned.copy()
    held[np.diag_indices(len(W))] += (W - pruned).sum(1)
    yield "intact", W.copy(), {"kind": "baseline"}
    yield "pruned", pruned.copy(), {"kind": "baseline"}
    yield "removed_mass_held", held, {"kind": "self_loop_control"}
    for size in [1, 2]:
        for rows in itertools.combinations(range(len(W)), size):
            restored = pruned.copy()
            restored[list(rows)] = W[list(rows)]
            yield (
                "rows:" + "+".join(nodes[i] for i in rows),
                restored,
                {"kind": "row_restoration", "rows": list(rows)},
            )
    # Selected post-hoc from the pruned channel's surviving step-seven NPT pair.
    a, b = nodes.index("Pm4_R"), nodes.index("T4a_R")
    edges = [(a, b), (b, a)]
    for subset in [(edges[0],), (edges[1],), tuple(edges)]:
        restored = pruned.copy()
        for i, j in subset:
            restored[i, j] = W[i, j]
        yield (
            "edges:" + "+".join(f"{nodes[i]}>{nodes[j]}" for i, j in subset),
            restored,
            {"kind": "post_hoc_edge_restoration", "edges": [list(e) for e in subset]},
        )


def certify(weights, nodes):
    P = weights / weights.sum(1, keepdims=True)
    records = []
    proof = None
    for r in range(1, 21):
        _, B, c = analytic_choi(P, 0.6, r)
        pairs = [
            [nodes[i], nodes[j]]
            for i in range(len(P))
            for j in range(i + 1, len(P))
            if B[i, j] * B[j, i] - c * c < -1e-12
        ]
        records.append(
            {
                "step": r,
                "population_dobrushin": float(
                    np.max(np.abs(B[:, None, :] - B[None, :, :]).sum(2)) / 2
                ),
                "npt_pairs": pairs,
            }
        )
        certificate = phase_certificate(B, c)
        if certificate is not None and r >= 2:
            proof = exact_certificate(weights, "0.6", r, certificate["v"])
            if proof["exact_eb_index"] != r:
                raise ValueError("Upper certificate lacks matching exact lower bound")
            break
    if proof is None:
        raise ValueError("No exact matching certificate within registered step limit")
    t = nodes.index("T4a_R")
    eigenvalues = np.linalg.eigvals(P)
    moduli = sorted(np.abs(eigenvalues), reverse=True)
    return {
        "transition_matrix": P.tolist(),
        "subdominant_modulus": float(moduli[1]),
        "t4a_escape": float(1 - P[t, t]),
        "exact_eb_index": proof["exact_eb_index"],
        "steps": records,
        "certificate": proof,
    }


def simulate(P, step):
    """Apply the actual Kraus channel to half of three Bell pairs locally."""
    channel = ConnectomeQuantumChannel(np.asarray(P), 0.6)
    qc = QuantumCircuit(6)
    for i in range(3):
        qc.h(i)
        qc.cx(i, i + 3)
    for _ in range(step):
        qc.append(channel.qiskit_channel.to_instruction(), [3, 4, 5])
    qc.save_density_matrix()
    result = (
        AerSimulator(method="density_matrix", max_parallel_threads=1)
        .run(qc, shots=1)
        .result()
    )
    rho = np.asarray(result.data(0)["density_matrix"])
    # Qiskit's high-order system register precedes its low-order reference register.
    ordered = rho.reshape(8, 8, 8, 8).transpose(1, 0, 3, 2).reshape(64, 64)
    expected, _, _ = analytic_choi(P, 0.6, step)
    pt = ordered.reshape(8, 8, 8, 8).transpose(0, 3, 2, 1).reshape(64, 64)
    error = float(np.max(np.abs(ordered - expected)))
    if error > 1e-10:
        raise ValueError("Kraus circuit disagrees with analytic Choi matrix")
    return {
        "step": step,
        "max_choi_error": error,
        "trace_real": float(np.trace(ordered).real),
        "partial_transpose_minimum": float(np.linalg.eigvalsh(pt).min()),
        "scope": "Local density-matrix simulation; no hardware submission",
    }


def main():
    nodes, W, provenance = load_graph()
    experiments = []
    for name, weights, intervention in interventions(W, nodes):
        result = certify(weights, nodes)
        result.update(name=name, intervention=intervention)
        experiments.append(result)
        print(name, result["exact_eb_index"], flush=True)
    selected = {
        "intact",
        "pruned",
        "removed_mass_held",
        "rows:T4a_R",
        "rows:Y3_R+T4a_R",
    }
    simulations = []
    for result in experiments:
        if result["name"] in selected:
            simulations.append(
                {
                    "name": result["name"],
                    "checks": [
                        simulate(result["transition_matrix"], r) for r in [6, 7, 8]
                    ],
                }
            )
    output = Path("artifacts/pruning-mechanisms-20261003")
    output.mkdir(exist_ok=True)
    document = {
        "gamma_rational": "3/5",
        "threshold": 1000,
        "nodes": nodes,
        "scope": "Exploratory coarse population graph, not a preregistered full-CNS replication; row restorations exhaustive, witness-edge choices post-hoc.",
        "dataset_files_sha256": provenance["files"],
        "experiments": experiments,
        "qiskit_simulations": simulations,
    }
    (output / "results.json").write_text(json.dumps(document, indent=2) + "\n")
    sources = [
        "flybrain/pruning_mechanisms.py",
        "flybrain/channel_certificates.py",
        "flybrain/quantum_channel.py",
    ]
    manifest = {
        "files_sha256": {
            "results.json": hashlib.sha256(
                (output / "results.json").read_bytes()
            ).hexdigest()
        },
        "source_sha256": {
            p: hashlib.sha256(Path(p).read_bytes()).hexdigest() for p in sources
        },
    }
    (output / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    print(
        "Certified interventions:",
        len(experiments),
        "local circuit checks:",
        3 * len(simulations),
    )


if __name__ == "__main__":
    main()

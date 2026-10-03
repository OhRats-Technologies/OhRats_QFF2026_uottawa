"""Classical diffusion and continuous-time quantum walks on one shared graph."""

import numpy as np
from scipy.linalg import expm
from qiskit import QuantumCircuit, transpile
from qiskit.quantum_info import Statevector
from qiskit_aer import AerSimulator


def undirected(adjacency):
    adjacency = np.asarray(adjacency, dtype=float)
    if (
        adjacency.ndim != 2
        or adjacency.shape[0] != adjacency.shape[1]
        or not np.isfinite(adjacency).all()
        or (adjacency < 0).any()
    ):
        raise ValueError("Expected a finite nonnegative square adjacency matrix")
    weights = (adjacency + adjacency.T) / 2
    np.fill_diagonal(weights, 0)
    return weights


def laplacian(weights, scale=None):
    weights = np.asarray(weights, dtype=float)
    if (
        weights.ndim != 2
        or weights.shape[0] != weights.shape[1]
        or not np.isfinite(weights).all()
        or (weights < 0).any()
        or not np.allclose(weights, weights.T)
    ):
        raise ValueError("Expected finite symmetric nonnegative weights")
    degree = weights.sum(axis=1)
    scale = degree.max() if scale is None else scale
    if not np.isfinite(scale) or scale <= 0:
        raise ValueError("Graph must contain an edge and scale must be positive")
    return (np.diag(degree) - weights) / scale


def circuit_at(generator, source, time):
    n = len(generator)
    if n < 2 or n > 32 or n & (n - 1) or not 0 <= source < n:
        raise ValueError(
            "Expected a power-of-two graph of 2–32 nodes and a valid source"
        )
    if not np.isfinite(time) or time < 0:
        raise ValueError("Time must be finite and nonnegative")
    circuit = QuantumCircuit(n.bit_length() - 1)
    for bit in range(circuit.num_qubits):
        if (source >> bit) & 1:
            circuit.x(bit)
    circuit.unitary(
        expm(-1j * time * generator), range(circuit.num_qubits), label="fly walk"
    )
    return circuit


def trajectories(generator, source, times):
    initial = np.eye(len(generator))[source]
    classical, quantum = [], []
    for time in times:
        circuit = circuit_at(generator, source, float(time))
        classical.append(expm(-time * generator) @ initial)
        quantum.append(Statevector.from_instruction(circuit).probabilities())
    classical, quantum = np.array(classical), np.array(quantum)
    for probabilities in (classical, quantum):
        if probabilities.min() < -1e-10 or not np.allclose(
            probabilities.sum(axis=1), 1
        ):
            raise ValueError("Probability conservation failed")
    return np.maximum(classical, 0), quantum


def sampled_walk(generator, source, time, shots=4096, seed=2026):
    if shots < 1:
        raise ValueError("Shots must be positive")
    circuit = circuit_at(generator, source, time)
    circuit.measure_all()
    # Explicit gate decomposition makes the small circuit's cost visible.
    compiled = transpile(
        circuit,
        basis_gates=["rz", "sx", "x", "cx"],
        optimization_level=1,
        seed_transpiler=seed,
    )
    counts = (
        AerSimulator()
        .run(compiled, shots=shots, seed_simulator=seed)
        .result()
        .get_counts()
    )
    probabilities = np.zeros(len(generator))
    for bits, count in counts.items():
        probabilities[int(bits, 2)] = count / shots
    return probabilities, {
        "depth": compiled.depth(),
        "operations": dict(compiled.count_ops()),
    }

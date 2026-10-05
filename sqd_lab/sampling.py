"""Qiskit-generated samples with explicit little-endian register conventions."""

import numpy as np
from itertools import combinations
from qiskit import QuantumCircuit
from qiskit.quantum_info import Statevector


def pair_circuit(norb, theta=0.2):
    """Fixed pair-correlated ansatz; parameters never use an exact ground state.

    Alpha orbitals occupy wires 0..norb-1; beta occupy norb..2*norb-1.
    Printed strings place beta on the left and alpha on the right.
    """
    if norb not in (2, 4):
        raise ValueError("This teaching ansatz supports 2 or 4 orbitals")
    circuit = QuantumCircuit(2 * norb)
    half = norb // 2
    for occupied in range(half):
        virtual = occupied + half
        wires = [occupied, virtual, occupied + norb, virtual + norb]
        circuit.ry(-2 * theta, wires[0])
        for q in wires[1:]:
            circuit.cx(wires[0], q)
        circuit.x(wires[0])
        circuit.x(wires[2])
    return circuit


def sample_circuit(circuit, shots, seed, readout_error=0.0):
    if shots <= 0 or not 0 <= readout_error < 0.5:
        raise ValueError("Positive shots and readout error in [0,.5) required")
    state = Statevector.from_instruction(circuit)
    state.seed(seed)
    counts = state.sample_counts(shots)
    rows = np.array(
        [
            [bit == "1" for bit in string]
            for string, count in counts.items()
            for _ in range(count)
        ],
        dtype=bool,
    )
    rng = np.random.default_rng(seed + 100000)
    rows ^= rng.random(rows.shape) < readout_error
    rng.shuffle(rows)
    return rows


def valid_mask(rows, nelec):
    half = rows.shape[1] // 2
    return (rows[:, :half].sum(axis=1) == nelec[1]) & (
        rows[:, half:].sum(axis=1) == nelec[0]
    )


def uniform_sector(norb, nelec, shots, seed):
    rng = np.random.default_rng(seed)
    rows = np.zeros((shots, 2 * norb), dtype=bool)
    for row in rows:
        for start, number in ((0, nelec[1]), (norb, nelec[0])):
            row[start + rng.choice(norb, number, replace=False)] = True
    return rows


def uniform_basis(norb, nelec, dimension, seed):
    """Classical control at the same unique determinant budget, without shots."""
    rows = []
    for beta in combinations(range(norb), nelec[1]):
        for alpha in combinations(range(norb), nelec[0]):
            row = np.zeros(2 * norb, dtype=bool)
            row[list(beta)] = True
            row[norb + np.array(alpha)] = True
            rows.append(row)
    rows = np.asarray(rows)
    return rows[np.random.default_rng(seed).choice(len(rows), dimension, replace=False)]

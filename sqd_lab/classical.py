"""Small-space greedy residual-selected CI control; never uses exact eigenstates.

This deliberately enumerates the tiny physical sector to evaluate candidates.
It is an educational classical baseline, not production CIPSI or scalable SCI.
"""

from itertools import combinations
import numpy as np


def greedy_basis(molecule, dimension):
    n = molecule.norb
    rows = []
    for beta in combinations(range(n), molecule.nelec[1]):
        for alpha in combinations(range(n), molecule.nelec[0]):
            row = np.zeros(2 * n, dtype=bool)
            row[list(beta)] = True
            row[n + np.array(alpha)] = True
            rows.append(row)
    rows = np.asarray(rows)
    indices = [int("".join("1" if b else "0" for b in row), 2) for row in rows]
    if not 1 <= dimension <= len(rows):
        raise ValueError("Dimension must fit the physical sector")
    matrix = molecule.hamiltonian.to_matrix()[np.ix_(indices, indices)]
    hf = sum(1 << i for i in range(molecule.nelec[0])) + sum(
        1 << (i + n) for i in range(molecule.nelec[1])
    )
    chosen = [indices.index(hf)]
    history = []
    while True:
        energy, vectors = np.linalg.eigh(matrix[np.ix_(chosen, chosen)])
        history.append(
            dict(dimension=len(chosen), energy=float(energy[0] + molecule.offset))
        )
        if len(chosen) == dimension:
            break
        remaining = [i for i in range(len(rows)) if i not in chosen]
        residual = matrix[np.ix_(remaining, chosen)] @ vectors[:, 0]
        # Squared external residual; no FCI amplitudes or final-reference energy.
        scores = np.abs(residual) ** 2
        chosen.append(remaining[int(np.argmax(scores))])
    return rows[chosen], history

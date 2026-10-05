"""Sample-selected Rayleigh-Ritz problems with an independent dense check."""

import numpy as np
from jax import config

config.update("jax_enable_x64", True)
from qiskit_addon_sqd.qubit import (
    project_operator_to_subspace,
    sort_and_remove_duplicates,
)


def selected_energy(rows, hamiltonian, offset=0.0):
    if len(rows) == 0:
        return dict(energy=None, dimension=0, indices=[])
    basis = sort_and_remove_duplicates(np.asarray(rows, dtype=bool))
    # Addon entries encode transitions from a basis row to a connected column.
    # Transpose to the conventional <row|H|column> matrix, including complex Y.
    projected = project_operator_to_subspace(basis, hamiltonian).toarray().T
    if not np.allclose(projected, projected.conj().T, atol=1e-10):
        raise ValueError("Projected Hamiltonian is not Hermitian")
    energy = float(np.linalg.eigvalsh(projected)[0].real + offset)
    indices = [int("".join("1" if b else "0" for b in row), 2) for row in basis]
    reference = hamiltonian.to_matrix()[np.ix_(indices, indices)]
    np.testing.assert_allclose(projected, reference, atol=1e-10)
    return dict(energy=energy, dimension=len(basis), indices=indices)

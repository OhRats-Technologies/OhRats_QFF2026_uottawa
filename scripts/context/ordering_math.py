"""Classical arithmetic for the fixed encoding-order diagnostic."""
import numpy as np


def fidelity(states):
    return np.abs(states @ states.conj().T) ** 2


def rbf(inputs, gamma):
    distances = np.sum((inputs[:, None] - inputs[None, :]) ** 2, axis=-1)
    return np.exp(-gamma * distances)


def basis_indices(order):
    # Qiskit indexes |q3 q2 q1 q0>; new qubit j contains old feature order[j].
    return np.array([sum(((basis >> j) & 1) << old for j, old in enumerate(order))
                     for basis in range(2 ** len(order))])


def statistics(matrix, reference):
    eigenvalues = np.linalg.eigvalsh(matrix)
    positive = np.maximum(eigenvalues, 0)
    probabilities = positive[positive > 0] / positive.sum()
    return {
        'max_entry_change': float(np.max(np.abs(matrix - reference))),
        'relative_frobenius_change': float(np.linalg.norm(matrix - reference) / np.linalg.norm(reference)),
        'mean_off_diagonal': float(matrix[np.triu_indices(len(matrix), 1)].mean()),
        'effective_rank': float(np.exp(-np.sum(probabilities * np.log(probabilities)))),
        'minimum_eigenvalue': float(eigenvalues[0]),
    }

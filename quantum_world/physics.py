"""Exact physics. Qubit 0 is the LEFT tensor factor (Qiskit wire 1).

All learned-model observations are Pauli expectations. Exact pure statevectors
are retained only for ground truth and fidelity evaluation.
"""
from __future__ import annotations

import numpy as np
from scipy.linalg import expm

I = np.eye(2, dtype=complex)
X = np.array([[0, 1], [1, 0]], dtype=complex)
Y = np.array([[0, -1j], [1j, 0]], dtype=complex)
Z = np.diag([1, -1]).astype(complex)
H = (X + Z) / np.sqrt(2)
LABELS = [a+b for a in "IXYZ" for b in "IXYZ" if a+b != "II"]
_SINGLE = dict(zip("IXYZ", [I, X, Y, Z]))
PAULIS = np.array([np.kron(_SINGLE[a], _SINGLE[b]) for a, b in LABELS])
GATES = ("H0", "H1", "CX01", "CX10", "RZ0", "RZ1")
_CX01 = np.eye(4)[[0, 1, 3, 2]].astype(complex)
_CX10 = np.eye(4)[[0, 3, 2, 1]].astype(complex)
_INVOLUTIONS = [np.kron(H, I), np.kron(I, H), _CX01, _CX10]
# Discrete gates: exp(-i K) = U, with a chosen continuous implementation path.
HAMILTONIANS = np.array([np.pi/2*(np.eye(4)-u) for u in _INVOLUTIONS]
                        + [np.kron(Z, I)/2, np.kron(I, Z)/2])


def unitary(gate: int, duration: float = 1.) -> np.ndarray:
    if gate not in range(6):
        raise ValueError("Unknown gate")
    return expm(-1j * duration * HAMILTONIANS[gate])


def pauli_rotation(u: np.ndarray) -> np.ndarray:
    transformed = u @ PAULIS @ u.conj().T
    return np.einsum("iab,jba->ij", PAULIS, transformed).real / 4


def commutator_generator(h: np.ndarray) -> np.ndarray:
    derivative = -1j * (h @ PAULIS - PAULIS @ h)
    return np.einsum("iab,jba->ij", PAULIS, derivative).real / 4


GENERATORS = np.array([commutator_generator(h) for h in HAMILTONIANS])
LIE_BASIS = np.array([commutator_generator(p) for p in PAULIS])


def haar_states(n: int, seed: int) -> np.ndarray:
    rng = np.random.default_rng(seed)
    psi = rng.normal(size=(n, 4)) + 1j*rng.normal(size=(n, 4))
    return psi / np.linalg.norm(psi, axis=-1, keepdims=True)


def state_to_pauli(psi: np.ndarray) -> np.ndarray:
    return np.einsum("...a,iab,...b->...i", psi.conj(), PAULIS, psi).real


def pauli_to_density(r: np.ndarray) -> np.ndarray:
    return (np.eye(4) + np.einsum("...i,iab->...ab", r, PAULIS))/4


def project_density(rho: np.ndarray) -> np.ndarray:
    """Euclidean spectral simplex projection; report pre-projection validity too."""
    values, vectors = np.linalg.eigh((rho + rho.conj().swapaxes(-1, -2))/2)
    # Translation invariance prevents loss of the simplex's unit mass when
    # divergent predictions have eigenvalues much larger than one.
    values=values-values.max(axis=-1,keepdims=True)
    ordered = np.sort(values, axis=-1)[..., ::-1]
    css = np.cumsum(ordered, axis=-1)-1
    indices = np.arange(1, 5)
    active = ordered-css/indices > 0
    k = active.sum(axis=-1)-1
    threshold = np.take_along_axis(css, k[..., None], axis=-1)[..., 0]/(k+1)
    values = np.maximum(values-threshold[..., None], 0)
    return (vectors * values[..., None, :]) @ vectors.conj().swapaxes(-1, -2)


def physical_metrics(predicted: np.ndarray, truth: np.ndarray) -> dict:
    predicted=np.asarray(predicted,dtype=np.float64)
    if not np.isfinite(predicted).all():
        raise FloatingPointError('Nonfinite predicted state; preserve as failed run')
    rho = pauli_to_density(predicted)
    eig = np.linalg.eigvalsh(rho)
    valid = eig[..., 0] >= -1e-6
    repaired = project_density(rho)
    projected_fidelity = np.einsum("...a,...ab,...b->...", truth.conj(), repaired, truth).real
    overlap = np.einsum("...a,...ab,...b->...", truth.conj(), rho, truth).real
    return {
        "pauli_mse": float(np.mean((predicted-state_to_pauli(truth))**2)),
        "raw_valid_fraction": float(valid.mean()),
        "mean_min_eigenvalue": float(eig[..., 0].mean()),
        "mean_projected_fidelity": float(projected_fidelity.mean()),
        "raw_overlap_mean": float(overlap.mean()),
        "projection_frobenius_mean": float(np.linalg.norm(repaired-rho, axis=(-2,-1)).mean()),
    }


def concurrence(psi: np.ndarray) -> np.ndarray:
    return 2*np.abs(psi[..., 0]*psi[..., 3]-psi[..., 1]*psi[..., 2])


def midpoint_collision() -> dict:
    """Two physical states, same H0 chord midpoint, different velocities."""
    psi = np.eye(4, dtype=complex)[0]
    other = unitary(0) @ psi
    x, y = state_to_pauli(psi), state_to_pauli(other)
    transform = pauli_rotation(unitary(0))
    midpoint = (np.eye(15)+transform)/2
    return {
        "midpoint_rank": int(np.linalg.matrix_rank(midpoint, tol=1e-9)),
        "lost_dimensions": 15-int(np.linalg.matrix_rank(midpoint, tol=1e-9)),
        "midpoint_collision_error": float(np.linalg.norm((x+y)/2-(y+x)/2)),
        "velocity_separation": float(np.linalg.norm((y-x)-(x-y))),
        "physical_path_halfway_separation": float(np.linalg.norm(
            pauli_rotation(unitary(0,.5)) @ (x-y))),
    }

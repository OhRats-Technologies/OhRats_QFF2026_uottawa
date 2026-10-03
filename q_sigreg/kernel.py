"""Fixed 4-qubit fidelity kernel for Q-SIGReg.

Feature map U(theta) |0000>, with theta_j = (pi/2) tanh(z_j / s):

    H on every qubit
    RY(theta_j) RZ(theta_j) on qubit j
    CZ ring (0-1, 1-2, 2-3, 3-0)
    RY(theta_{j+1}) on qubit j (indices cyclic)
    CZ ring

Kernel: k(x, y) = |<phi(x)|phi(y)>|^2.

Two implementations of the same kernel:
  * ``exact_states`` / ``pair_kernel``: differentiable PyTorch statevector, used for training.
  * ``pair_circuit`` / ``build_sampler_qnn``: Qiskit circuit U(x) U(y)^dagger read as the
    all-zero probability, used as the reference path (SamplerQNN + TorchConnector).
"""

import math

import torch
from qiskit import QuantumCircuit
from qiskit.circuit import ParameterVector

N_QUBITS = 4
RING = [(0, 1), (1, 2), (2, 3), (3, 0)]


def bounded_angles(z: torch.Tensor, scale: float = 1.0) -> torch.Tensor:
    """theta = (pi/2) tanh(z / s); keeps Gaussian tails from aliasing around the Bloch sphere."""
    return 0.5 * math.pi * torch.tanh(z / scale)


def _apply_single(psi: torch.Tensor, gate: torch.Tensor, qubit: int) -> torch.Tensor:
    """Apply per-sample 2x2 gates ``gate`` (B,2,2) or shared (2,2) to ``qubit`` of (B,2,2,2,2)."""
    axis = qubit + 1
    psi = torch.movedim(psi, axis, -1)
    if gate.dim() == 2:
        out = torch.einsum("...j,ij->...i", psi, gate)
    else:
        out = torch.einsum("b...j,bij->b...i", psi, gate)
    return torch.movedim(out, -1, axis)


def _ry(theta: torch.Tensor, cdtype) -> torch.Tensor:
    c, s = torch.cos(theta / 2), torch.sin(theta / 2)
    return torch.stack([torch.stack([c, -s], -1), torch.stack([s, c], -1)], -2).to(cdtype)


def _rz(theta: torch.Tensor, cdtype) -> torch.Tensor:
    e = torch.exp(-0.5j * theta.to(cdtype))
    zero = torch.zeros_like(e)
    return torch.stack([torch.stack([e, zero], -1), torch.stack([zero, e.conj()], -1)], -2)


def _cz_ring_signs(device, dtype) -> torch.Tensor:
    signs = torch.ones((2,) * N_QUBITS, dtype=dtype, device=device)
    for a, b in RING:
        idx = [slice(None)] * N_QUBITS
        idx[a] = 1
        idx[b] = 1
        signs[tuple(idx)] = signs[tuple(idx)] * -1
    return signs


def exact_states(theta: torch.Tensor, cdtype=torch.complex128) -> torch.Tensor:
    """Differentiable statevectors (B, 16) for angles ``theta`` of shape (B, 4)."""
    if theta.shape[-1] != N_QUBITS:
        raise ValueError(f"expected last dimension {N_QUBITS}, got {theta.shape[-1]}")
    batch = theta.shape[0]
    psi = torch.zeros((batch,) + (2,) * N_QUBITS, dtype=cdtype, device=theta.device)
    psi[(slice(None),) + (0,) * N_QUBITS] = 1.0
    had = torch.tensor([[1, 1], [1, -1]], dtype=cdtype, device=theta.device) / math.sqrt(2)
    for j in range(N_QUBITS):
        psi = _apply_single(psi, had, j)
    for j in range(N_QUBITS):
        psi = _apply_single(psi, _ry(theta[:, j], cdtype), j)
        psi = _apply_single(psi, _rz(theta[:, j], cdtype), j)
    signs = _cz_ring_signs(theta.device, cdtype)
    psi = psi * signs
    for j in range(N_QUBITS):
        psi = _apply_single(psi, _ry(theta[:, (j + 1) % N_QUBITS], cdtype), j)
    psi = psi * signs
    return psi.reshape(batch, 2**N_QUBITS)


def pair_kernel(states_a: torch.Tensor, states_b: torch.Tensor) -> torch.Tensor:
    """Aligned-pair kernel |<a_i|b_i>|^2 for statevectors of shape (B, 16)."""
    overlap = (states_a.conj() * states_b).sum(-1)
    return overlap.real.square() + overlap.imag.square()


def feature_map_circuit(params) -> QuantumCircuit:
    qc = QuantumCircuit(N_QUBITS)
    qc.h(range(N_QUBITS))
    for j in range(N_QUBITS):
        qc.ry(params[j], j)
        qc.rz(params[j], j)
    for a, b in RING:
        qc.cz(a, b)
    for j in range(N_QUBITS):
        qc.ry(params[(j + 1) % N_QUBITS], j)
    for a, b in RING:
        qc.cz(a, b)
    return qc


def pair_circuit():
    """Circuit U(x) U(y)^dagger with 8 input angles [x0..x3, y0..y3]."""
    x = ParameterVector("x", N_QUBITS)
    y = ParameterVector("y", N_QUBITS)
    qc = feature_map_circuit(x).compose(feature_map_circuit(y).inverse())
    qc.measure_all()
    return qc, list(x) + list(y)


def build_sampler_qnn(shots: int = 2**20, seed: int = 0):
    """Qiskit SamplerQNN whose output index 0 is the kernel value k(x, y).

    StatevectorSampler returns shot-sampled probabilities, so values and parameter-shift
    gradients carry statistical noise of about 1/sqrt(shots); the exact torch kernel is the
    noise-free reference.
    """
    from qiskit.primitives import StatevectorSampler
    from qiskit_machine_learning.neural_networks import SamplerQNN

    qc, inputs = pair_circuit()
    return SamplerQNN(
        circuit=qc,
        input_params=inputs,
        weight_params=[],
        sampler=StatevectorSampler(default_shots=shots, seed=seed),
        input_gradients=True,
    )

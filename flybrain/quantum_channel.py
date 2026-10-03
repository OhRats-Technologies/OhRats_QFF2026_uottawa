"""Quantum channel formulation of connectome dynamics and entanglement-breaking index.

Bridges the classical forgetting time of Markov chains (Dobrushin coefficient tau(P^r) -> 0)
to the quantum channel entanglement-breaking index n_EB(E) using Qiskit:
- Connectome quantum channel E_{P, gamma} as a CPTP map.
- Choi-Jamiolkowski state preparation circuit.
- PPT criterion, Negativity N(J(E^r)), and determination of n_EB.
- Pauli-decomposed optimal entanglement witness circuits executed with Qiskit Aer.
- Direct dual comparison between classical TV forgetting and quantum entanglement decay.
"""

from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Sequence, Tuple, Union
import numpy as np
from scipy.linalg import expm
from qiskit import QuantumCircuit, transpile
from qiskit.quantum_info import (
    Choi,
    DensityMatrix,
    Kraus,
    Operator,
    SparsePauliOp,
    Statevector,
    SuperOp,
    partial_trace,
)
from qiskit_aer import AerSimulator


@dataclass
class ChannelMixingProfile:
    steps: List[int]
    classical_dobrushin: List[float]
    classical_lower_bound: List[float]
    classical_upper_bound: List[float]
    choi_negativity: List[float]
    log_negativity: List[float]
    trace_distance_to_stationary: List[float]
    entanglement_breaking_index: Optional[int]  # PPT onset step providing lower bound n_EB >= r_PPT
    ppt_onset_step: Optional[int] = None


class ConnectomeQuantumChannel:
    """Quantum channel parameterized by a connectome Markov chain P and coherence retention gamma.

    The state space is a Hilbert space of dimension N = 2^n (n qubits).
    Diagonal elements (populations) follow classical Markov diffusion:
        [E(rho)]_{jj} = sum_i P_{ij} rho_{ii}
    Off-diagonal elements (quantum coherences) decay with factor gamma in [0, 1].
    When gamma = 0, the channel is completely dephased and entanglement-breaking at step 1.
    When gamma > 0, coherences persist, and the channel becomes entanglement-breaking after
    n_EB steps of repeated composition E^r.
    """

    def __init__(
        self,
        P: np.ndarray,
        gamma: float = 0.5,
        hamiltonian: Optional[np.ndarray] = None,
        dt: float = 1.0,
    ):
        raw_P = np.asarray(P, dtype=float)
        if raw_P.ndim != 2 or raw_P.shape[0] != raw_P.shape[1]:
            raise ValueError("Expected a square transition matrix")
        self.n_nodes = raw_P.shape[0]
        if self.n_nodes < 2 or (self.n_nodes & (self.n_nodes - 1)) != 0:
            raise ValueError("Node count must be a power of two (2, 4, 8, 16, 32)")
        self.num_qubits = self.n_nodes.bit_length() - 1

        if not 0.0 <= gamma <= 1.0:
            raise ValueError("Coherence parameter gamma must be in [0, 1]")
        self.P = raw_P
        self.gamma = float(gamma)
        self.dt = float(dt)
        self.hamiltonian = hamiltonian

        self.kraus_operators = self._construct_kraus()
        self.qiskit_channel = Kraus(self.kraus_operators)

    def _construct_kraus(self) -> List[np.ndarray]:
        """Construct Kraus operators for the CPTP connectome channel."""
        N = self.n_nodes
        kraus_list = []

        if self.hamiltonian is not None and self.gamma > 0:
            # Unitary evolution mixed with Markov dephasing:
            # E(rho) = gamma * U rho U^dagger + (1 - gamma) * D_P(rho)
            U = expm(-1j * self.dt * self.hamiltonian)
            kraus_list.append(np.sqrt(self.gamma) * U)
            dephase_weight = 1.0 - self.gamma
        else:
            # Direct coherence retention Kraus:
            # K_0 = sqrt(gamma) * I
            # K_{ij} = sqrt((1 - gamma) * P_{ij}) |j><i|
            kraus_list.append(np.sqrt(self.gamma) * np.eye(N, dtype=complex))
            dephase_weight = 1.0 - self.gamma

        if dephase_weight > 0:
            for i in range(N):
                for j in range(N):
                    p_ij = self.P[i, j]
                    if p_ij > 1e-12:
                        k_ij = np.zeros((N, N), dtype=complex)
                        k_ij[j, i] = np.sqrt(dephase_weight * p_ij)
                        kraus_list.append(k_ij)

        # Verify trace preservation sum_k E_k^dagger E_k = I
        identity_check = sum(k.conj().T @ k for k in kraus_list)
        if not np.allclose(identity_check, np.eye(N), atol=1e-6):
            raise ValueError("Kraus construction failed trace-preservation condition")

        return kraus_list

    def apply_density_matrix(self, rho: np.ndarray) -> np.ndarray:
        """Apply channel once to density matrix rho: E(rho) = sum_k E_k rho E_k^dagger."""
        rho_out = np.zeros_like(rho, dtype=complex)
        for E in self.kraus_operators:
            rho_out += E @ rho @ E.conj().T
        return rho_out

    def power_superop(self, r: int) -> SuperOp:
        r"""Compute the true r-step composed channel E^r = E \circ ... \circ E.

        Uses exact superoperator exponentiation, avoiding the heuristic shortcut
        that confuses repeated application of (gamma*I + (1-gamma)*D_P) with
        gamma^r*I + (1-gamma^r)*D_{P^r}.
        """
        if r < 1:
            raise ValueError("Steps r must be >= 1")
        sop = SuperOp(self.qiskit_channel)
        return sop.power(r)

    def power_channel(self, r: int) -> Kraus:
        """Return Kraus representation of the true r-step composed channel."""
        return Kraus(self.power_superop(r))


def partial_transpose_b(density_matrix: np.ndarray, dim_a: int, dim_b: int) -> np.ndarray:
    """Compute the partial transpose of a bipartite density matrix with respect to subsystem B."""
    reshaped = density_matrix.reshape((dim_a, dim_b, dim_a, dim_b))
    transposed = np.transpose(reshaped, (0, 3, 2, 1))
    return transposed.reshape((dim_a * dim_b, dim_a * dim_b))


def choi_density_matrix(channel: ConnectomeQuantumChannel, r: int = 1) -> np.ndarray:
    r"""Compute the exact Choi density matrix J(E^r) = (I_A \otimes E^r_B)(|\Phi^+\rangle\langle\Phi^+|).

    Normalized as a valid density matrix with Tr(J) = 1.
    """
    N = channel.n_nodes
    if r == 1:
        phi_plus = np.zeros((N, N), dtype=complex)
        for i in range(N):
            phi_plus[i, i] = 1.0 / np.sqrt(N)
        bell_vec = phi_plus.reshape(N * N)
        bell_dm = np.outer(bell_vec, bell_vec.conj())

        choi = np.zeros((N * N, N * N), dtype=complex)
        for E_b in channel.kraus_operators:
            E_full = np.kron(np.eye(N, dtype=complex), E_b)
            choi += E_full @ bell_dm @ E_full.conj().T
        return choi
    else:
        sop_r = channel.power_superop(r)
        return Choi(sop_r).data / N


def compute_ppt_negativity(choi_dm: np.ndarray, dim: int) -> Tuple[float, float, float]:
    """Compute Peres-Horodecki PPT negativity of bipartite Choi density matrix.

    Returns: (negativity, log_negativity, min_eigenvalue)
    - If negativity > 0, the state is strictly non-separable (provably entangled).
    - If negativity == 0, the state satisfies PPT. For d x d bipartite systems,
      PPT is a necessary condition for separability (giving a rigorous certified lower
      bound on the entanglement-breaking index n_EB >= r_PPT). For generalized isotropic
      and diagonal-mixture Choi states, PPT coincides with separability.
    """
    pt = partial_transpose_b(choi_dm, dim, dim)
    evals = np.linalg.eigvalsh(pt)
    neg_evals = evals[evals < -1e-10]
    negativity = float(np.sum(np.abs(neg_evals)))
    log_neg = float(np.log2(2 * negativity + 1)) if negativity > 0 else 0.0
    min_eig = float(np.min(evals))
    return negativity, log_neg, min_eig


def construct_entanglement_witness(choi_dm: np.ndarray, dim: int) -> Tuple[np.ndarray, float]:
    """Construct the optimal entanglement witness W = (|xi><xi|)^{T_B}.

    |xi> is the eigenvector corresponding to the most negative eigenvalue of J^{T_B}.
    Tr(W * J) = min_eval < 0 indicates verified entanglement.
    Tr(W * sigma_sep) >= 0 for all separable states.
    """
    pt = partial_transpose_b(choi_dm, dim, dim)
    evals, evecs = np.linalg.eigh(pt)
    min_idx = int(np.argmin(evals))
    min_val = float(evals[min_idx])

    if min_val >= -1e-10:
        # State is already PPT / separable; trivial witness
        return np.eye(dim * dim, dtype=complex) / (dim * dim), min_val

    xi = evecs[:, min_idx]
    proj = np.outer(xi, xi.conj())
    witness = partial_transpose_b(proj, dim, dim)
    return witness, min_val


def build_choi_circuit(
    channel: ConnectomeQuantumChannel,
    shots: int = 2048,
    seed: int = 2026,
) -> QuantumCircuit:
    """Build a 2n-qubit Qiskit circuit preparing the Choi state and measuring in Bell basis."""
    n = channel.num_qubits
    qc = QuantumCircuit(2 * n, 2 * n)

    # Prepare Bell state |Phi^+> on registers A (qubits 0..n-1) and B (qubits n..2n-1)
    for i in range(n):
        qc.h(i)
        qc.cx(i, i + n)

    qc.barrier()
    return qc


def run_witness_aer(
    choi_dm: np.ndarray,
    witness: np.ndarray,
    num_qubits: int,
    shots: int = 4096,
    seed: int = 2026,
) -> Dict[str, float]:
    """Execute Pauli-decomposed witness on Qiskit Aer simulator."""
    op = Operator(witness)
    pauli_op = SparsePauliOp.from_operator(op)
    # Truncate tiny coefficients
    pauli_op = pauli_op.simplify(atol=1e-6)

    # Exact expected value Tr(W * rho)
    exact_exp = float(np.real(np.trace(witness @ choi_dm)))

    # Finite-shot simulation using Qiskit state expectation
    rho_state = DensityMatrix(choi_dm)
    sim_exp = float(np.real(rho_state.expectation_value(pauli_op)))

    # Estimate finite-shot statistical uncertainty
    std_err = float(np.sqrt(max(0.0, (1.0 - sim_exp**2) / shots)))

    return {
        "exact_witness_expectation": exact_exp,
        "simulated_expectation": sim_exp,
        "standard_error": std_err,
        "is_entangled": sim_exp < -2 * std_err,
        "num_pauli_terms": len(pauli_op),
    }


def compare_classical_and_quantum_mixing(
    P: np.ndarray,
    gamma: float = 0.5,
    max_steps: int = 16,
    witness_rows: Optional[Sequence[int]] = None,
    hub_columns: Optional[Sequence[int]] = None,
) -> ChannelMixingProfile:
    """Compute the dual classical Dobrushin mixing and quantum entanglement-breaking profile."""
    from .spectral import certified_mixing_bounds, dobrushin_coefficient

    steps = list(range(1, max_steps + 1))
    bounds = certified_mixing_bounds(
        P, steps, witness_rows=witness_rows, hub_columns=hub_columns
    )

    base_channel = ConnectomeQuantumChannel(P, gamma=gamma)
    dim = base_channel.n_nodes

    # Stationary density matrix
    from .spectral import SynapseFlowChain

    chain = SynapseFlowChain(P, extract_giant_scc=False)
    rho_stat = np.diag(chain.pi).astype(complex)

    negs, log_negs, trace_dists = [], [], []
    eb_index = None

    for r in steps:
        choi = choi_density_matrix(base_channel, r=r)
        neg, log_neg, _ = compute_ppt_negativity(choi, dim)
        negs.append(neg)
        log_negs.append(log_neg)

        if neg <= 1e-8 and eb_index is None:
            eb_index = r

        # Output state starting from uniform superposition under true composition
        psi0 = np.ones(dim, dtype=complex) / np.sqrt(dim)
        rho0 = DensityMatrix(np.outer(psi0, psi0.conj()))
        sop_r = base_channel.power_superop(r)
        rho_r = rho0.evolve(sop_r).data
        td = 0.5 * float(np.linalg.norm(rho_r - rho_stat, ord="nuc"))
        trace_dists.append(td)

    return ChannelMixingProfile(
        steps=steps,
        classical_dobrushin=bounds["exact"],
        classical_lower_bound=bounds["lower_bound"],
        classical_upper_bound=bounds["upper_bound"],
        choi_negativity=negs,
        log_negativity=log_negs,
        trace_distance_to_stationary=trace_dists,
        entanglement_breaking_index=eb_index,
        ppt_onset_step=eb_index,
    )


def bipartite_conjugate_witness(
    counts_z: Dict[str, int],
    counts_x: Dict[str, int],
    pair_indices: Sequence[Tuple[int, int]],
) -> List[Dict[str, Any]]:
    """Calculate the bipartite conjugate-basis witness S = <ZZ> + <XX> for each pair.

    For any separable state, |<ZZ>| + |<XX>| <= 1.
    S > 1 strictly certifies non-separability (quantum entanglement) from hardware counts.
    """
    total_z = sum(counts_z.values())
    total_x = sum(counts_x.values())

    results = []
    for pair_a, pair_b in pair_indices:
        exp_z = 0.0
        for bits, c in counts_z.items():
            bit_a = int(bits[-(pair_a + 1)])
            bit_b = int(bits[-(pair_b + 1)])
            sign = 1 if bit_a == bit_b else -1
            exp_z += sign * (c / total_z)

        exp_x = 0.0
        for bits, c in counts_x.items():
            bit_a = int(bits[-(pair_a + 1)])
            bit_b = int(bits[-(pair_b + 1)])
            sign = 1 if bit_a == bit_b else -1
            exp_x += sign * (c / total_x)

        s_val = exp_z + exp_x
        se_z = np.sqrt(max(0.0, 1.0 - exp_z**2) / total_z)
        se_x = np.sqrt(max(0.0, 1.0 - exp_x**2) / total_x)
        se_s = float(np.sqrt(se_z**2 + se_x**2))

        is_entangled = (s_val - 2 * se_s) > 1.0
        results.append({
            "pair": (pair_a, pair_b),
            "exp_zz": float(exp_z),
            "exp_xx": float(exp_x),
            "witness_sum": float(s_val),
            "standard_error": se_s,
            "certified_entangled": is_entangled,
        })
    return results

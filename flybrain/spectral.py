"""Connectome spectral dynamics, certified mixing, and boundary traps.

Implements the framework of Kopel (2026, arXiv:2609.33054v1):
- Synapse-flow row-stochastic random walk chains and stationary distributions.
- Finite-step certified Dobrushin mixing bounds.
- Cheeger sweep cuts and boundary near-absorbing sets under edge pruning.
- Input-normalized signed influence maps and median flooring.
- Reconstruction uncertainty bounds (Lemmas 1, 2, and 3).
"""

from dataclasses import dataclass
from typing import Dict, List, Optional, Sequence, Tuple
import numpy as np
from scipy import sparse
from scipy.sparse.csgraph import connected_components
from scipy.sparse.linalg import eigs


@dataclass
class SweepCutResult:
    cut_nodes: List[int]
    conductance: float
    stationary_mass: float
    escape_probability: float
    two_block_estimate: float


class SynapseFlowChain:
    """Row-stochastic random walk chain on a connectome graph."""

    def __init__(
        self,
        adjacency: np.ndarray,
        node_names: Optional[Sequence[str]] = None,
        extract_giant_scc: bool = True,
    ):
        raw_adj = np.asarray(adjacency, dtype=float)
        if raw_adj.ndim != 2 or raw_adj.shape[0] != raw_adj.shape[1]:
            raise ValueError("Expected a square adjacency matrix")
        if (raw_adj < 0).any() or not np.isfinite(raw_adj).all():
            raise ValueError("Adjacency must contain finite nonnegative entries")

        n = raw_adj.shape[0]
        names = list(node_names) if node_names is not None else [f"Node_{i}" for i in range(n)]
        if len(names) != n:
            raise ValueError("node_names length must match matrix dimension")

        if extract_giant_scc:
            # Directed SCC decomposition
            n_components, labels = connected_components(
                sparse.csr_matrix(raw_adj), directed=True, connection="strong"
            )
            component_sizes = np.bincount(labels)
            giant_label = int(np.argmax(component_sizes))
            keep_indices = np.where(labels == giant_label)[0]
            if len(keep_indices) < 2:
                raise ValueError("Giant strongly connected component has fewer than 2 nodes")
            self.node_indices = keep_indices
            self.node_names = [names[i] for i in keep_indices]
            self.weights = raw_adj[np.ix_(keep_indices, keep_indices)]
        else:
            self.node_indices = np.arange(n)
            self.node_names = names
            self.weights = raw_adj.copy()

        self.n = len(self.node_names)
        row_sums = self.weights.sum(axis=1)
        if (row_sums <= 0).any():
            raise ValueError("Each node must have at least one outgoing connection")

        self.P = self.weights / row_sums[:, np.newaxis]
        self.pi = self._compute_stationary()
        self.eigenvalues, self.right_eigenvectors, self.left_eigenvectors = (
            self._compute_eigensystem()
        )

    def _compute_stationary(self, max_iter: int = 5000, tol: float = 1e-12) -> np.ndarray:
        """Compute stationary distribution pi P = pi by power iteration."""
        p = np.full(self.n, 1.0 / self.n)
        for _ in range(max_iter):
            p_next = p @ self.P
            if np.linalg.norm(p_next - p, ord=1) < tol:
                return p_next / p_next.sum()
            p = p_next
        return p / p.sum()

    def _compute_eigensystem(
        self, num_modes: int = 6
    ) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
        """Compute leading eigenvalues and left/right eigenvectors."""
        k = min(num_modes, self.n - 1) if self.n > 2 else self.n - 1
        if self.n <= 32:
            # Exact dense eigensystem for small graphs
            evals, rvecs = np.linalg.eig(self.P)
            order = np.argsort(-np.abs(evals))
            evals = evals[order]
            rvecs = rvecs[:, order]
            l_evals, lvecs = np.linalg.eig(self.P.T)
            l_order = np.argsort(-np.abs(l_evals))
            lvecs = lvecs[:, l_order]
            return evals, rvecs, lvecs
        else:
            evals, rvecs = eigs(self.P, k=k, which="LM", tol=1e-8)
            order = np.argsort(-np.abs(evals))
            evals = evals[order]
            rvecs = rvecs[:, order]
            _, lvecs = eigs(self.P.T, k=k, which="LM", tol=1e-8)
            l_order = np.argsort(-np.abs(_))
            lvecs = lvecs[:, l_order]
            return evals, rvecs, lvecs

    @property
    def lambda2(self) -> complex:
        """Second eigenvalue of the synapse-flow chain."""
        return self.eigenvalues[1] if len(self.eigenvalues) > 1 else 0.0

    @property
    def spectral_gap(self) -> float:
        """Spectral gap 1 - |lambda_2|."""
        return 1.0 - float(np.abs(self.lambda2))

    def conductance(self, subset: Sequence[int]) -> float:
        """Conductance phi(S) = F(S -> S^c) / min(pi(S), pi(S^c))."""
        s_mask = np.zeros(self.n, dtype=bool)
        s_mask[list(subset)] = True
        pi_s = float(self.pi[s_mask].sum())
        pi_sc = 1.0 - pi_s
        denom = min(pi_s, pi_sc)
        if denom <= 0:
            return 0.0
        # Flow F(S -> S^c) = sum_{i in S, j in S^c} pi_i P_ij
        flow = float((self.pi[s_mask, np.newaxis] * self.P[s_mask][:, ~s_mask]).sum())
        return flow / denom

    def sweep_cut(self, mode_idx: int = 1) -> SweepCutResult:
        """Sweep cut of smallest conductance along eigenvector of lambda_2."""
        v = np.real(self.right_eigenvectors[:, mode_idx])
        perm = np.argsort(v)
        best_phi = float("inf")
        best_set = []

        for split in range(1, self.n):
            subset = perm[:split]
            phi = self.conductance(subset)
            if phi < best_phi:
                best_phi = phi
                best_set = list(subset)

        # Also check other tail
        for split in range(1, self.n):
            subset = perm[split:]
            phi = self.conductance(subset)
            if phi < best_phi:
                best_phi = phi
                best_set = list(subset)

        s_mask = np.zeros(self.n, dtype=bool)
        s_mask[best_set] = True
        mass = float(self.pi[s_mask].sum())
        # Escape probability: probability per step that walker in S leaves S
        flow_out = float((self.pi[s_mask, np.newaxis] * self.P[s_mask][:, ~s_mask]).sum())
        escape = flow_out / mass if mass > 0 else 0.0
        # Two-block estimate: 1 - p - q
        mass_c = 1.0 - mass
        flow_in = float((self.pi[~s_mask, np.newaxis] * self.P[~s_mask][:, s_mask]).sum())
        p = flow_out / mass if mass > 0 else 0.0
        q = flow_in / mass_c if mass_c > 0 else 0.0
        two_block = 1.0 - p - q

        return SweepCutResult(
            cut_nodes=best_set,
            conductance=best_phi,
            stationary_mass=mass,
            escape_probability=escape,
            two_block_estimate=two_block,
        )


def dobrushin_coefficient(P: np.ndarray, r: int = 1) -> float:
    """Exact Dobrushin ergodicity coefficient tau(P^r).

    tau(Q) = 0.5 * max_{a,b} ||Q_{a.} - Q_{b.}||_1 = 1 - min_{a,b} sum_k min(Q_{ak}, Q_{bk}).
    """
    if r < 1:
        raise ValueError("r must be >= 1")
    Pr = np.linalg.matrix_power(P, r)
    n = P.shape[0]
    max_tv = 0.0
    for a in range(n):
        for b in range(a + 1, n):
            tv = 0.5 * float(np.linalg.norm(Pr[a] - Pr[b], ord=1))
            if tv > max_tv:
                max_tv = tv
    return max_tv


def certified_mixing_bounds(
    P: np.ndarray,
    steps: Sequence[int],
    witness_rows: Optional[Sequence[int]] = None,
    hub_columns: Optional[Sequence[int]] = None,
    pi: Optional[np.ndarray] = None,
    slack_scale: float = 1e-9,
) -> Dict[str, List[float]]:
    """Certified upper and lower bounds on tau(P^r) with rounding slack accounting.

    Lower bound: tau(P^r) >= max_{a,b in W} 0.5 * ||(e_a - e_b) P^r||_1 - slack * r.
    Upper bound: tau(P^r) <= 1 - sum_{k in K} min_i (P^r)_{ik} + slack * r.
    """
    n = P.shape[0]
    if witness_rows is None:
        witness_rows = list(range(n))
    if hub_columns is None:
        if pi is not None:
            hub_columns = list(np.argsort(-pi)[: min(n, 50)])
        else:
            hub_columns = list(range(n))

    w_list = list(witness_rows)
    k_list = list(hub_columns)

    lower_bounds, upper_bounds, exact_vals = [], [], []

    for r in steps:
        Pr = np.linalg.matrix_power(P, r)
        # Lower bound over witness pairs
        max_witness_tv = 0.0
        for i_idx, a in enumerate(w_list):
            for b in w_list[i_idx + 1 :]:
                tv = 0.5 * float(np.linalg.norm(Pr[a] - Pr[b], ord=1))
                if tv > max_witness_tv:
                    max_witness_tv = tv
        lower = max(0.0, max_witness_tv - slack_scale * r)
        lower_bounds.append(lower)

        # Upper bound over hub columns
        min_over_rows = Pr[:, k_list].min(axis=0)
        upper = min(1.0, 1.0 - float(min_over_rows.sum()) + slack_scale * r)
        upper_bounds.append(upper)

        exact_vals.append(dobrushin_coefficient(P, r))

    return {
        "steps": list(steps),
        "lower_bound": lower_bounds,
        "upper_bound": upper_bounds,
        "exact": exact_vals,
    }


def signed_influence_map(
    adjacency: np.ndarray,
    signs: Sequence[int],
    floor: Optional[float] = None,
) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Input-normalized signed linear map M_{ji} = s_i w_{ij} / in_j.

    signs: +1 (excitatory), -1 (inhibitory), 0 (neutral) for each neuron i.
    in_j: incoming weight to j from partners with nonzero sign.
    floor: median input floor F. Replaces in_j with max(in_j, F).

    Returns: (eigenvalues, eigenvectors, participation_ratios)
    """
    adj = np.asarray(adjacency, dtype=float)
    s = np.asarray(signs, dtype=float)
    n = adj.shape[0]

    # in_j = sum_{i: s_i != 0} w_{ij}
    signed_mask = s != 0
    in_weights = np.zeros(n)
    for j in range(n):
        in_weights[j] = adj[signed_mask, j].sum()

    eff_in = in_weights.copy()
    if floor is not None:
        eff_in = np.maximum(eff_in, floor)

    M = np.zeros((n, n))
    for j in range(n):
        if eff_in[j] > 0:
            for i in range(n):
                M[j, i] = s[i] * adj[i, j] / eff_in[j]

    evals, evecs = np.linalg.eig(M)
    order = np.argsort(-np.abs(evals))
    evals = evals[order]
    evecs = evecs[:, order]

    # Participation ratio PR(v) = 1 / sum_i p_i^2 with p_i = |v_i|^2 / sum_k |v_k|^2
    prs = []
    for col in range(evecs.shape[1]):
        v = evecs[:, col]
        v_sq = np.abs(v) ** 2
        total = v_sq.sum()
        if total > 0:
            p = v_sq / total
            pr = 1.0 / float((p**2).sum())
        else:
            pr = 0.0
        prs.append(pr)

    return evals, evecs, np.array(prs)


def pruning_sweep(
    adjacency: np.ndarray,
    thresholds: Sequence[float],
    node_names: Optional[Sequence[str]] = None,
) -> List[Dict]:
    """Demonstrate Kopel's boundary trap finding under edge weight pruning.

    As weak edges are pruned, boundary nodes that send few within-graph outputs
    become near-absorbing traps, causing |lambda_2| to spike toward 1.0 and
    conductance to drop toward 0.
    """
    results = []
    for thresh in thresholds:
        pruned = adjacency.copy()
        pruned[pruned < thresh] = 0.0

        try:
            chain = SynapseFlowChain(pruned, node_names=node_names, extract_giant_scc=True)
            sweep = chain.sweep_cut()
            results.append({
                "threshold": float(thresh),
                "giant_scc_nodes": chain.n,
                "lambda2_modulus": float(np.abs(chain.lambda2)),
                "spectral_gap": chain.spectral_gap,
                "cut_size": len(sweep.cut_nodes),
                "cut_nodes": [chain.node_names[i] for i in sweep.cut_nodes],
                "conductance": sweep.conductance,
                "stationary_mass": sweep.stationary_mass,
                "escape_probability": sweep.escape_probability,
                "two_block_estimate": sweep.two_block_estimate,
            })
        except Exception as e:
            results.append({
                "threshold": float(thresh),
                "error": str(e),
            })
    return results


def uncertainty_lemma1(w: np.ndarray, w_hi: np.ndarray) -> np.ndarray:
    """Lemma 1: Row total-variation error eps_i(c) = 1 - W^{hi}_i(c) / W_i."""
    W = w.sum(axis=1)
    W_hi = w_hi.sum(axis=1)
    eps = np.zeros(len(W))
    nonzero = W > 0
    eps[nonzero] = 1.0 - (W_hi[nonzero] / W[nonzero])
    return eps


def uncertainty_lemma2(
    P: np.ndarray,
    a: int,
    b: int,
    r: int,
    eps: np.ndarray,
) -> float:
    """Lemma 2: Accumulated total-variation certificate slack after r steps.

    |d_r(a,b; P') - d_r(a,b; P)| <= sum_{t=0}^{r-1} sum_i |x_t(i)| eps_i
    where x_t = (e_a - e_b) P^t.
    """
    n = P.shape[0]
    x_t = np.zeros(n)
    x_t[a] = 1.0
    x_t[b] = -1.0

    accumulated = 0.0
    for t in range(r):
        accumulated += float((np.abs(x_t) * eps).sum())
        x_t = x_t @ P
    return accumulated


def uncertainty_lemma3_knapsack(
    w_row: np.ndarray,
    w_hi_row: np.ndarray,
) -> float:
    """Lemma 3: Exact / fractional knapsack bound for largest row TV change eps*_i <= eps_i."""
    W = float(w_row.sum())
    if W <= 0:
        return 0.0
    l_row = w_row - w_hi_row
    if (l_row <= 0).all():
        return 0.0

    d = len(w_row)
    if d <= 12:
        # Exact enumeration over 2^d - 1 nonempty subsets S
        best_eps = 0.0
        for mask in range(1, 1 << d):
            s_indices = [idx for idx in range(d) if (mask >> idx) & 1]
            w_S = float(w_row[s_indices].sum())
            w_hi_S = float(w_hi_row[s_indices].sum())
            l_S = float(l_row[s_indices].sum())
            denom = W - l_S
            if denom > 0:
                val = (w_S / W) - (w_hi_S / denom)
                if val > best_eps:
                    best_eps = val
        return best_eps
    else:
        # Fractional relaxation upper bound: sort partners by q_j = w_hi_j / w_j
        with np.errstate(divide="ignore", invalid="ignore"):
            q = np.where(w_row > 0, w_hi_row / w_row, 1.0)
        order = np.argsort(q)
        best_eps = 0.0
        cum_w, cum_whi, cum_l = 0.0, 0.0, 0.0
        for idx in order:
            cum_w += w_row[idx]
            cum_whi += w_hi_row[idx]
            cum_l += l_row[idx]
            denom = W - cum_l
            if denom > 0:
                val = (cum_w / W) - (cum_whi / denom)
                if val > best_eps:
                    best_eps = val
        return best_eps

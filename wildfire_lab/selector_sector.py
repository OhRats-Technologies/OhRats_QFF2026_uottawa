"""Exact XY-QAOA simulation in the cardinality-k sector; no 2**n array."""
from itertools import combinations
import time
import numpy as np
from scipy.optimize import minimize
from wildfire_lab.selection import energies


class Sector:
    def __init__(self, objective):
        start = time.perf_counter()
        self.n = len(objective['linear'])
        self.k = objective['k']
        if self.n % 2:
            raise ValueError('Even-ring mixer requires an even candidate count')
        self.states = np.array(sorted(sum(1 << j for j in subset)
                                      for subset in combinations(range(self.n), self.k)))
        self.bits = ((self.states[:, None] >> np.arange(self.n)) & 1).astype(float)
        self.cost = energies(objective, self.bits)
        self.enumeration_seconds = time.perf_counter()-start
        lookup = {int(state): index for index, state in enumerate(self.states)}
        self.exchanges = []
        for offset in [0, 1]:
            for i in range(offset, self.n, 2):
                j = (i+1) % self.n
                left = np.flatnonzero((self.bits[:, i] == 0) & (self.bits[:, j] == 1))
                right = np.array([lookup[int(self.states[a]) ^ (1 << i) ^ (1 << j)] for a in left])
                self.exchanges.append((left, right))
        self.scale = max(float(np.ptp(self.cost)), 1e-12)
        self.shift = float(self.cost.min())
        self.mixer_setup_seconds = time.perf_counter()-start-self.enumeration_seconds

    def state(self, parameters):
        """Each (gamma,beta) applies exp(-i gamma H), then XXPlusYY(2 beta)."""
        state = np.ones(len(self.cost), dtype=complex) / np.sqrt(len(self.cost))
        for gamma, beta in np.asarray(parameters).reshape(-1, 2):
            state *= np.exp(-1j * gamma * self.cost)
            c, s = np.cos(beta), -1j*np.sin(beta)
            for left, right in self.exchanges:
                a, b = state[left].copy(), state[right].copy()
                state[left], state[right] = c*a+s*b, s*a+c*b
        return state

    def probability(self, parameters):
        probability = np.abs(self.state(parameters))**2
        np.testing.assert_allclose(probability.sum(), 1., atol=1e-10)
        return probability / probability.sum()

    def optimize(self, depth, calls):
        start = time.perf_counter()
        trace = []
        def expected(normalized):
            physical = np.array(normalized).reshape(-1, 2).copy()
            physical[:, 0] /= self.scale
            probability = self.probability(physical.ravel())
            mean = float(probability @ self.cost)
            trace.append(dict(parameters=physical.ravel().tolist(), expected_objective=mean))
            return (mean-self.shift)/self.scale
        result = minimize(expected, np.tile([2., .4], depth), method='COBYLA',
                          bounds=[(0, 2*np.pi), (-np.pi, np.pi)]*depth,
                          options={'maxiter': calls, 'rhobeg': .7})
        physical = result.x.reshape(-1, 2).copy()
        physical[:, 0] /= self.scale
        probability = self.probability(physical.ravel())
        return dict(parameters=physical.ravel().tolist(), probability=probability.tolist(),
                    expected_objective=float(probability @ self.cost), trace=trace,
                    objective_calls=len(trace), sector_state_evaluations=len(trace)+1,
                    seconds=time.perf_counter()-start, success=bool(result.success),
                    message=str(result.message), depth=depth,
                    phase_energy_range=self.scale, uniform_sector_initialization=True)


def sample(sector, probability, shots, seed):
    indices = np.random.default_rng(seed).choice(len(sector.states), size=shots, p=probability)
    unique, count = np.unique(indices, return_counts=True)
    best = int(unique[np.argmin(sector.cost[unique])])
    return dict(counts={str(int(sector.states[a])): int(n) for a, n in zip(unique, count)},
                selected_indices=np.flatnonzero(sector.bits[best]).tolist(),
                objective=float(sector.cost[best]), gap=float(sector.cost[best]-sector.cost.min()),
                optimum_found=bool(np.isclose(sector.cost[best], sector.cost.min(), atol=1e-9, rtol=0)),
                unique_subsets=len(unique), shots=shots, seed=seed)


def diagonal_sqd(objective, sample_record):
    """Real addon projection/solve, on sampled basis only, with diagonal-minimum check."""
    from qiskit_addon_sqd.qubit import project_operator_to_subspace, solve_qubit
    from wildfire_lab.sqd_selection import hamiltonian
    n = len(objective['linear'])
    states = np.array(sorted(int(s) for s in sample_record['counts']))
    bits = ((states[:, None] >> np.arange(n)) & 1).astype(float)
    costs = energies(objective, bits)
    start = time.perf_counter()
    operator = hamiltonian(objective)
    basis = bits[:, ::-1].astype(bool)
    projected = project_operator_to_subspace(basis, operator).tocsr()
    np.testing.assert_allclose(projected.diagonal(), costs, atol=1e-9)
    from scipy.sparse import diags
    off_diagonal = projected-diags(costs)
    maximum = float(abs(off_diagonal).max())
    assert maximum < 1e-9
    if len(states) <= 2:
        lowest = float(costs.min())
    else:
        values, _ = solve_qubit(basis, operator, k=1, which='SA', tol=1e-10,
                                v0=np.ones(len(states)))
        lowest = float(values[0])
    np.testing.assert_allclose(lowest, costs.min(), atol=1e-8)
    return dict(sqd_energy=lowest, sampled_minimum=float(costs.min()),
                basis_size=len(states), projected_off_diagonal_max=maximum,
                seconds=time.perf_counter()-start, solver='qiskit-addon-sqd solve_qubit')

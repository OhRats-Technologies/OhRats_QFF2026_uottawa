"""SQD applicability check for a diagonal feature-selection Hamiltonian."""
import time
import numpy as np
from qiskit.quantum_info import SparsePauliOp
from qiskit_addon_sqd.qubit import solve_qubit, project_operator_to_subspace
from wildfire_lab.selection import ising, energies, configurations, exact_subset


def hamiltonian(objective):
    single, pair, constant = ising(objective)
    n = len(single)
    terms = [('I'*n, constant)]
    for i in range(n):
        label = ['I']*n; label[n-1-i] = 'Z'
        terms.append((''.join(label), single[i]))
        for j in range(i+1, n):
            label = ['I']*n; label[n-1-i] = label[n-1-j] = 'Z'
            terms.append((''.join(label), pair[i,j]))
    return SparsePauliOp.from_list(terms).simplify()


def sampled_subspace(objective, draws):
    bits = configurations(len(objective['linear']))
    indices = np.unique(draws[bits[draws].sum(axis=1) == objective['k']])
    if not len(indices):
        return dict(status='no_feasible_sample', unique_feasible=0)
    costs = energies(objective, bits[indices])
    # SQD represents bitstrings most-significant bit first; objective uses qubit order.
    basis = bits[indices, ::-1].astype(bool)
    operator = hamiltonian(objective)
    start = time.perf_counter()
    projected = project_operator_to_subspace(basis, operator).toarray()
    np.testing.assert_allclose(projected, np.diag(costs), atol=1e-10)
    if len(indices) <= 2:
        lowest = float(np.linalg.eigvalsh(projected).min())
    else:
        values, _ = solve_qubit(basis, operator, k=1, which='SA', tol=1e-12,
                               v0=np.ones(len(indices)))
        lowest = float(values[0])
    exact, optimum = exact_subset(objective)
    np.testing.assert_allclose(lowest, costs.min(), atol=1e-9)
    best = indices[np.argmin(costs)]
    return dict(status='complete', unique_feasible=len(indices),
        sqd_energy=lowest, sampled_minimum=float(costs.min()),
        gap_to_exact=lowest-optimum, exact_subset=exact,
        selected_subset=np.flatnonzero(bits[best]).tolist(),
        sqd_seconds=time.perf_counter()-start,
        eigensolver='dense projected matrix' if len(indices)<=2 else 'addon solve_qubit',
        projected_off_diagonal_max=float(np.max(np.abs(projected-np.diag(costs)))))

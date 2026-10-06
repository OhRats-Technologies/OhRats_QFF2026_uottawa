"""Basis-start XY circuits; omit the first, purely global, cost phase."""
import time
import numpy as np
from scipy.optimize import minimize
from qiskit import QuantumCircuit
from qiskit.circuit.library import XXPlusYYGate
from wildfire_lab.selection import ising


def mix(sector, state, beta):
    cosine, sine = np.cos(beta), -1j*np.sin(beta)
    for left, right in sector.exchanges:
        a, b = state[left].copy(), state[right].copy()
        state[left], state[right] = cosine*a+sine*b, sine*a+cosine*b


def probability(sector, initial_indices, parameters):
    state = np.zeros(len(sector.states), dtype=complex)
    basis = sum(1 << int(index) for index in initial_indices)
    where = np.flatnonzero(sector.states == basis)
    assert len(where) == 1 and len(initial_indices) == sector.k
    state[where[0]] = 1
    mix(sector, state, parameters[0])
    for gamma, beta in np.asarray(parameters[1:]).reshape(-1, 2):
        state *= np.exp(-1j*gamma*sector.cost)
        mix(sector, state, beta)
    probabilities = abs(state)**2
    np.testing.assert_allclose(probabilities.sum(), 1., atol=1e-10)
    return probabilities/probabilities.sum()


def cost_phase(qc, objective, gamma):
    n, k, penalty = len(objective['linear']), objective['k'], objective['penalty']
    reduced = dict(objective,
                   linear=objective['linear']-penalty*(1-2*k),
                   pair=objective['pair']-np.triu(np.full((n, n), 2*penalty), 1),
                   constant=objective['constant']-penalty*k*k)
    single, pair, _ = ising(reduced)
    for index, value in enumerate(single):
        qc.rz(2*gamma*value, index)
    for first in range(n):
        for second in range(first+1, n):
            if pair[first, second]:
                qc.rzz(2*gamma*pair[first, second], first, second)


def circuit(objective, initial_indices, parameters):
    n = len(objective['linear'])
    qc = QuantumCircuit(n)
    qc.x(initial_indices)

    def mixer(beta):
        for offset in [0, 1]:
            for index in range(offset, n, 2):
                qc.append(XXPlusYYGate(2*beta), [index, (index+1) % n])

    mixer(parameters[0])
    for gamma, beta in np.asarray(parameters[1:]).reshape(-1, 2):
        cost_phase(qc, objective, gamma)
        mixer(beta)
    return qc


def optimize(sector, initial_indices, depth, calls):
    started = time.perf_counter()
    trace = []
    bounds = [(-np.pi, np.pi)]+[(0, 2*np.pi), (-np.pi, np.pi)]*(depth-1)

    def physical(normalized):
        values = np.asarray(normalized).copy()
        values[1::2] /= sector.scale
        return values

    def expected(normalized):
        values = physical(normalized)
        p = probability(sector, initial_indices, values)
        value = float(p @ sector.cost)
        trace.append(dict(parameters=values.tolist(), objective=value,
                          feasible=bool(all(lo-1e-7 <= x <= hi+1e-7
                                            for x, (lo, hi) in zip(normalized, bounds)))))
        return (value-sector.shift)/sector.scale

    result = minimize(expected, [.4]+[2., .4]*(depth-1), method='COBYLA', bounds=bounds,
                      options=dict(maxiter=calls, rhobeg=.7, tol=1e-4, catol=1e-6))
    best = min((row for row in trace if row['feasible']), key=lambda row: row['objective'])
    p = probability(sector, initial_indices, best['parameters'])
    return dict(parameters=best['parameters'], probability=p.tolist(),
                expected_objective=best['objective'], initial_indices=initial_indices,
                depth=depth, optimized_parameters=2*depth-1,
                reachable_numerical_states=int((p > 1e-12).sum()),
                optimum_probability=float(p[np.isclose(sector.cost, sector.shift, atol=1e-9, rtol=0)].sum()),
                objective_calls=len(trace), state_evaluations=len(trace)+1, trace=trace,
                optimizer_success=bool(result.success), message=str(result.message),
                seconds=time.perf_counter()-started)

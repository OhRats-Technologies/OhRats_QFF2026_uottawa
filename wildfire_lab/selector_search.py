"""Multi-start XY-QAOA search with a complete, bounded evaluation trace."""
import time
import numpy as np
from scipy.optimize import minimize


def optimize(sector, depth, start_pair, calls):
    started = time.perf_counter()
    trace = []

    def expected(normalized):
        physical = np.asarray(normalized).reshape(-1, 2).copy()
        physical[:, 0] /= sector.scale
        probability = sector.probability(physical.ravel())
        value = float(probability @ sector.cost)
        trace.append(dict(parameters=physical.ravel().tolist(), objective=value))
        return (value - sector.shift) / sector.scale

    result = minimize(
        expected, np.tile(start_pair, depth), method='COBYLA',
        bounds=[(0, 2*np.pi), (-np.pi, np.pi)] * depth,
        options=dict(maxiter=calls, rhobeg=.7, tol=1e-4, catol=1e-6))
    # Retain the best evaluated *feasible* point, rather than assuming the
    # optimizer's last point is best when its evaluation budget expires.
    feasible = [row for row in trace if all(
        -1e-7 <= gamma*sector.scale <= 2*np.pi+1e-7 and
        -np.pi-1e-7 <= beta <= np.pi+1e-7
        for gamma, beta in np.asarray(row['parameters']).reshape(-1, 2))]
    chosen = min(feasible, key=lambda row: row['objective'])
    probability = sector.probability(chosen['parameters'])
    optimum = np.isclose(sector.cost, sector.shift, atol=1e-9, rtol=0)
    return dict(depth=depth, start_pair=start_pair, call_cap=calls,
                objective_calls=len(trace), state_evaluations=len(trace)+1,
                optimizer_success=bool(result.success), message=str(result.message),
                optimizer_final_parameters=result.x.tolist(),
                parameters=chosen['parameters'], expected_objective=chosen['objective'],
                optimum_probability=float(probability[optimum].sum()),
                probability=probability.tolist(), phase_energy_range=sector.scale,
                trace=trace, seconds=time.perf_counter()-started)


def search(sector, plan):
    runs, winners = [], {}
    for depth, calls in plan['optimization_calls'].items():
        indices = []
        for start in plan['starts']:
            indices.append(len(runs))
            runs.append(optimize(sector, int(depth), start, calls))
        # Training objective only. Ties keep the first frozen start.
        winners['optimized'+depth] = min(
            indices, key=lambda index: runs[index]['expected_objective'])
    return runs, winners

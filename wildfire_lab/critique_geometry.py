"""Exact classical cost and measured-kernel repair diagnostics."""
from time import perf_counter_ns
import numpy as np
from wildfire_lab.saved_shot_sweep import sector


def exact_timing(objective, repetitions):
    sector(objective)  # One uncharged warmup; imports and objective construction excluded.
    elapsed = []
    for _ in range(repetitions):
        start = perf_counter_ns()
        states, costs = sector(objective)
        selected = int(states[costs.argmin()])
        elapsed.append((perf_counter_ns()-start)/1e6)
    return dict(pool=len(objective['linear']), cardinality=objective['k'],
        feasible_states=len(states), objective=objective,
        selected_state=selected, exact_cost=float(costs.min()), elapsed_ms=elapsed,
        median_ms=float(np.median(elapsed)), p10_ms=float(np.quantile(elapsed, .1)),
        p90_ms=float(np.quantile(elapsed, .9)),
        scope='Warm allocated feasible-state enumeration, cost evaluation and argmin; excludes objective fitting, imports, QAOA mixer setup and predictor fitting.')


def repairs(result):
    rows = []
    for panel in result['models']:
        ideal = result['models'][panel]['rows'][2]
        for arm in ['raw', 'dd_twirl']:
            measured = {r['repair']: r for r in result['rows'] if r['panel'] == panel and r['arm'] == arm}
            raw = np.asarray(measured['raw']['train_matrix'])
            values, vectors = np.linalg.eigh((raw+raw.T)/2)
            positive = np.flatnonzero(values > 1e-10)
            for repair, kept in [('psd', positive), ('rank4', positive[-4:])]:
                basis = vectors[:, kept]
                gram = (basis*values[kept])@basis.T
                cross = np.asarray(measured['raw']['cross_matrix'])@basis@basis.T
                np.testing.assert_allclose(gram, measured[repair]['train_matrix'], atol=1e-9)
                np.testing.assert_allclose(cross, measured[repair]['cross_matrix'], atol=1e-9)
                rows.append(dict(panel=panel, arm=arm, repair=repair,
                    matrix_size=len(raw), retained_rank=len(kept),
                    raw_minimum_eigenvalue=float(values.min()),
                    raw_negative_eigenvalues=int((values < -1e-10).sum()),
                    raw_negative_spectral_mass=float(-values[values < 0].sum()),
                    relative_gram_change=float(np.linalg.norm(gram-raw)/np.linalg.norm(raw)),
                    relative_cross_change=float(np.linalg.norm(cross-measured['raw']['cross_matrix'])/
                                                np.linalg.norm(measured['raw']['cross_matrix'])),
                    positive_trace_retained=float(values[kept].sum()/values[positive].sum()),
                    positive_frobenius_retained=float((values[kept]**2).sum()/(values[positive]**2).sum()),
                    raw_mae=measured['raw']['mae_ha'], repaired_mae=measured[repair]['mae_ha'],
                    ideal_mae=ideal['mae_ha']))
    return rows

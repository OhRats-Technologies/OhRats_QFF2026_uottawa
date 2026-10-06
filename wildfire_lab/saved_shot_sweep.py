"""Independent shot-sweep arithmetic replay, including every uniform draw."""
import base64
from itertools import combinations
import math
import zlib
import numpy as np


def sector(objective):
    n, k = len(objective['linear']), objective['k']
    states = np.asarray(sorted(sum(1 << i for i in subset) for subset in combinations(range(n), k)))
    bits = ((states[:, None] >> np.arange(n)) & 1).astype(float)
    costs = bits@np.asarray(objective['linear'])+np.einsum(
        'bi,ij,bj->b', bits, np.asarray(objective['pair']), bits)+objective['constant']
    return states, costs


def verify_uniform(control, states, costs):
    budget = control['draw_budget']
    if budget == 0:
        assert control['status'] == 'no_accepted_draws'
        return 0
    indices = np.frombuffer(zlib.decompress(base64.b64decode(control['encoded_indices'])), dtype='<u2')
    indices = indices.reshape(control['replicates'], budget)
    assert np.all(indices < len(states))
    measured = costs[indices]
    minima = measured.min(axis=1)
    best = indices[np.arange(len(indices)), measured.argmin(axis=1)]
    np.testing.assert_allclose(minima, control['minima'])
    np.testing.assert_allclose(minima-costs.min(), control['gaps'])
    assert states[best].tolist() == control['selected_states']
    assert [len(np.unique(row)) for row in indices] == control['unique_counts']
    assert int(np.isclose(minima, costs.min(), atol=1e-9, rtol=0).sum()) == control['optimum_trials']
    np.testing.assert_allclose(np.mean(minima-costs.min()), control['mean_gap'])
    probability = np.isclose(costs, costs.min(), atol=1e-9, rtol=0).mean()
    expected = 1. if probability == 1 else -math.expm1(budget*math.log1p(-probability))
    np.testing.assert_allclose(expected, control['exact_uniform_optimum_probability'])
    return indices.size


def verify(result, plan):
    objectives = {r['specification']['pool_size']: r['objective_specification'] for r in result['rows']}
    sectors = {n: sector(objective) for n, objective in objectives.items()}
    draws = 0
    for key, control in result['uniform_controls'].items():
        n, budget = map(int, key.split('-'))
        assert control['draw_budget'] == budget
        draws += verify_uniform(control, *sectors[n])
    assert draws == result['classical_uniform_draws']
    observed = set()
    for row in result['rows']:
        records = result['compilation'][row['job_label']]
        index = records.index(row['specification'])
        assert result['physical_counts'][row['job_label']][index] == row['measured_counts']
        assert sum(row['measured_counts'].values()) == row['shots']
        success, count = row['feasible_shots'], row['shots']
        p, z = success/count, 1.959963984540054
        denominator = 1+z*z/count
        center = (p+z*z/(2*count))/denominator
        radius = z*math.sqrt(p*(1-p)/count+z*z/(4*count*count))/denominator
        np.testing.assert_allclose([max(0., center-radius), min(1., center+radius)], row['wilson95'])
        np.testing.assert_allclose(p, row['feasible_fraction'])
        n = row['specification']['pool_size']
        np.testing.assert_allclose(row['exact_objective'], sectors[n][1].min())
        if row['specification']['kind'] == 'confirmation':
            for label, budget in [('physical', count), ('accepted', success)]:
                assert row['uniform_controls'][label] == f'{n}-{budget}'
            observed.add((n, row['arm'], count))
    assert observed == {(n, arm, shots) for n in [10, 16, 20]
                        for arm in ['raw', 'dd_twirl'] for shots in plan['shots']}
    assert result['hardware_jobs'] == 6
    return draws

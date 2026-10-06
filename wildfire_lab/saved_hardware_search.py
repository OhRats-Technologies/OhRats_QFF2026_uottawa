"""Offline arithmetic audit of published hardware search and confirmation."""
import hashlib
import json
from zipfile import ZipFile
import numpy as np
from wildfire_lab.saved_search import prediction


def measured(row, objective):
    n = len(objective['linear'])
    states = np.asarray([int(key.replace(' ', ''), 2) for key in row['measured_counts']])
    frequency = np.asarray(list(row['measured_counts'].values()))
    bits = ((states[:, None] >> np.arange(n)) & 1).astype(float)
    costs = bits@np.asarray(objective['linear'])+np.einsum(
        'bi,ij,bj->b', bits, np.asarray(objective['pair']), bits)+objective['constant']
    valid = bits.sum(axis=1) == objective['k']
    assert frequency.sum() == row['shots']
    assert frequency[valid].sum() == row['feasible_shots']
    np.testing.assert_allclose(frequency@costs/frequency.sum(), row['unconditional_expected_objective'])
    expected_counts = {str(int(s)): int(c) for s, c, v in zip(states, frequency, valid) if v}
    assert expected_counts == row['feasible_counts']
    if valid.any():
        np.testing.assert_allclose(costs[valid].min(), row['objective'])
        np.testing.assert_allclose(frequency[valid]@costs[valid]/frequency[valid].sum(),
                                   row['conditional_expected_objective'])
        index = min(np.flatnonzero(valid), key=lambda i: (costs[i], states[i]))
        assert np.flatnonzero(bits[index]).tolist() == row['selected_indices']
    else:
        assert row['conditional_expected_objective'] is None


def kernel_variants(result, panel, arm):
    """Independent dense calibration inversion and kernel projection arithmetic."""
    original = result['models'][panel]['rows'][2]
    n, m = len(original['scaled_train']), len(original['scaled_cross'])
    physical = result['physical_counts'][arm]
    rows = [c for r, c in zip(result['compilation'], physical, strict=True) if r.get('model') == panel]
    calibration = []
    for counts, prepared in zip(physical[-2:], [0, 1]):
        frequencies = np.asarray(list(counts.values()))
        states = np.asarray([int(k.replace(' ', ''), 2) for k in counts])
        bits = (states[:, None] >> np.arange(4)) & 1
        calibration.append(frequencies@(bits if prepared == 0 else 1-bits)/frequencies.sum())
    p01, p10 = calibration
    channels = np.asarray([[[1-a, b], [a, 1-b]] for a, b in zip(p01, p10)])
    np.testing.assert_allclose(channels, result['calibrations'][arm]['channels'])
    assignment = np.ones((16, 16))
    for q, channel in enumerate(channels):
        observed = (np.arange(16)[:, None] >> q) & 1
        actual = (np.arange(16)[None, :] >> q) & 1
        assignment *= channel[observed, actual]
    values, corrected = [], []
    for counts in rows:
        frequency = np.zeros(16)
        for bits, count in counts.items():
            frequency[int(bits.replace(' ', ''), 2)] += count
        vector = frequency/frequency.sum()
        values.append(vector[0])
        corrected.append(float(np.clip(np.linalg.solve(assignment, vector)[0], 0, 1)))
    def assemble(v):
        gram = np.zeros((n, n))
        i, j = np.triu_indices(n)
        gram[i, j] = v[:len(i)]
        gram[j, i] = gram[i, j]
        return gram, np.asarray(v[len(i):]).reshape(m, n)
    def project(pair, rank=None):
        gram, cross = pair
        values, vectors = np.linalg.eigh((gram+gram.T)/2)
        kept = np.flatnonzero(values > 1e-10)
        if rank is not None:
            kept = kept[-rank:]
        basis = vectors[:, kept]
        return (basis*values[kept])@basis.T, cross@basis@basis.T
    raw, readout = assemble(values), assemble(corrected)
    return dict(raw=raw, psd=project(raw), rank4=project(raw, 4), readout=readout,
                readout_psd=project(readout), readout_rank4=project(readout, 4))


def collect(root, study):
    index = json.loads((root/f'docs/results/{study}.json').read_text())
    bundle = root/index['bundle']
    assert hashlib.sha256(bundle.read_bytes()).hexdigest() == index['bundle_sha256']
    with ZipFile(bundle) as archive:
        raw = archive.read('evidence.json')
    assert hashlib.sha256(raw).hexdigest() == index['evidence_sha256']
    evidence = json.loads(raw)
    result = evidence['analysis']
    equations, count_rows = 0, 0
    if result.get('study', '').startswith('shot-sweep-'):
        from wildfire_lab.saved_shot_sweep import verify
        verify(result, evidence['plan'])
    if result.get('stage') == 'hardware_exploration':
        physical_shots = 0
        for cohort in result['cohorts']:
            for row in cohort['rows']:
                measured(row, cohort['objective'])
                count_rows += 1
                physical_shots += row['shots']
            physical_shots += sum(sum(r['counts'].values()) for r in cohort['calibration'])
            eligible = [r for r in cohort['rows'] if r['specification']['kind'] == 'candidate'
                        and r['feasible_shots'] > 0]
            if eligible:
                chosen = min(eligible, key=lambda r: (r['unconditional_expected_objective'], r['index']))
                assert chosen['index'] == cohort['winner_index']
                np.testing.assert_allclose(chosen['objective'], cohort['winner_sqd']['sqd_energy'])
        assert physical_shots == result['physical_shots']
    elif 'models' not in result:
        for row in result['rows']:
            measured(row, row['objective_specification'])
            if row['feasible_shots']:
                np.testing.assert_allclose(row['sqd']['sqd_energy'], row['objective'])
                np.testing.assert_allclose(row['gap_to_exact'], row['objective']-row['exact_objective'])
            count_rows += 1
    else:
        reconstructed = {(panel, arm): kernel_variants(result, panel, arm)
                         for panel in result['models'] for arm in result['physical_counts']}
        for model in result['models'].values():
            for row in model['rows']:
                inputs = row['scaled_cross'] if row['specification']['model'] == 'ridge' else row['cross_matrix']
                prediction(row, row['preprocessing'], inputs)
                equations += 1
            for kind, selected in model['tuning']['chosen'].items():
                candidates = [r for r in model['tuning']['candidates'] if r['specification']['model'] == kind]
                assert min(candidates, key=lambda r: r['mae_ha'])['specification'] == selected
        for row in result['rows']:
            model = result['models'][row['panel']]
            prediction(row, model['preprocessing'], row['cross_matrix'])
            assert row['specification'] == model['tuning']['chosen']['qsvr']
            gram, cross = reconstructed[row['panel'], row['arm']][row['repair']]
            np.testing.assert_allclose(gram, row['train_matrix'], atol=1e-7)
            np.testing.assert_allclose(cross, row['cross_matrix'], atol=1e-7)
            equations += 1
    if 'physical_counts' in result:
        total = sum(sum(c.values()) for arm in result['physical_counts'].values() for c in arm)
        assert total == result['physical_shots']
    assert result['final_test_accessed'] is False
    np.testing.assert_allclose(sum(r['charged_seconds'] for r in result.get('resources', {}).values()),
        result['charged_seconds']) if result.get('resources') else None
    return dict(status='passed', study=study, prediction_equations=equations,
                measured_count_rows=count_rows, physical_shots=result['physical_shots'],
                charged_seconds=result['charged_seconds'], predictor_fits=0,
                new_quantum_states=0, new_samples=0, hardware_jobs_submitted=0)

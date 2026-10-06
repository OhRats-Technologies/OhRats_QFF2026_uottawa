"""Validate saved context-pilot evidence without fitting or simulating anything."""
import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    directory = ROOT / '.cache/wildfire/coarse-height-context-v1'
    result_path = directory / 'result.json'
    result = json.loads(result_path.read_text())
    intent = json.loads((directory / 'intent.json').read_text())
    plan = intent['plan']
    for name, expected in {**plan['data_hashes'], **intent['runner_hashes']}.items():
        assert digest(ROOT / name) == expected, name
    assert (ROOT / 'docs/results/coarse-height-context.json').read_bytes() == result_path.read_bytes()
    original = pd.read_csv(ROOT / 'docs/data/annual_training.csv')
    table = pd.read_csv(directory / 'annual.csv')
    assert table.year.tolist() == list(range(1988, 2019))
    np.testing.assert_allclose(table[original.columns], original, rtol=0, atol=1e-10)
    context = json.loads((ROOT / 'docs/data/scanfi_height_context.json').read_text())
    epochs = {row['year']: row['common_mean_height_m'] for row in context['rows']}
    expected_epochs = [max(epoch for epoch in epochs if epoch < year) for year in table.year]
    assert table.height_epoch.tolist() == expected_epochs
    np.testing.assert_allclose(table.height, [epochs[e] for e in expected_epochs])
    assert table.zero.eq(0).all()
    pair_count = 0
    for fold_id, fold in enumerate(plan['folds']):
        truth = table[table.year.between(fold[2], fold[3])]
        rows = [row for row in result['results'] if row['fold'] == fold]
        assert len(rows) == 13
        for row in rows:
            assert row['years'] == truth.year.tolist()
            actual, prediction = np.array(row['actual_ha']), np.array(row['predicted_ha'])
            np.testing.assert_allclose(actual, truth.mean_reported_size_ha)
            assert np.isfinite(prediction).all() and (prediction >= 0).all()
            error = prediction - actual
            for metric, value in [('mae_ha', abs(error).mean()),
                                  ('rmse_ha', np.sqrt(np.mean(error ** 2))),
                                  ('bias_ha', error.mean())]:
                np.testing.assert_allclose(row[metric], value, rtol=0, atol=1e-10)
        grams = {}
        for condition in plan['conditions']:
            path = directory / f'fold-{fold_id}' / condition / 'kernel'
            receipt = json.loads((path / 'receipt.json').read_text())
            assert digest(path / 'matrices.npz') == receipt['matrix_sha256']
            pair_count += receipt['pair_circuits']
            with np.load(path / 'matrices.npz') as saved:
                gram, cross = saved['gram'], saved['cross']
                assert gram.shape == (fold[1] - fold[0] + 1,) * 2
                assert cross.shape == (4, len(gram))
                np.testing.assert_allclose(gram, gram.T, atol=1e-12)
                np.testing.assert_allclose(np.diag(gram), 1, atol=1e-12)
                assert np.linalg.eigvalsh(gram).min() > -1e-8
                grams[condition] = gram.copy()
        width = np.max(abs(grams['weather_four'] - grams['weather_plus_zero']))
        np.testing.assert_allclose(width, result['width_control'][fold_id]['maximum_kernel_change_from_zero_qubit'])
        for model in ['ridge', 'rbf', 'qsvr']:
            by_condition = {r['condition']: r for r in rows if r['model'] == model}
            contrast = next(r for r in result['contrasts'] if r['fold'] == fold and r['model'] == model)
            for key, left, right in [('height_minus_zero_mae', 'weather_plus_height', 'weather_plus_zero'),
                                      ('height_minus_year_mae', 'weather_plus_height', 'weather_plus_year'),
                                      ('zero_minus_four_mae', 'weather_plus_zero', 'weather_four')]:
                np.testing.assert_allclose(contrast[key], by_condition[left]['mae_ha'] - by_condition[right]['mae_ha'])
            if model != 'qsvr':
                np.testing.assert_allclose(by_condition['weather_four']['predicted_ha'],
                                           by_condition['weather_plus_zero']['predicted_ha'], atol=1e-10)
    assert pair_count == result['pair_circuits'] == 4204
    assert result['model_fits'] == plan['budget']['model_fits'] == 36
    assert result['hardware_jobs'] == 0
    receipt = {'status': 'verified', 'result_sha256': digest(result_path),
               'saved_predictions': 156, 'saved_kernels': 12, 'pair_circuits_in_original_run': pair_count,
               'new_fits': 0, 'new_quantum_states': 0, 'hardware_jobs': 0,
               'checks': ['source/code hashes', 'strict prior-epoch join', 'years/truth',
                          'saved prediction metrics', 'matrix hashes/PSD', 'contrasts', 'width placebo']}
    (ROOT / 'docs/data/coarse_height_verification.json').write_text(json.dumps(receipt, indent=2) + '\n')
    print(json.dumps(receipt, indent=2))


if __name__ == '__main__':
    main()

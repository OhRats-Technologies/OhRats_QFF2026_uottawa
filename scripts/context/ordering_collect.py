"""Check saved amplitudes, preprocessing and metrics without quantum execution."""
import json

import numpy as np
import pandas as pd

from ordering import ROOT, PLAN, sha
from ordering_math import fidelity, rbf, statistics, basis_indices


def collect(output):
    plan = json.loads(PLAN.read_text())
    result = json.loads((output / 'result.json').read_text())
    assert result['plan_sha256'] == sha(PLAN)
    for path, expected in result['source_sha256'].items():
        assert sha(ROOT / path) == expected, path
    assert result['arrays_sha256'] == sha(output / 'arrays.npz')
    arrays = np.load(output / 'arrays.npz', allow_pickle=False)
    raw = arrays['raw']
    original = pd.read_csv(ROOT / plan['input'], usecols=['year', *plan['features']])
    assert np.allclose(original[plan['features']].to_numpy(), raw, equal_nan=True)
    imputed = np.where(np.isnan(raw), np.nanmedian(raw, axis=0), raw)
    expected_z = (imputed - imputed.mean(axis=0)) / imputed.std(axis=0)
    assert np.max(np.abs(expected_z - arrays['z'])) < plan['tolerance']
    assert arrays['years'].tolist() == result['years'] == list(range(1988, 2019))
    distances = np.sum((expected_z[:, None] - expected_z[None, :]) ** 2, axis=-1)
    gamma = 1 / np.median(distances[distances > 0])
    assert abs(gamma - result['gamma']) < plan['tolerance']
    classical = rbf(expected_z, gamma)
    assert np.max(np.abs(classical - arrays['rbf_reference'])) < plan['tolerance']
    checked = []
    for row in result['rows']:
        key = row['key']
        states, matrix = arrays[key + '_states'], arrays[key + '_kernel']
        reference_key = f"{row['graph']}_d{row['denominator']}_identity"
        reference = arrays[reference_key + '_kernel']
        assert np.max(np.abs(fidelity(states) - matrix)) < plan['tolerance']
        assert np.max(np.abs(np.sum(abs(states) ** 2, axis=1) - 1)) < plan['tolerance']
        stats = statistics(matrix, reference)
        assert all(abs(stats[name] - row[name]) < plan['tolerance'] for name in stats)
        indices = row['order']['indices']
        error = float(np.max(np.abs(states - arrays[reference_key + '_states'][:, basis_indices(indices)])))
        assert abs(error - row['state_relabelling_error']) < plan['tolerance']
        if row['expected_symmetry']:
            assert error < plan['tolerance'] and stats['max_entry_change'] < plan['tolerance']
        rbf_error = float(np.max(np.abs(rbf(expected_z[:, indices], gamma) - classical)))
        assert rbf_error < plan['tolerance']
        checked.append({'key': key, 'metrics_and_state_relabelling_match': True})
    assert len(checked) == 16 and result['statevector_preparations'] == 496
    receipt = {
        'status': 'passed', 'result_sha256': sha(output / 'result.json'),
        'plan_sha256': sha(PLAN), 'arrays_sha256': result['arrays_sha256'],
        'checked': checked, 'new_statevector_preparations': 0, 'predictor_fits': 0, 'hardware_jobs': 0,
        'scope': 'Saved preprocessing/state/matrix arithmetic. Circuit generation is not repeated; source hashes '
                 'and normalization are checked. No labels, test years, order ranking or predictive claims.',
    }
    (output / 'collection.json').write_text(json.dumps(receipt, indent=2) + '\n')
    print(json.dumps({'status': 'passed', 'checked_conditions': len(checked), 'new_states': 0, 'fits': 0}))

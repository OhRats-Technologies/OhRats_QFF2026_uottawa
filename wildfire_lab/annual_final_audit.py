"""Collect frozen annual states/matrices without fits, shots or new quantum states."""

import json

import numpy as np
import pandas as pd
from sklearn.metrics.pairwise import rbf_kernel

from wildfire_lab.annual_data import digest
from wildfire_lab.annual_final_protocol import current_code


def read(path):
    return json.loads(path.read_text())


def checked_array(path, expected):
    if digest(path) != expected:
        raise ValueError(f'Saved matrix changed: {path.name}')
    return np.load(path)


def normalized(values, scaling):
    return (np.where(np.isnan(values), scaling['medians'], values)
            - np.array(scaling['means'])) / np.array(scaling['scales'])


def gram_diagnostic(entry, gram, cross):
    np.testing.assert_allclose(gram, gram.T, atol=1e-10)
    np.testing.assert_allclose(np.diag(gram), 1., atol=1e-10)
    if gram.shape != (31, 31) or cross.shape != (6, 31):
        raise ValueError('Final annual matrix dimensions differ from observation unit')
    eigenvalues = np.linalg.eigvalsh(gram)
    if eigenvalues.min() < -1e-8 or not np.isfinite(cross).all():
        raise ValueError('Invalid exact annual kernel')
    probabilities = np.maximum(eigenvalues, 0) / eigenvalues.sum()
    positive = probabilities[probabilities > 0]
    off_diagonal = gram[~np.eye(len(gram), dtype=bool)]
    return dict(id=entry['id'], kind=entry['kind'], inputs=len(entry['features']),
                params=entry['params'], eigenvalues=eigenvalues.tolist(),
                minimum_eigenvalue=float(eigenvalues.min()),
                maximum_eigenvalue=float(eigenvalues.max()),
                condition_number=float(np.linalg.cond(gram)),
                effective_rank=float(np.exp(-np.sum(positive * np.log(positive)))),
                off_diagonal_mean=float(off_diagonal.mean()),
                off_diagonal_std=float(off_diagonal.std()), cross_mean=float(cross.mean()))


def collect(root, run, plan_path):
    plan, receipt = read(plan_path), read(run / 'training_receipt.json')
    if digest(plan_path) != receipt['plan_sha256'] or current_code(root) != receipt['code_sha256']:
        raise ValueError('Final code/plan changed after frozen training')
    if digest(run / 'training.json') != receipt['training_sha256']:
        raise ValueError('Frozen learned states changed')
    training, outcome = read(run / 'training.json'), read(run / 'evaluation/outcome.json')
    if outcome['training_receipt'] != receipt or outcome['predictor_fits'] != 0:
        raise ValueError('Final evaluation did not use frozen state')
    train_path, test_path = root / plan['training_dataset'], run / 'evaluation/data/annual.csv'
    if digest(train_path) != plan['training_sha256']:
        raise ValueError('Training table changed')
    if digest(test_path) != outcome['dataset_manifest']['table_sha256']:
        raise ValueError('Reused evaluation table changed')
    train, test = pd.read_csv(train_path), pd.read_csv(test_path)
    if train.year.tolist() != list(range(1988, 2019)) or test.year.tolist() != list(range(2019, 2025)):
        raise ValueError('Unexpected province-year observations')
    actual = test.mean_reported_size_ha.to_numpy()
    records = outcome['main_results'] + outcome['crossed_results']
    results = {record['id']: record for record in records}
    models = training['main_models'] + training['crossed_models']
    if len(results) != len(records) or set(results) != {model['id'] for model in models}:
        raise ValueError('Final model/result identities differ')
    matrices, diagnostics = {}, []
    cross_receipts = {entry['id']: entry for entry in outcome['cross_resources']}
    for entry in training['kernels']:
        identifier = entry['id']
        saved = checked_array(run / 'kernels' / identifier / 'matrix.npz', entry['matrix_sha256'])
        receipt_cross = cross_receipts[identifier]
        cross = checked_array(run / 'evaluation/cross' / identifier / 'cross.npz',
                              receipt_cross['matrix_sha256'])
        raw = train[entry['features']].to_numpy()
        np.testing.assert_allclose(entry['scaling']['medians'], np.nanmedian(raw, axis=0))
        filled = np.where(np.isnan(raw), entry['scaling']['medians'], raw)
        np.testing.assert_allclose(entry['scaling']['means'], filled.mean(axis=0))
        np.testing.assert_allclose(entry['scaling']['scales'], filled.std(axis=0))
        x, z = normalized(raw, entry['scaling']), normalized(test[entry['features']].to_numpy(), entry['scaling'])
        if entry['kind'] == 'quantum':
            amplitude = entry['params']['amplitude']
            np.testing.assert_allclose(saved['train_angles'], amplitude * np.tanh(x / 2))
            np.testing.assert_allclose(cross['cross_angles'], amplitude * np.tanh(z / 2))
        else:
            np.testing.assert_allclose(saved['gram'], rbf_kernel(x, gamma=entry['gamma']))
            np.testing.assert_allclose(cross['cross'], rbf_kernel(z, x, gamma=entry['gamma']))
        matrices[identifier] = cross['cross']
        diagnostics.append(gram_diagnostic(entry, saved['gram'], cross['cross']))
    checked, tuning_records = 0, 0
    for model in models:
        row = results[model['id']]
        if model.get('status', 'complete') != 'complete':
            if row['status'] != model['status']:
                raise ValueError('Selector failure status changed')
            continue
        if model['kind'] == 'constant':
            prediction = np.repeat(model['prediction_ha'], len(test))
        elif model['kind'] == 'trend':
            prediction = np.maximum(0, np.polyval(model['coefficients'], test.year))
        else:
            state, scaling = model['state'], model['scaling']
            x = matrices[model['kernel_id']] if model['kind'] in ['quantum', 'rbf'] else normalized(test[model['features']].to_numpy(), scaling)
            value = (x[:, state['support']] @ state['dual'] if model['kind'] in ['quantum', 'rbf']
                     else x @ state['coefficients']) + state['intercept']
            prediction = np.maximum(0, np.expm1(scaling['target_mean'] + scaling['target_scale'] * value))
        np.testing.assert_allclose(row['predicted_ha'], prediction, rtol=1e-10, atol=1e-8)
        np.testing.assert_allclose(row['actual_ha'], actual, rtol=0, atol=0)
        delta = prediction - actual
        for key, value in dict(mae_ha=np.abs(delta).mean(), rmse_ha=np.sqrt((delta ** 2).mean()), bias_ha=delta.mean()).items():
            np.testing.assert_allclose(row[key], value, rtol=1e-10, atol=1e-8)
        np.testing.assert_allclose(row['absolute_errors_ha'], np.abs(delta))
        if 'inner_tuning' in model:
            chosen = min(model['inner_tuning'], key=lambda record: record['mae_ha'])
            params = chosen.get('params', chosen)
            for name, value in model['params'].items():
                if params[name] != value:
                    raise ValueError('Main hyperparameters do not minimize frozen inner score')
            if model['kind'] == 'quantum' and (model['reps'] != chosen['reps'] or model['amplitude'] != chosen['amplitude']):
                raise ValueError('Feature map differs from selected training configuration')
            tuning_records += len(model['inner_tuning'])
        checked += 1
    if training['training_quantum_matrices'] > plan['budget']['maximum_training_quantum_matrices']:
        raise ValueError('Quantum training budget exceeded')
    return dict(study='annual-final-audit', status='passed', outcome_sha256=digest(run / 'evaluation/outcome.json'),
                training_sha256=receipt['training_sha256'], plan_sha256=receipt['plan_sha256'],
                training_table_sha256=digest(train_path), test_table_sha256=digest(test_path),
                prediction_records_checked=checked, inner_candidates_checked=tuning_records,
                kernel_records_checked=len(diagnostics), kernel_diagnostics=diagnostics,
                collection_predictor_fits=0, new_quantum_states=0, hardware_jobs=0,
                reused_evaluation_years=True)

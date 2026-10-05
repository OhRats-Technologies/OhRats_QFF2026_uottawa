"""Equal-budget inner kernel selection on the same annual chronological folds."""

import json
import itertools
from pathlib import Path

import numpy as np
from sklearn.model_selection import TimeSeriesSplit
from sklearn.svm import SVR

from wildfire_lab.annual_classical import errors, gamma, inverse, scale
from wildfire_lab.annual_data import digest


def choose_quantum(rows, fold):
    candidates = [row for row in rows if row['fold'] == fold]
    if len(candidates) != 4:
        raise ValueError('Expected all four frozen circuit configurations')
    return min(candidates, key=lambda row: min(r['mae_ha'] for r in row['inner_tuning']))


def predict_rbf(x, cross, y, params):
    fit_x, valid_x, fit_y, scaler = scale(x, cross, y)
    model = SVR(kernel='rbf', C=params['C'], epsilon=params['epsilon'],
                gamma=gamma(fit_x) * params['gamma_multiplier'])
    model.fit(fit_x, fit_y)
    return inverse(model.predict(valid_x), scaler)


def rbf_candidates(plan, parent):
    return [dict(C=c, epsilon=e, gamma_multiplier=g) for g, c, e in itertools.product(
        plan['rbf_gamma_multipliers'], parent['svr_grid']['C'], parent['svr_grid']['epsilon'])]


def screen(table, plan, parent, quantum_parents):
    results = []
    for fold in parent['development_folds']:
        first, last, valid_first, valid_last = fold
        train = table[table.year.between(first, last)]
        validation = table[table.year.between(valid_first, valid_last)]
        y, actual = train.mean_reported_size_ha.to_numpy(), validation.mean_reported_size_ha.to_numpy()
        for qubits, features in [(4, parent['four_feature_subset']), (10, parent['features'])]:
            x, cross = train[features].to_numpy(), validation[features].to_numpy()
            tuning = []
            for params in rbf_candidates(plan, parent):
                targets, predictions = [], []
                for fit, valid in TimeSeriesSplit(n_splits=3).split(x):
                    targets.extend(y[valid])
                    predictions.extend(predict_rbf(x[fit], x[valid], y[fit], params))
                tuning.append(dict(params=params, **errors(np.array(targets), np.array(predictions))))
            selected = min(tuning, key=lambda row: row['mae_ha'])
            prediction = predict_rbf(x, cross, y, selected['params'])
            result = dict(model='matched_rbf_svr', qubits=None, features=features, fold=fold,
                          candidates=36, chosen=selected['params'], inner_tuning=tuning,
                          selected_inner_mae=selected['mae_ha'], years=validation.year.tolist(),
                          actual_ha=actual.tolist(), predicted_ha=prediction.tolist(),
                          **errors(actual, prediction))
            results.append(result)
            chosen = choose_quantum(quantum_parents[qubits]['results'], fold)
            if chosen['years'] != validation.year.tolist() or not np.allclose(chosen['actual_ha'], actual):
                raise ValueError('Quantum parent uses different validation years or targets')
            selected_inner = min(chosen['inner_tuning'], key=lambda row: row['mae_ha'])
            if selected_inner['params'] != chosen['chosen']:
                raise ValueError('Quantum parent hyperparameters disagree with inner selection')
            quantum_result = dict(chosen, model='matched_fidelity_svr', candidates=36,
                                  selected_inner_mae=selected_inner['mae_ha'],
                                  reused_quantum_parent=True)
            results.append(quantum_result)
    return results


def load_inputs(dataset, plan_path, root):
    import pandas as pd
    plan = json.loads(Path(plan_path).read_text())
    parent_path = root / 'experiments/annual_qsvr.json'
    if digest(parent_path) != plan['parent_plan_sha256'] or digest(dataset) != plan['dataset_sha256']:
        raise ValueError('Frozen annual parent plan or dataset changed')
    parent = json.loads(parent_path.read_text())
    quantum = {}
    for path, expected in zip(plan['quantum_parent_receipts'], plan['quantum_parent_sha256']):
        if digest(root / path) != expected:
            raise ValueError('Quantum parent receipt changed')
        outcome = json.loads((root / path).read_text())
        if outcome['dataset_sha256'] != plan['dataset_sha256']:
            raise ValueError('Quantum parent uses different annual data')
        quantum[outcome['results'][0]['qubits']] = outcome
    table = pd.read_csv(dataset)
    if len(table) != 31 or table.year.tolist() != list(range(1988, 2019)):
        raise ValueError('Expected the 31 frozen training years')
    return table, plan, parent, quantum

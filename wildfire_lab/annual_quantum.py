"""Actual fidelity-kernel SVR on annual outcomes; reuse matrices across tuning."""

import itertools
import json
from pathlib import Path
import time

import numpy as np
from sklearn.model_selection import TimeSeriesSplit
from qiskit_machine_learning.algorithms import QSVR

from wildfire_lab.annual_classical import errors, grid, inverse, scale
from wildfire_lab.annual_data import digest
from wildfire_lab.library_kernel import matrices


def kernel_fold(train_x, cross_x, train_y, directory, reps, amplitude):
    x, cross, y, y_scaler = scale(train_x, cross_x, train_y)
    angles, cross_angles = amplitude * np.tanh(x / 2), amplitude * np.tanh(cross / 2)
    gram, cross_gram, resources = matrices(angles, cross_angles, reps=reps)
    minimum = float(np.linalg.eigvalsh((gram + gram.T) / 2).min())
    if minimum < -1e-8:
        raise ValueError('Exact fidelity Gram matrix is not positive semidefinite')
    directory.mkdir(parents=True)
    np.savez(directory / 'matrices.npz', gram=gram, cross=cross_gram,
             train_angles=angles, cross_angles=cross_angles)
    receipt = dict(**resources, matrix_sha256=digest(directory / 'matrices.npz'),
                   raw_min_eigenvalue=minimum, train_rows=len(x), validation_rows=len(cross),
                   qubits=x.shape[1], reps=reps, amplitude=amplitude)
    (directory / 'receipt.json').write_text(json.dumps(receipt, indent=2) + '\n')
    return gram, cross_gram, y, y_scaler, receipt


def predict_cached(gram, cross, y, y_scaler, params):
    model = QSVR(quantum_kernel='precomputed', **params)
    model.fit(gram, y)
    return inverse(model.predict(cross), y_scaler)


def screen(table, plan, output, qubits):
    output = Path(output)
    if output.exists():
        raise FileExistsError(output)
    output.mkdir(parents=True)
    feature_names = plan['four_feature_subset'] if qubits == 4 else plan['features']
    results, resource_records = [], []
    for outer, (first, last, valid_first, valid_last) in enumerate(plan['development_folds']):
        train = table[table.year.between(first, last)]
        validation = table[table.year.between(valid_first, valid_last)]
        x, cross = train[feature_names].to_numpy(), validation[feature_names].to_numpy()
        y, actual = train.mean_reported_size_ha.to_numpy(), validation.mean_reported_size_ha.to_numpy()
        for reps, amplitude in itertools.product(plan['quantum']['reps'],
                                                 plan['quantum']['angle_amplitudes']):
            directory = output / f'fold-{outer}' / f'reps-{reps}-angle-{amplitude:.6f}'
            inner_records = []
            for inner, (fit, valid) in enumerate(TimeSeriesSplit(n_splits=3).split(x)):
                kernel = kernel_fold(x[fit], x[valid], y[fit], directory / f'inner-{inner}',
                                     reps, amplitude)
                resource_records.append(kernel[-1])
                inner_records.append((kernel[:4], y[valid]))
            tuning = []
            for params in grid('rbf', plan):
                predictions, targets = [], []
                for kernel, target in inner_records:
                    predictions.extend(predict_cached(*kernel, params))
                    targets.extend(target)
                tuning.append(dict(params=params, **errors(np.array(targets), np.array(predictions))))
            chosen = min(tuning, key=lambda row: row['mae_ha'])['params']
            kernel = kernel_fold(x, cross, y, directory / 'outer', reps, amplitude)
            resource_records.append(kernel[-1])
            prediction = predict_cached(*kernel[:4], chosen)
            result = dict(model='fidelity_svr', features=feature_names, qubits=qubits,
                          reps=reps, amplitude=amplitude, chosen=chosen, inner_tuning=tuning,
                          fold=[first, last, valid_first, valid_last], years=validation.year.tolist(),
                          actual_ha=actual.tolist(), predicted_ha=prediction.tolist(),
                          **errors(actual, prediction))
            results.append(result)
            (output / 'progress.json').write_text(json.dumps(dict(results=results), indent=2) + '\n')
            print(json.dumps(dict(completed=len(results), total=12, qubits=qubits,
                                  fold=outer, reps=reps, amplitude=amplitude,
                                  mae_ha=result['mae_ha'])), flush=True)
    return results, resource_records

"""Recompute annual metrics and replay cached-kernel predictions without new circuits."""

import json
from pathlib import Path

import numpy as np
import pandas as pd

from wildfire_lab.annual_classical import errors, fit_predict, scale
from wildfire_lab.annual_data import digest, prepare
from wildfire_lab.annual_quantum import predict_cached


def validate_metrics(results):
    checked = 0
    for row in results:
        if row.get('status', 'complete') != 'complete':
            continue
        actual, prediction = np.array(row['actual_ha']), np.array(row['predicted_ha'])
        if not np.isfinite(prediction).all() or (prediction < 0).any():
            raise ValueError('Annual prediction must be finite and nonnegative')
        for name, value in errors(actual, prediction).items():
            np.testing.assert_allclose(row[name], value, rtol=1e-10, atol=1e-9)
        checked += 1
    return checked


def matrix_diagnostic(directory, x, cross, y, reps, amplitude):
    receipt = json.loads((directory / 'receipt.json').read_text())
    path = directory / 'matrices.npz'
    if digest(path) != receipt['matrix_sha256']:
        raise ValueError('Saved annual kernel changed')
    saved = np.load(path)
    fit_x, valid_x, fit_y, scaler = scale(x, cross, y)
    np.testing.assert_allclose(saved['train_angles'], amplitude * np.tanh(fit_x / 2))
    np.testing.assert_allclose(saved['cross_angles'], amplitude * np.tanh(valid_x / 2))
    gram, cross_gram = saved['gram'], saved['cross']
    np.testing.assert_allclose(gram, gram.T, atol=1e-10)
    np.testing.assert_allclose(np.diag(gram), 1., atol=1e-10)
    if gram.shape != (len(x), len(x)) or cross_gram.shape != (len(cross), len(x)):
        raise ValueError('Annual matrix shape mismatch')
    eigenvalues = np.linalg.eigvalsh(gram)
    if eigenvalues.min() < -1e-8:
        raise ValueError('Analytic fidelity matrix is not PSD')
    off_diagonal = gram[~np.eye(len(x), dtype=bool)]
    probabilities = np.maximum(eigenvalues, 0) / eigenvalues.sum()
    positive = probabilities[probabilities > 0]
    diagnostic = dict(train_rows=len(x), validation_rows=len(cross), qubits=x.shape[1],
                      reps=reps, amplitude=amplitude,
                      minimum_eigenvalue=float(eigenvalues.min()),
                      off_diagonal_mean=float(off_diagonal.mean()),
                      off_diagonal_median=float(np.median(off_diagonal)),
                      cross_mean=float(cross_gram.mean()),
                      effective_rank=float(np.exp(-np.sum(positive * np.log(positive)))),
                      pair_circuits=receipt['pair_circuits'])
    return (gram, cross_gram, fit_y, scaler), diagnostic


def audit(root, output):
    if output.exists():
        raise FileExistsError(output)
    root, output = Path(root), Path(output)
    parent_path = root / 'experiments/annual_qsvr.json'
    parent = json.loads(parent_path.read_text())
    table, manifest = prepare(root / 'data/raw/nfdb-audit/source.zip',
                              root / '.cache/wildfire/processed/weather/52f047eb76b948cf66d5/weather_months.csv',
                              parent_path, output / 'data')
    if manifest['table_sha256'] != digest(root / 'docs/data/annual_training.csv'):
        raise ValueError('Recomputed province-year table differs from published training data')
    serialized_table = pd.read_csv(root / 'docs/data/annual_training.csv')
    metrics, classical_refits, quantum_refits, diagnostics = {}, 0, 0, []
    for name in ['classical', 'quantum-4', 'quantum-10', 'matched', 'selectors', 'context']:
        outcome = json.loads((root / f'docs/results/annual-{name}.json').read_text())
        if outcome['final_test_accessed'] or outcome['hardware_jobs_submitted']:
            raise ValueError('Development receipt accesses test or hardware')
        metrics[name] = validate_metrics(outcome['results'])
        if name == 'classical':
            for row in outcome['results']:
                if not row['features']:
                    continue
                first, last, valid_first, valid_last = row['fold']
                train = table[table.year.between(first, last)]
                valid = table[table.year.between(valid_first, valid_last)]
                prediction = fit_predict(row['model'], train[row['features']].to_numpy(),
                                         valid[row['features']].to_numpy(),
                                         train.mean_reported_size_ha.to_numpy(), row['chosen'])
                np.testing.assert_allclose(prediction, row['predicted_ha'], rtol=1e-9, atol=1e-8)
                classical_refits += 1
        if not name.startswith('quantum-'):
            continue
        width = int(name.split('-')[1])
        for row in outcome['results']:
            first, last, valid_first, valid_last = row['fold']
            outer = parent['development_folds'].index(row['fold'])
            # Quantum runners consumed serialized CSV floats; classical ran pre-serialization.
            train = serialized_table[serialized_table.year.between(first, last)]
            valid = serialized_table[serialized_table.year.between(valid_first, valid_last)]
            directory = root / f'.cache/wildfire/annual-qsvr/quantum-{width}-v1/fold-{outer}'
            directory /= f"reps-{row['reps']}-angle-{row['amplitude']:.6f}/outer"
            kernel, diagnostic = matrix_diagnostic(
                directory, train[row['features']].to_numpy(), valid[row['features']].to_numpy(),
                train.mean_reported_size_ha.to_numpy(), row['reps'], row['amplitude'])
            diagnostic.update(fold=row['fold'])
            diagnostics.append(diagnostic)
            prediction = predict_cached(*kernel, row['chosen'])
            np.testing.assert_allclose(prediction, row['predicted_ha'], rtol=1e-9, atol=1e-8)
            quantum_refits += 1
    return dict(study='annual-evidence-audit', training_table_sha256=manifest['table_sha256'],
                metric_records_checked=metrics, classical_reproduction_fits=classical_refits,
                cached_qsvr_reproduction_fits=quantum_refits, new_quantum_states=0,
                new_hardware_jobs=0, annual_test_accessed=False, kernel_diagnostics=diagnostics,
                interpretation='Reproduction fits use fixed saved parameters; they are QA, not new search or independent experiments')

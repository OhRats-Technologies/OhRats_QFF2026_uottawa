"""Descriptive saved-kernel diagnostics; no fitting, optimization or quantum execution."""

import json

import numpy as np
import pandas as pd

from wildfire_lab.annual_final_audit import collect


def gram_summary(gram, target):
    centered = gram - gram.mean(axis=0) - gram.mean(axis=1)[:, None] + gram.mean()
    yy = np.outer(target - target.mean(), target - target.mean())
    denominator = np.linalg.norm(centered) * np.linalg.norm(yy)
    eigenvalues = np.linalg.eigvalsh(gram)
    off = gram[~np.eye(len(gram), dtype=bool)]
    return dict(symmetry_relative_error=float(np.linalg.norm(gram-gram.T)/np.linalg.norm(gram)),
                maximum_diagonal_deviation=float(np.max(np.abs(np.diag(gram)-1))),
                negative_eigenvalue_mass=float(-eigenvalues[eigenvalues<0].sum()),
                participation_ratio=float(np.trace(gram)**2 / np.sum(gram**2)),
                off_diagonal_median=float(np.median(off)),
                off_diagonal_iqr=np.quantile(off, [.25,.75]).tolist(),
                fraction_off_diagonal_below_001=float(np.mean(off<.01)),
                centered_log_target_alignment=float(np.sum(centered*yy)/denominator))


def describe(root, run):
    certificate = collect(root, run, root/'experiments/annual_final.json')
    training = json.loads((run/'training.json').read_text())
    outcome = json.loads((run/'evaluation/outcome.json').read_text())
    observed = {row['id']:row for row in outcome['main_results']}
    table = pd.read_csv(root/'docs/data/annual_training.csv')
    target = np.log1p(table.mean_reported_size_ha.to_numpy())
    diagnostics = []
    for entry in training['kernels']:
        gram = np.load(run/'kernels'/entry['id']/'matrix.npz')['gram']
        diagnostics.append(dict(id=entry['id'], kind=entry['kind'], inputs=len(entry['features']),
                                **gram_summary(gram, target)))
    signals = []
    for model in training['main_models']:
        if model['kind'] not in ['rbf','quantum']:
            continue
        state, scaling = model['state'], model['scaling']
        cross = np.load(run/'evaluation/cross'/model['kernel_id']/'cross.npz')['cross']
        value = cross[:,state['support']] @ state['dual']
        baseline = max(0., float(np.expm1(scaling['target_mean'] + scaling['target_scale']*state['intercept'])))
        prediction = np.maximum(0, np.expm1(scaling['target_mean'] + scaling['target_scale']*(value+state['intercept'])))
        np.testing.assert_allclose(prediction, observed[model['id']]['predicted_ha'], rtol=1e-10, atol=1e-8)
        signals.append(dict(model=model['id'], kernel=model['kernel_id'], years=observed[model['id']]['years'],
                            zero_cross_prediction_ha=baseline, scaled_log_kernel_contribution=value.tolist(),
                            hectare_difference_from_zero_cross=(prediction-baseline).tolist(),
                            support_count=state['support_count'], support_fraction=state['support_count']/len(table)))
    return dict(study='annual-saved-kernel-signal', status='audited_descriptive',
                outcome_sha256=certificate['outcome_sha256'], training_sha256=certificate['training_sha256'],
                kernel_diagnostics=diagnostics, main_kernel_signals=signals,
                model_fits=0, optimizer_calls=0, new_quantum_states=0, hardware_jobs=0,
                interpretation='Post-final reporting from frozen matrices/states. Alignment uses training targets only; no model/map/rank choice follows. Zero-cross output is an algebraic intercept diagnostic, not a newly selected predictor.')

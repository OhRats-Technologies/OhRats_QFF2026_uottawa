"""Select final annual models using training years only and serialize learned states."""

import itertools
import json

import numpy as np
from sklearn.model_selection import TimeSeriesSplit

from wildfire_lab.annual_classical import errors, grid, tune
from wildfire_lab.annual_matched import rbf_candidates, predict_rbf
from wildfire_lab.annual_model_state import fit_scaling, fit_state
from wildfire_lab.annual_quantum import kernel_fold, predict_cached
from wildfire_lab.annual_selectors import selectors
from wildfire_lab.selection import energies


def tune_rbf(x, y, parent, matched):
    scores = []
    for params in rbf_candidates(matched, parent):
        actual, predictions = [], []
        for fit, valid in TimeSeriesSplit(n_splits=3).split(x):
            predictions.extend(predict_rbf(x[fit], x[valid], y[fit], params))
            actual.extend(y[valid])
        scores.append(dict(params=params, **errors(np.array(actual), np.array(predictions))))
    return min(scores, key=lambda row: row['mae_ha']), scores


def tune_quantum(table, features, parent, output):
    x, y = table[features].to_numpy(), table.mean_reported_size_ha.to_numpy()
    scores, resources = [], []
    for reps, amplitude in itertools.product(parent['quantum']['reps'], parent['quantum']['angle_amplitudes']):
        directory = output / f'reps-{reps}-angle-{amplitude:.6f}'
        inner = []
        for index, (fit, valid) in enumerate(TimeSeriesSplit(n_splits=3).split(x)):
            kernel = kernel_fold(x[fit], x[valid], y[fit], directory / f'inner-{index}', reps, amplitude)
            resources.append(dict(years_train=table.year.iloc[fit].tolist(),
                                  years_validation=table.year.iloc[valid].tolist(), **kernel[-1]))
            inner.append((kernel[:4], y[valid]))
        for params in grid('rbf', parent):
            predictions, actual = [], []
            for kernel, targets in inner:
                predictions.extend(predict_cached(*kernel, params))
                actual.extend(targets)
            scores.append(dict(params=params, reps=reps, amplitude=amplitude,
                               **errors(np.array(actual), np.array(predictions))))
        print(json.dumps(dict(stage='train', inputs=len(features), reps=reps,
                              amplitude=amplitude, candidates_scored=len(scores))), flush=True)
    return min(scores, key=lambda row: row['mae_ha']), scores, resources


def main_models(table, parent, matched, kernels, output):
    y = table.mean_reported_size_ha.to_numpy()
    models = [dict(id='training_mean', kind='constant', prediction_ha=float(y.mean())),
              dict(id='training_median', kind='constant', prediction_ha=float(np.median(y))),
              dict(id='linear_year_trend', kind='trend', coefficients=np.polyfit(table.year, y, 1).tolist())]
    resources = []
    for features in [parent['four_feature_subset'], parent['features']]:
        width = len(features)
        x_raw = table[features].to_numpy()
        x, fit_y, scaling = fit_scaling(x_raw, y)
        for kind in ['ridge', 'linear']:
            chosen, scores = tune(kind, x_raw, y, parent)
            state = fit_state(kind, x, fit_y, chosen)
            name = f'ridge_{width}' if kind == 'ridge' else f'linear_svr_{width}'
            models.append(dict(id=name, kind=kind, features=features,
                               scaling=scaling, state=state, params=chosen, inner_tuning=scores))
        chosen, scores = tune_rbf(x_raw, y, parent, matched)
        params = {name: chosen['params'][name] for name in ['C', 'epsilon']}
        gram, entry = kernels.get(table, features, 'rbf', dict(gamma_multiplier=chosen['params']['gamma_multiplier']))
        models.append(dict(id=f'matched_rbf_svr_{width}', kind='rbf', features=features,
                           scaling=scaling, state=fit_state('rbf', gram, fit_y, params),
                           params=chosen['params'], inner_tuning=scores, kernel_id=entry['id']))
        chosen, scores, receipts = tune_quantum(table, features, parent, output / f'inner-{width}')
        resources.extend(receipts)
        gram, entry = kernels.get(table, features, 'quantum', dict(reps=chosen['reps'], amplitude=chosen['amplitude']))
        models.append(dict(id=f'matched_fidelity_svr_{width}', kind='quantum', features=features,
                           scaling=scaling, state=fit_state('quantum', gram, fit_y, chosen['params']),
                           params=chosen['params'], reps=chosen['reps'], amplitude=chosen['amplitude'],
                           inner_tuning=scores, kernel_id=entry['id']))
    return models, resources


def crossover(table, parent, selector_plan, final_plan, kernels):
    features = parent['features']
    full_x, full_y, _ = fit_scaling(table[features].to_numpy(), table.mean_reported_size_ha.to_numpy())
    models, selections = [], []
    for seed in final_plan['selector_crossover']['seeds']:
        choices, objective, metadata = selectors(full_x, full_y, features, parent, selector_plan, seed)
        selections.append(dict(seed=seed, **metadata))
        for selector, indices in choices.items():
            prefix = f'{selector}-seed-{seed}'
            if indices is None:
                models.append(dict(id=prefix, selector=selector, seed=seed, status='no_feasible_draw'))
                continue
            indices = sorted(indices)
            names = [features[index] for index in indices]
            x, y, scaling = fit_scaling(table[names].to_numpy(), table.mean_reported_size_ha.to_numpy())
            bits = np.zeros((1, len(features)))
            bits[0, indices] = 1
            cost = float(energies(objective, bits)[0])
            for kind in ['ridge', 'rbf', 'quantum']:
                params = dict(alpha=1.) if kind == 'ridge' else dict(C=1., epsilon=.2)
                model = dict(id=f'{prefix}-{kind}', selector=selector, seed=seed, kind=kind,
                             features=names, feature_indices=indices, scaling=scaling, params=params,
                             status='complete', objective=cost,
                             objective_gap=cost - metadata['exact_objective'] if len(indices) == 4 else None)
                if kind != 'ridge':
                    kernel_params = dict(gamma_multiplier=1.) if kind == 'rbf' else dict(reps=1, amplitude=np.pi / 2)
                    gram, entry = kernels.get(table, names, kind, kernel_params)
                    model['kernel_id'] = entry['id']
                    model['state'] = fit_state(kind, gram, y, params)
                else:
                    model['state'] = fit_state(kind, x, y, params)
                models.append(model)
    return models, selections

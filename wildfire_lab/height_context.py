"""Fixed training-only height/width/year ablation; never reads final outcomes."""
import json
import time

import numpy as np

from wildfire_lab.annual_classical import errors, fit_predict
from wildfire_lab.annual_quantum import kernel_fold, predict_cached


def append_context(table, context):
    table = table.copy()
    table['zero'] = 0.0
    heights = {row['year']: row['common_mean_height_m'] for row in context['rows']}
    epochs = sorted(heights)
    table['height_epoch'] = [max(epoch for epoch in epochs if epoch < year) for year in table.year]
    table['height'] = table.height_epoch.map(heights)
    return table


def geometry(gram):
    values = np.maximum(np.linalg.eigvalsh(gram), 0)
    probabilities = values / values.sum()
    positive = probabilities[probabilities > 0]
    off_diagonal = gram[~np.eye(len(gram), dtype=bool)]
    return {'effective_rank': float(np.exp(-np.sum(positive * np.log(positive)))),
            'off_diagonal_mean': float(off_diagonal.mean()),
            'minimum_eigenvalue': float(np.linalg.eigvalsh(gram).min())}


def run(table, plan, directory):
    results, resources, kernels = [], [], {}
    start = time.perf_counter()
    pairs = 0
    for fold_id, fold in enumerate(plan['folds']):
        first, last, valid_first, valid_last = fold
        train = table[table.year.between(first, last)]
        valid = table[table.year.between(valid_first, valid_last)]
        y = train.mean_reported_size_ha.to_numpy()
        actual = valid.mean_reported_size_ha.to_numpy()
        results.append(dict(condition='no_inputs', model='training_mean', fold=fold,
                            years=valid.year.tolist(), actual_ha=actual.tolist(),
                            predicted_ha=np.repeat(y.mean(), len(valid)).tolist(),
                            **errors(actual, np.repeat(y.mean(), len(valid)))))
        for condition in plan['conditions']:
            if time.perf_counter() - start > plan['budget']['elapsed_soft_limit_seconds']:
                raise TimeoutError('Context pilot reached its elapsed budget; partial records retained')
            extra = {'weather_four': [], 'weather_plus_zero': ['zero'],
                     'weather_plus_year': ['year'], 'weather_plus_height': ['height']}[condition]
            columns = plan['weather_features'] + extra
            x, cross = train[columns].to_numpy(), valid[columns].to_numpy()
            path = directory / f'fold-{fold_id}' / condition
            kernel = kernel_fold(x, cross, y, path / 'kernel', reps=1, amplitude=np.pi / 32)
            gram = kernel[0]
            kernels[(fold_id, condition)] = gram
            pairs += kernel[-1]['pair_circuits']
            assert pairs <= plan['budget']['pair_circuits_max']
            resources.append(dict(condition=condition, fold=fold, **kernel[-1], **geometry(gram)))
            predictions = {
                'ridge': fit_predict('ridge', x, cross, y, {'alpha': 1.}),
                'rbf': fit_predict('rbf', x, cross, y, {'C': 1., 'epsilon': .2}),
                'qsvr': predict_cached(*kernel[:4], {'C': 1., 'epsilon': .2}),
            }
            for model, prediction in predictions.items():
                results.append(dict(condition=condition, model=model, fold=fold, features=columns,
                                    years=valid.year.tolist(), actual_ha=actual.tolist(),
                                    predicted_ha=prediction.tolist(), **errors(actual, prediction)))
            (directory / 'progress.json').write_text(json.dumps({'results': results, 'resources': resources}, indent=2) + '\n')
            print(f'Fold {fold_id}, {condition}: {len(predictions)} fits; {pairs} pair circuits', flush=True)
    contrasts = []
    for fold_id, fold in enumerate(plan['folds']):
        for model in ['ridge', 'rbf', 'qsvr']:
            rows = {row['condition']: row for row in results if row['model'] == model and row['fold'] == fold}
            contrasts.append(dict(fold=fold, model=model,
                                  height_minus_zero_mae=rows['weather_plus_height']['mae_ha'] - rows['weather_plus_zero']['mae_ha'],
                                  height_minus_year_mae=rows['weather_plus_height']['mae_ha'] - rows['weather_plus_year']['mae_ha'],
                                  zero_minus_four_mae=rows['weather_plus_zero']['mae_ha'] - rows['weather_four']['mae_ha']))
    width_control = [{'fold': fold, 'maximum_kernel_change_from_zero_qubit': float(np.max(np.abs(
        kernels[(fold_id, 'weather_four')] - kernels[(fold_id, 'weather_plus_zero')])))}
        for fold_id, fold in enumerate(plan['folds'])]
    assert len(results) - len(plan['folds']) == plan['budget']['model_fits']
    return {'results': results, 'resources': resources, 'contrasts': contrasts,
            'width_control': width_control, 'pair_circuits': pairs,
            'model_fits': plan['budget']['model_fits'], 'seconds': time.perf_counter() - start,
            'hardware_jobs': 0, 'status': 'complete', 'interpretation': plan['interpretation']}

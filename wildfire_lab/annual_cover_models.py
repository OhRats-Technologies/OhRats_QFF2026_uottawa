"""Fixed annual forest-context ablation against climate and calendar-year controls."""

import numpy as np

from wildfire_lab.annual_classical import errors, fit_predict
from wildfire_lab.annual_quantum import kernel_fold, predict_cached


def screen(table, parent, output):
    results, resources = [], []
    conditions = {
        'physical_four': parent['four_feature_subset'],
        'physical_four_plus_calendar_year': parent['four_feature_subset'] + ['year'],
        'physical_four_plus_previous_map_treed_fraction': parent['four_feature_subset'] + ['treed_fraction'],
    }
    for condition, features in conditions.items():
        for outer, fold in enumerate(parent['development_folds']):
            first, last, valid_first, valid_last = fold
            train = table[table.year.between(first, last)]
            valid = table[table.year.between(valid_first, valid_last)]
            x, cross = train[features].to_numpy(), valid[features].to_numpy()
            y, actual = train.mean_reported_size_ha.to_numpy(), valid.mean_reported_size_ha.to_numpy()
            kernel = kernel_fold(x, cross, y, output / condition / f'fold-{outer}', 1, np.pi / 2)
            resources.append(dict(condition=condition, fold=fold, **kernel[-1]))
            predictions = {
                'fixed_ridge': fit_predict('ridge', x, cross, y, dict(alpha=1.)),
                'fixed_rbf': fit_predict('rbf', x, cross, y, dict(C=1., epsilon=.2)),
                'fixed_qsvr': predict_cached(*kernel[:4], dict(C=1., epsilon=.2)),
            }
            for model, prediction in predictions.items():
                results.append(dict(condition=condition, model=model, features=features, fold=fold,
                                    years=valid.year.tolist(), actual_ha=actual.tolist(),
                                    predicted_ha=prediction.tolist(), **errors(actual, prediction)))
    return results, resources

"""Score frozen annual learned states; test targets never enter prediction functions."""

import json

import numpy as np

from wildfire_lab.annual_classical import errors
from wildfire_lab.annual_data import digest
from wildfire_lab.annual_final_kernel import evaluate_cross
from wildfire_lab.annual_model_state import transform, inverse, predict_scaled


def predict_models(models, table, kernels, training_directory, output, cross_cache):
    results, resources = [], []
    entries = {entry['id']: entry for entry in kernels}
    for model in models:
        record = {key: value for key, value in model.items()
                  if key not in ['state', 'scaling', 'inner_tuning']}
        if model.get('status', 'complete') != 'complete':
            results.append(record)
            continue
        if model['kind'] == 'constant':
            prediction = np.repeat(model['prediction_ha'], len(table))
        elif model['kind'] == 'trend':
            prediction = np.maximum(0, np.polyval(model['coefficients'], table.year))
        else:
            x = transform(table[model['features']].to_numpy(), model['scaling'])
            if model['kind'] in ['rbf', 'quantum']:
                identifier = model['kernel_id']
                if identifier not in cross_cache:
                    entry = entries[identifier]
                    path = training_directory / 'kernels' / identifier / 'matrix.npz'
                    if digest(path) != entry['matrix_sha256']:
                        raise ValueError('Frozen training kernel changed')
                    cross, receipt = evaluate_cross(entry, np.load(path), x, output / 'cross' / identifier)
                    cross_cache[identifier] = cross
                    resources.append(receipt)
                values = cross_cache[identifier]
            else:
                values = x
            prediction = inverse(predict_scaled(model['state'], values), model['scaling'])
        if not np.isfinite(prediction).all():
            raise ValueError('Nonfinite annual prediction')
        # Only scoring reads targets. Frozen state and predictor inputs contain no test labels.
        actual = table.mean_reported_size_ha.to_numpy()
        record.update(years=table.year.tolist(), actual_ha=actual.tolist(),
                      predicted_ha=prediction.tolist(), absolute_errors_ha=np.abs(actual - prediction).tolist(),
                      **errors(actual, prediction))
        results.append(record)
        (output / 'progress.json').write_text(json.dumps(dict(results=results), indent=2) + '\n')
    return results, resources

"""Exclusive, fixed training-only real-circuit mitigation experiment."""
import hashlib
import importlib.metadata
import json
import sys
from pathlib import Path
import time
import numpy as np
import pandas as pd
from wildfire_lab.annual_classical import scale, errors
from wildfire_lab.mitigation_noise import calibrate
from wildfire_lab.mitigation_kernel import experiment as kernel_experiment
from wildfire_lab.mitigation_selection import experiment as selector_experiment

def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def write(path, value):
    path.write_text(json.dumps(value, indent=2)+'\n')

def run(root, dataset, output, plan_path):
    plan = json.loads(plan_path.read_text())
    if digest(dataset) != plan['dataset_sha256']:
        raise ValueError('Frozen training input differs')
    table = pd.read_csv(dataset)
    if table.year.min()<1988 or table.year.max()>2018 or table.year.duplicated().any():
        raise ValueError('Only unique training-period annual rows are accepted')
    parent = json.loads((root/'experiments/annual_qsvr.json').read_text())
    train = table.set_index('year').loc[plan['train_years']]
    valid = table.set_index('year').loc[plan['validation_years']]
    output.mkdir(parents=True, exist_ok=False)
    code_paths = ['annual_classical', 'annual_selectors', 'library_kernel', 'constrained_qaoa',
                  'selection', 'sqd_selection', 'mitigation_noise', 'mitigation_kernel',
                  'mitigation_selection', 'mitigation_run', 'mitigation_collect']
    pins = {f'wildfire_lab/{name}.py': digest(root/f'wildfire_lab/{name}.py') for name in code_paths}
    pins['experiments/annual_qsvr.json'] = digest(root/'experiments/annual_qsvr.json')
    intent = dict(plan_sha256=digest(plan_path), dataset_sha256=digest(dataset), code_sha256=pins,
                  python_version=sys.version, lock_sha256=digest(root/'uv.lock'),
                  packages={p: importlib.metadata.version(p) for p in
                            ['qiskit', 'qiskit-aer', 'qiskit-machine-learning', 'qiskit-addon-sqd',
                             'numpy', 'scipy', 'scikit-learn', 'pandas']},
                  hardware_jobs_submitted=0, final_test_accessed=False)
    write(output/'intent.json', intent)
    started = time.perf_counter()
    calibrations = {}
    for seed in plan['seeds']:
        calibrations[str(seed)] = {}
        for n in [4, 10]:
            counts, channels = calibrate(n, plan['noise'], plan['calibration_shots'], seed+n)
            calibrations[str(seed)][str(n)] = dict(counts=counts.tolist(), channels=channels.tolist())
    actual = valid.mean_reported_size_ha.to_numpy()
    raw_y = train.mean_reported_size_ha.to_numpy()
    features = parent['features']
    x, cross, y, scaler = scale(train[features].to_numpy(), valid[features].to_numpy(), raw_y)
    indices = [features.index(f) for f in parent['four_feature_subset']]
    # Re-standardizing the same four columns gives the same values as their all-ten marginal scaling.
    kernels, kernel_counts, kernel_resources = kernel_experiment(
        x[:, indices], cross[:, indices], y, scaler, actual, plan, calibrations, output)
    write(output/'kernel_checkpoint.json', dict(calibrations=calibrations,
          predictions=kernels, counts=kernel_counts, resources=kernel_resources))
    print('Kernel arms complete', flush=True)
    selectors, selector_counts, selector_resources = selector_experiment(
        x, cross, y, scaler, actual, plan, calibrations, output)
    predictions = kernels+selectors
    mean = np.repeat(raw_y.mean(), len(actual))
    predictions.append(dict(kind='control', label='training_mean', seed=None,
                            predicted_ha=mean.tolist(), **errors(actual, mean)))
    fits = len([r for r in predictions if r['kind']!='control'])+1
    if fits > plan['budget']['maximum_predictor_fits']:
        raise ValueError('Fit budget exceeded')
    payload = dict(plan=plan, intent=intent, features=features,
                   train_years=plan['train_years'], validation_years=plan['validation_years'],
                   scaled_train=x.tolist(), scaled_cross=cross.tolist(), scaled_targets=y.tolist(),
                   y_mean=float(scaler.mean_[0]), y_scale=float(scaler.scale_[0]),
                   actual_ha=actual.tolist(), calibrations=calibrations,
                   kernels=kernel_counts, selectors=selector_counts, predictions=predictions,
                   kernel_resources=kernel_resources, selector_resources=selector_resources,
                   predictor_fits=fits, wall_seconds=time.perf_counter()-started)
    write(output/'evidence.json', payload)
    write(output/'manifest.json', {name: digest(output/name) for name in
          ['evidence.json', 'intent.json', 'kernel_base.qpy', 'selector_base.qpy']})
    return payload

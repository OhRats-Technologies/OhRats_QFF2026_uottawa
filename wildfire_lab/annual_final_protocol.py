"""Exclusive train/evaluate phases and byte-pinned provenance for annual regression."""

from datetime import datetime, timezone
from importlib.metadata import version
import json
import time

import pandas as pd

from wildfire_lab.annual_data import digest, prepare
from wildfire_lab.annual_final_kernel import TrainingKernels
from wildfire_lab.annual_final_train import main_models, crossover
from wildfire_lab.annual_final_evaluate import predict_models

CODE = ['annual_data', 'annual_classical', 'annual_quantum', 'annual_matched',
        'annual_selectors', 'annual_model_state', 'annual_final_kernel', 'annual_final_train',
        'annual_final_evaluate', 'annual_final_protocol', 'nfdb', 'selection', 'qaoa',
        'sqd_selection', 'library_kernel']


def write_json(path, value):
    path.write_text(json.dumps(value, indent=2) + '\n')


def current_code(root):
    paths = [f'wildfire_lab/{name}.py' for name in CODE]
    paths += ['scripts/run_annual_final.py', 'uv.lock', 'pyproject.toml']
    return {name: digest(root / name) for name in paths}


def dependencies():
    return {name: version(name) for name in ['numpy', 'pandas', 'scikit-learn', 'scipy',
                                           'qiskit', 'qiskit-machine-learning', 'qiskit-addon-sqd']}


def inputs(root, plan_path):
    plan = json.loads(plan_path.read_text())
    parents = []
    for field in ['parent', 'matched_parent', 'selectors_parent']:
        path = root / plan[field]
        if digest(path) != plan[field + '_sha256']:
            raise ValueError(f'Final parent changed: {field}')
        parents.append(json.loads(path.read_text()))
    if digest(root / plan['training_dataset']) != plan['training_sha256']:
        raise ValueError('Annual training dataset changed')
    return plan, parents


def train(root, plan_path, output):
    if output.exists():
        raise FileExistsError(output)
    plan, (parent, matched, selector_plan) = inputs(root, plan_path)
    table = pd.read_csv(root / plan['training_dataset'])
    if table.year.tolist() != list(range(1988, 2019)):
        raise ValueError('Final training phase must use exactly 1988–2018')
    output.mkdir(parents=True)
    code = current_code(root)
    write_json(output / 'training_intent.json', dict(created_utc=datetime.now(timezone.utc).isoformat(),
                                                   plan_sha256=digest(plan_path), code_sha256=code))
    start = time.perf_counter()
    kernels = TrainingKernels(output / 'kernels')
    main, inner_resources = main_models(table, parent, matched, kernels, output)
    crossed, selections = crossover(table, parent, selector_plan, plan, kernels)
    if [m['id'] for m in main] != plan['main_models']:
        # Families may be emitted width-first; the frozen set must still be exact.
        if sorted(m['id'] for m in main) != sorted(plan['main_models']):
            raise ValueError('Final main model set differs from frozen plan')
    quantum_count = len(inner_resources) + sum(e['kind'] == 'quantum' for e in kernels.entries)
    if quantum_count > plan['budget']['maximum_training_quantum_matrices']:
        raise ValueError('Final training kernel budget exceeded')
    optimizer_calls = sum(r['qaoa']['circuit_evaluations'] - 1 for r in selections)
    if (optimizer_calls > plan['budget']['selector_qaoa_optimizer_calls']
            or len(crossed) > plan['budget']['selector_final_records']):
        raise ValueError('Final selector budget exceeded')
    outcome = dict(study='annual-final', stage='training_complete', plan_sha256=digest(plan_path),
                   training_sha256=plan['training_sha256'], code_sha256=code, dependencies=dependencies(),
                   main_models=main, crossed_models=crossed, selections=selections,
                   kernels=kernels.entries, inner_resources=inner_resources,
                   training_quantum_matrices=quantum_count,
                   optimizer_calls=optimizer_calls,
                   final_predictor_fits=8 + sum(m.get('status') == 'complete' for m in crossed),
                   main_classical_inner_fits=288, main_quantum_inner_fits=216,
                   wall_seconds=time.perf_counter() - start,
                   final_test_accessed=False, hardware_jobs_submitted=0)
    if current_code(root) != code:
        raise ValueError('Executed recipe changed during training')
    write_json(output / 'training.json', outcome)
    write_json(output / 'training_receipt.json', dict(training_sha256=digest(output / 'training.json'),
                                                   code_sha256=code, plan_sha256=digest(plan_path)))
    return dict(stage='training_complete', models=len(main), crossed_records=len(crossed),
                quantum_matrices=quantum_count, wall_seconds=outcome['wall_seconds'], test_accessed=False)


def evaluate(root, plan_path, output):
    plan, _ = inputs(root, plan_path)
    receipt = json.loads((output / 'training_receipt.json').read_text())
    if digest(output / 'training.json') != receipt['training_sha256']:
        raise ValueError('Frozen annual learned states changed')
    if current_code(root) != receipt['code_sha256'] or digest(plan_path) != receipt['plan_sha256']:
        raise ValueError('Final recipe changed after training')
    training = json.loads((output / 'training.json').read_text())
    if dependencies() != training['dependencies']:
        raise ValueError('Final dependency versions changed')
    archive, weather = root / 'data/raw/nfdb-audit/source.zip', root / plan['weather_path']
    if digest(archive) != plan['nfdb_sha256'] or digest(weather) != plan['weather_sha256']:
        raise ValueError('Final annual source snapshot changed')
    evaluation = output / 'evaluation'
    if evaluation.exists():
        raise FileExistsError('Annual evaluation already has an intent; collect it rather than restart')
    evaluation.mkdir()
    write_json(evaluation / 'intent.json', dict(created_utc=datetime.now(timezone.utc).isoformat(),
                                              training_sha256=receipt['training_sha256'],
                                              plan_sha256=receipt['plan_sha256'], reused_years=[2019, 2024]))
    start = time.perf_counter()
    _, manifest = prepare(archive, weather, plan_path, evaluation / 'data', 2019, 2024)
    table = pd.read_csv(evaluation / 'data/annual.csv')
    if table.year.tolist() != list(range(2019, 2025)):
        raise ValueError('Annual evaluation must contain exactly six reused years')
    cache = {}
    main, resources = predict_models(training['main_models'], table, training['kernels'], output,
                                     evaluation, cache)
    crossed, more_resources = predict_models(training['crossed_models'], table, training['kernels'], output,
                                             evaluation, cache)
    resources += more_resources
    if sum(r['kind'] == 'quantum' for r in resources) > plan['budget']['maximum_test_cross_matrices']:
        raise ValueError('Final test cross-kernel budget exceeded')
    outcome = dict(study='annual-final', stage='evaluated', plan_sha256=receipt['plan_sha256'],
                   training_receipt=receipt, dataset_manifest=manifest, main_results=main,
                   crossed_results=crossed, cross_resources=resources,
                   wall_seconds=time.perf_counter() - start, predictor_fits=0,
                   reused_test_years=True, hardware_jobs_submitted=0, limitations=plan['limitations'])
    if current_code(root) != receipt['code_sha256']:
        raise ValueError('Final recipe changed during evaluation; preserve partial records for audit')
    write_json(evaluation / 'outcome.json', outcome)
    return dict(stage='evaluated', models=len(main), crossed_records=len(crossed),
                wall_seconds=outcome['wall_seconds'], predictor_fits=0, reused_test_years=True)

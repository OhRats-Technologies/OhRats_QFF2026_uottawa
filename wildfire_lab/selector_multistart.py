"""Frozen deeper selector search; training-only, no hardware submission."""
import argparse
import importlib.metadata
import json
from pathlib import Path
import subprocess
import time
import numpy as np
import pandas as pd
from wildfire_lab.annual_selectors import objective
from wildfire_lab.forest_models import prepare, fit
from wildfire_lab.forest_run import digest, write
from wildfire_lab.selector_sector import Sector, sample, diagonal_sqd
from wildfire_lab.selector_search import search


def cohort(train, valid, columns, plan, number):
    targets = train.mean_reported_size_ha.to_numpy()
    actual = valid.mean_reported_size_ha.to_numpy()
    x, _, y, _, preprocessing = prepare(
        train[columns].to_numpy(), valid[columns].to_numpy(), targets)
    obj = objective(x, y, plan['selection'], plan['selection']['seed'])
    sector = Sector(obj)
    runs, winners = search(sector, plan)
    policies = {'uniform': np.full(len(sector.cost), 1/len(sector.cost))}
    policies.update({name: np.asarray(runs[index]['probability'])
                     for name, index in winners.items()})
    choices = dict(
        exact=np.flatnonzero(sector.bits[np.argmin(sector.cost)]).tolist(),
        mi=np.sort(np.argsort(-obj['relevance'], kind='stable')[:obj['k']]).tolist())
    samples, sqd = [], {}
    for name, probability in policies.items():
        for shots in plan['shot_budgets']:
            for replicate in range(plan['sampling_replicates']):
                seed = plan['selection']['seed']+10000*number+100*len(columns)+replicate
                record = sample(sector, probability, shots, seed)
                samples.append(dict(policy=name, replicate=replicate, **record))
                if shots == max(plan['shot_budgets']) and replicate == 0:
                    choices[name] = record['selected_indices']
                    sqd[name] = diagonal_sqd(obj, record)
    models = {}
    for name, indices in choices.items():
        features = [columns[i] for i in indices]
        models[name] = fit(train[features].to_numpy(), valid[features].to_numpy(),
                           targets, actual, features, plan)
    return dict(features=columns, selector_qubits=len(columns), predictor_qubits=obj['k'],
                selector_train=x.tolist(), selector_targets=y.tolist(),
                preprocessing=preprocessing, exact_objective=sector.shift,
                sector_states=sector.states.tolist(), sector_objectives=sector.cost.tolist(),
                enumeration_seconds=sector.enumeration_seconds,
                runs=runs, winners=winners, choices=choices, samples=samples,
                sqd=sqd, models=models)


def run(root, output, plan_path):
    plan = json.loads(plan_path.read_text())
    for name, expected in plan['input_sha256'].items():
        assert digest(root/name) == expected, f'Changed frozen input: {name}'
    paths = [str(plan_path.relative_to(root)), *plan['code_paths']]
    for name in paths:
        committed = subprocess.check_output(['git', 'show', 'HEAD:'+name], cwd=root)
        assert committed == (root/name).read_bytes(), f'Uncommitted recipe: {name}'
    table = pd.read_csv(root/plan['dataset'])
    assert table.year.tolist() == list(range(1988, 2019))
    output.mkdir(parents=True, exist_ok=False)
    intent = dict(plan=plan, plan_sha256=digest(plan_path),
                  revision=subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=root,
                                                   text=True).strip(),
                  code_sha256={name: digest(root/name) for name in plan['code_paths']},
                  packages={name: importlib.metadata.version(name) for name in
                            ['numpy', 'scipy', 'scikit-learn', 'qiskit',
                             'qiskit-machine-learning', 'qiskit-addon-sqd']})
    write(output/'intent.json', intent)
    started = time.perf_counter()
    evidence = dict(intent=intent, cohorts=[], rows=[], model_fits=0, pair_circuits=0,
                    optimizer_calls=0, hardware_jobs=0, final_test_accessed=False)
    for number, fold in enumerate(plan['folds']):
        first, last, vfirst, vlast = fold
        train = table[table.year.between(first, last)]
        valid = table[table.year.between(vfirst, vlast)]
        for width in plan['pool_sizes']:
            if time.perf_counter()-started > plan['budget']['elapsed_soft_limit_seconds']:
                raise TimeoutError('Search stopped at declared boundary; evidence retained')
            result = cohort(train, valid, plan['features'][:width], plan, number)
            result['fold'] = fold
            write(output/f'cohort-{number}-{width}.json', result)
            evidence['cohorts'].append(result)
            evidence['optimizer_calls'] += sum(r['objective_calls'] for r in result['runs'])
            for name, model in result['models'].items():
                evidence['model_fits'] += len(model['rows'])
                evidence['pair_circuits'] += model['resource']['pair_circuits']
                evidence['rows'].extend(dict(fold=fold, pool_size=width, selector=name, **row)
                                        for row in model['rows'])
            write(output/'progress.json', evidence)
            print(f'Fold {number}, pool {width}: 12 searches, '
                  f'{evidence["optimizer_calls"]} cumulative calls', flush=True)
    assert evidence['model_fits'] == plan['budget']['model_fits']
    assert evidence['optimizer_calls'] <= plan['budget']['optimizer_calls_max']
    assert evidence['pair_circuits'] <= plan['budget']['pair_circuits_max']
    evidence.update(status='complete', seconds=time.perf_counter()-started,
                    classical_sample_draws=9*5*plan['sampling_replicates']*sum(plan['shot_budgets']),
                    converged_searches=sum(r['optimizer_success'] for c in evidence['cohorts']
                                          for r in c['runs']))
    write(output/'evidence.json', evidence)
    return {key: evidence[key] for key in ['status', 'seconds', 'model_fits',
                                          'optimizer_calls', 'converged_searches']}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    print(json.dumps(run(root, args.output.resolve(),
                         root/'experiments/selector_multistart.json')))

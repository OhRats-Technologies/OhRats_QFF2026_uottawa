"""Frozen larger-pool selector study, with matched training-only regression panels."""
import json
import time
import importlib.metadata
from pathlib import Path
import numpy as np
import pandas as pd
from wildfire_lab.annual_selectors import objective
from wildfire_lab.forest_models import prepare, fit
from wildfire_lab.forest_run import digest, write
from wildfire_lab.selector_sector import Sector, sample, diagonal_sqd


def cohort(train, valid, columns, plan, fold_number):
    start = time.perf_counter()
    targets = train.mean_reported_size_ha.to_numpy()
    actual = valid.mean_reported_size_ha.to_numpy()
    x, _, y, _, preprocessing = prepare(train[columns].to_numpy(),
                                       valid[columns].to_numpy(), targets)
    t = time.perf_counter()
    obj = objective(x, y, plan['selection'], plan['selection']['seed'])
    objective_seconds = time.perf_counter()-t
    t = time.perf_counter()
    sector = Sector(obj)
    sector_setup_seconds = time.perf_counter()-t
    best = int(np.argmin(sector.cost))
    choices = dict(exact=np.flatnonzero(sector.bits[best]).tolist(),
                   mi=np.sort(np.argsort(-obj['relevance'], kind='stable')[:obj['k']]).tolist())
    t = time.perf_counter()
    fixed_probability = sector.probability(plan['selection']['fixed_parameters'])
    fixed_seconds = time.perf_counter()-t
    policies = dict(uniform=dict(probability=np.repeat(1/len(sector.cost), len(sector.cost)).tolist(),
                                  objective_calls=0, sector_state_evaluations=0, seconds=0, depth=0),
                    fixed=dict(parameters=plan['selection']['fixed_parameters'],
                               probability=fixed_probability.tolist(),
                               objective_calls=0, sector_state_evaluations=1, seconds=fixed_seconds, depth=1))
    for depth, calls in plan['optimization_calls'].items():
        policies['optimized'+depth] = sector.optimize(int(depth), calls)
    samples = []
    representative = {}
    for name, policy in policies.items():
        p = np.array(policy['probability'])
        optimum = np.isclose(sector.cost, sector.cost.min(), atol=1e-9, rtol=0)
        policy['optimum_probability'] = float(p[optimum].sum())
        policy['expected_objective'] = float(p @ sector.cost)
        for shots in plan['shot_budgets']:
            policy.setdefault('probability_find_optimum', {})[str(shots)] = float(-np.expm1(shots*np.log1p(-min(p[optimum].sum(),1-1e-15))))
            for replicate in range(plan['sampling_replicates']):
                seed = plan['selection']['seed'] + 10000*fold_number + 100*len(columns) + replicate
                record = sample(sector, p, shots, seed)
                samples.append(dict(policy=name, replicate=replicate, **record))
                if shots == max(plan['shot_budgets']) and replicate == 0:
                    representative[name] = record
                    choices[name] = record['selected_indices']
                    policy['sqd'] = diagonal_sqd(obj, record)
    models = {}
    for name, indices in choices.items():
        chosen = [columns[i] for i in indices]
        models[name] = fit(train[chosen].to_numpy(), valid[chosen].to_numpy(),
                           targets, actual, chosen, plan)
    return dict(features=columns, logical_selector_qubits=len(columns), selected_count=obj['k'],
                feasible_subsets=len(sector.states), sector_states=sector.states.tolist(),
                sector_objectives=sector.cost.tolist(), objective={k:v.tolist() if isinstance(v,np.ndarray) else v for k,v in obj.items()},
                objective_seconds=objective_seconds, enumeration_seconds=sector.enumeration_seconds,
                mixer_setup_seconds=sector.mixer_setup_seconds, sector_setup_seconds=sector_setup_seconds,
                selector_preprocessing=preprocessing, selector_train=x.tolist(), selector_targets=y.tolist(),
                exact_objective=float(sector.cost.min()), choices=choices,
                policies=policies, samples=samples, representative=representative, models=models,
                downstream_qsvr_qubits=obj['k'], seconds=time.perf_counter()-start)


def run(root, output):
    path = root/'experiments/selector_scaling.json'
    plan = json.loads(path.read_text())
    for name, expected in plan['input_sha256'].items():
        assert digest(root/name) == expected, f'Frozen input changed: {name}'
    table = pd.read_csv(root/plan['dataset'])
    assert table.year.tolist() == list(range(1988,2019))
    output.mkdir(parents=True, exist_ok=False)
    intent = dict(plan=plan, plan_sha256=digest(path),
                  dataset_sha256=digest(root/plan['dataset']),
                  code_sha256={name:digest(root/name) for name in plan['code_paths']})
    intent['packages'] = {n:importlib.metadata.version(n) for n in
                          ['qiskit','qiskit-machine-learning','qiskit-addon-sqd','scikit-learn','numpy','scipy']}
    write(output/'intent.json', intent)
    start = time.perf_counter()
    evidence = dict(intent=intent, cohorts=[], rows=[], model_fits=0, pair_circuits=0,
                    hardware_jobs=0, final_test_accessed=False, simulator='exact cardinality-sector classical simulation')
    for number, fold in enumerate(plan['folds']):
        first, last, vfirst, vlast = fold
        train = table[table.year.between(first,last)]
        valid = table[table.year.between(vfirst,vlast)]
        for width in plan['pool_sizes']:
            if time.perf_counter()-start > plan['budget']['elapsed_soft_limit_seconds']:
                raise TimeoutError('Study budget reached; progress preserved')
            result = cohort(train, valid, plan['features'][:width], plan, number)
            result['fold'] = fold
            for name, model in result['models'].items():
                evidence['model_fits'] += len(model['rows'])
                evidence['pair_circuits'] += model['resource']['pair_circuits']
                evidence['rows'].extend(dict(fold=fold, pool_size=width, selector=name, **row) for row in model['rows'])
            evidence['cohorts'].append(result)
            write(output/f'cohort-{number}-{width}.json', result)
            write(output/'progress.json', evidence)
            print(f'Fold{number} pool{width}: {len(result["sector_states"])} subsets, {evidence["model_fits"]} fits',flush=True)
    assert evidence['model_fits'] == plan['budget']['model_fits']
    assert evidence['pair_circuits'] <= plan['budget']['pair_circuits_max']
    evidence.update(status='complete', seconds=time.perf_counter()-start,
                    classical_sample_draws=len(evidence['cohorts'])*4*plan['sampling_replicates']*sum(plan['shot_budgets']),
                    qiskit_sampler_shots=0)
    write(output/'evidence.json', evidence)
    return evidence


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    result = run(root, args.output.resolve())
    print(json.dumps({k:result[k] for k in ['seconds','model_fits','pair_circuits','classical_sample_draws']}))

"""Tune selector redundancy only inside chronological training splits."""
import argparse
import json
from pathlib import Path
import subprocess
import time
import numpy as np
import pandas as pd
from sklearn.model_selection import TimeSeriesSplit
from wildfire_lab.annual_selectors import objective
from wildfire_lab.annual_classical import fit_predict, errors
from wildfire_lab.forest_models import prepare, fit
from wildfire_lab.forest_run import digest, write
from wildfire_lab.selector_sector import Sector, sample, diagonal_sqd
from wildfire_lab.selector_search import optimize


def selected(train, columns, weight, plan):
    raw = train[columns].to_numpy()
    x, _, y, _, preprocessing = prepare(raw, raw, train.mean_reported_size_ha.to_numpy())
    specification = dict(plan['selection'], redundancy_weight=weight)
    obj = objective(x, y, specification, plan['selection']['seed'])
    sector = Sector(obj)
    best = int(np.argmin(sector.cost))
    return sector, obj, np.flatnonzero(sector.bits[best]).tolist(), preprocessing


def tune_weight(train, columns, plan):
    records = []
    for weight in plan['weights']:
        for proxy in ['ridge', 'rbf']:
            actual, predictions, splits = [], [], []
            for indices, validation in TimeSeriesSplit(n_splits=3).split(train):
                inner, held_out = train.iloc[indices], train.iloc[validation]
                _, _, subset, preprocessing = selected(inner, columns, weight, plan)
                features = [columns[i] for i in subset]
                parameters = plan['models']['ridge'] if proxy == 'ridge' else plan['models']['svr']
                prediction = fit_predict(proxy, inner[features].to_numpy(), held_out[features].to_numpy(),
                                         inner.mean_reported_size_ha.to_numpy(), parameters)
                actual.extend(held_out.mean_reported_size_ha)
                predictions.extend(prediction)
                splits.append(dict(training_years=inner.year.tolist(), validation_years=held_out.year.tolist(),
                                   selected_indices=subset, preprocessing=preprocessing,
                                   actual_ha=held_out.mean_reported_size_ha.tolist(), predicted_ha=prediction.tolist()))
            records.append(dict(weight=weight, proxy=proxy, splits=splits,
                                **errors(np.asarray(actual), np.asarray(predictions))))
    chosen = {proxy: min((record for record in records if record['proxy'] == proxy),
                        key=lambda row: row['mae_ha'])['weight'] for proxy in ['ridge', 'rbf']}
    return chosen, records


def cohort(train, valid, columns, plan, number):
    chosen, tuning = tune_weight(train, columns, plan)
    base, original, exact, preprocessing = selected(train, columns, .5, plan)
    _, _, no_redundancy, _ = selected(train, columns, 0., plan)
    choices = dict(mi=np.sort(np.argsort(-original['relevance'], kind='stable')[:4]).tolist(),
                   random=np.sort(np.random.default_rng(137+number).choice(len(columns), 4, replace=False)).tolist(),
                   exact_original=exact, exact_no_redundancy=no_redundancy)
    selectors = {}
    for proxy, weight in chosen.items():
        sector, obj, exact, _ = selected(train, columns, weight, plan)
        choices['exact_'+proxy] = exact
        runs = [optimize(sector, 2, start, plan['qaoa_calls']) for start in plan['starts']]
        winner = min(range(len(runs)), key=lambda index: runs[index]['expected_objective'])
        p = np.asarray(runs[winner]['probability'])
        samples = [sample(sector, p, plan['shots'], 901+10000*number+replicate)
                   for replicate in range(plan['sampling_replicates'])]
        choices['qaoa_'+proxy] = samples[0]['selected_indices']
        selectors[proxy] = dict(weight=weight, objective={key: value.tolist() if isinstance(value, np.ndarray)
                                                        else value for key, value in obj.items()},
                                sector_states=sector.states.tolist(), sector_objectives=sector.cost.tolist(),
                                runs=runs, chosen_run=winner, samples=samples,
                                sqd=diagonal_sqd(obj, samples[0]))
    models, rows = {}, []
    for name, indices in choices.items():
        features = [columns[i] for i in indices]
        result = fit(train[features].to_numpy(), valid[features].to_numpy(),
                     train.mean_reported_size_ha.to_numpy(), valid.mean_reported_size_ha.to_numpy(),
                     features, plan)
        models[name] = result
        bits = np.zeros((1, len(columns)))
        bits[0, indices] = 1
        from wildfire_lab.selection import energies
        reference_cost = float(energies(original, bits)[0])
        rows.extend(dict(selector=name, original_half_weight_cost=reference_cost, **row)
                    for row in result['rows'])
    return dict(chosen_weights=chosen, tuning=tuning, choices=choices, selectors=selectors,
                models=models, rows=rows, selector_preprocessing=preprocessing,
                enumeration_seconds=base.enumeration_seconds)


def run(root, output):
    path = root/'experiments/objective_alignment.json'
    plan = json.loads(path.read_text())
    for name in [str(path.relative_to(root)), *plan['code_paths']]:
        assert subprocess.check_output(['git', 'show', 'HEAD:'+name], cwd=root) == (root/name).read_bytes()
    assert digest(root/plan['dataset']) == plan['dataset_sha256']
    table = pd.read_csv(root/plan['dataset'])
    assert table.year.tolist() == list(range(1988, 2019))
    output.mkdir(parents=True, exist_ok=False)
    started = time.perf_counter()
    intent = dict(plan=plan, plan_sha256=digest(path),
                  revision=subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=root, text=True).strip(),
                  code_sha256={name: digest(root/name) for name in plan['code_paths']})
    write(output/'intent.json', intent)
    evidence = dict(intent=intent, cohorts=[], rows=[], model_fits=0, pair_circuits=0,
                    hardware_jobs=0, final_test_accessed=False)
    for number, fold in enumerate(plan['folds']):
        first, last, vfirst, vlast = fold
        train, valid = table[table.year.between(first, last)], table[table.year.between(vfirst, vlast)]
        for width in plan['pool_sizes']:
            result = cohort(train, valid, plan['features'][:width], plan, number)
            result.update(fold=fold, pool_size=width)
            evidence['cohorts'].append(result)
            evidence['rows'].extend(dict(fold=fold, pool_size=width, **row) for row in result['rows'])
            evidence['model_fits'] += len(result['rows'])+len(plan['weights'])*2*3
            evidence['pair_circuits'] += sum(model['resource']['pair_circuits'] for model in result['models'].values())
            write(output/f'cohort-{number}-{width}.json', result)
            write(output/'progress.json', evidence)
            print(f'Fold {number}, pool {width}: proxy choices {result["chosen_weights"]}', flush=True)
    assert evidence['model_fits'] == plan['budget']['model_fits']
    evidence.update(status='complete', seconds=time.perf_counter()-started,
                    objective_calls=sum(run['objective_calls'] for c in evidence['cohorts']
                                        for selector in c['selectors'].values() for run in selector['runs']),
                    classical_sample_draws=9*2*plan['sampling_replicates']*plan['shots'])
    write(output/'evidence.json', evidence)
    return {key: evidence[key] for key in ['status', 'seconds', 'model_fits', 'objective_calls']}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(run(Path(__file__).resolve().parents[1], args.output.resolve())))

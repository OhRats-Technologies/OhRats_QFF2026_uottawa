"""Training-only preparation alternatives, with saved states, samples and fits."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import time
from zipfile import ZipFile
import numpy as np
import pandas as pd
from wildfire_lab.forest_models import fit
from wildfire_lab.forest_run import digest, write
from wildfire_lab.selector_sector import Sector, sample, diagonal_sqd
from wildfire_lab.shallow_selector import optimize


def parent(root, plan):
    index = json.loads((root/'docs/results/selector-scaling.json').read_text())
    bundle = root/index['bundle']
    assert digest(bundle) == index['bundle_sha256']
    with ZipFile(bundle) as archive:
        raw = archive.read('evidence.json')
    assert hashlib.sha256(raw).hexdigest() == plan['parent_evidence_sha256']
    return json.loads(raw)


def run(root, output):
    path = root/'experiments/shallow_preparation.json'
    plan = json.loads(path.read_text())
    for name in [str(path.relative_to(root)), *plan['code_paths']]:
        assert subprocess.check_output(['git', 'show', 'HEAD:'+name], cwd=root) == (root/name).read_bytes()
    source = parent(root, plan)
    assert digest(root/plan['dataset']) == plan['dataset_sha256']
    table = pd.read_csv(root/plan['dataset'])
    assert table.year.tolist() == list(range(1988, 2019))
    output.mkdir(parents=True, exist_ok=False)
    intent = dict(plan=plan, plan_sha256=digest(path),
                  revision=subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=root,
                                                   text=True).strip(),
                  code_sha256={name: digest(root/name) for name in plan['code_paths']})
    write(output/'intent.json', intent)
    started = time.perf_counter()
    evidence = dict(intent=intent, cohorts=[], rows=[], optimizer_calls=0, model_fits=0,
                    pair_circuits=0, hardware_jobs=0, final_test_accessed=False)
    for number, old in enumerate(source['cohorts']):
        obj = {key: np.asarray(value) if isinstance(value, list) else value
               for key, value in old['objective'].items()}
        sector = Sector(obj)
        initial = dict(random=np.sort(np.random.default_rng(plan['seed']+sector.n).choice(
            sector.n, sector.k, replace=False)).tolist(), mi=old['choices']['mi'])
        fits, runs, samples, sqd = {}, {}, [], {}
        choices = dict(initial)
        for name, indices in initial.items():
            for depth, calls in plan['optimization_calls'].items():
                label = name+'-p'+depth
                result = optimize(sector, indices, int(depth), calls)
                runs[label] = result
                evidence['optimizer_calls'] += result['objective_calls']
                for replicate in range(plan['sampling_replicates']):
                    record = sample(sector, np.asarray(result['probability']), plan['shots'],
                                    plan['seed']+10000*number+replicate)
                    samples.append(dict(policy=label, replicate=replicate, **record))
                    if replicate == 0:
                        choices[label] = record['selected_indices']
                        sqd[label] = diagonal_sqd(obj, record)
        first, last, vfirst, vlast = old['fold']
        train, valid = table[table.year.between(first, last)], table[table.year.between(vfirst, vlast)]
        for label, indices in choices.items():
            columns = [old['features'][i] for i in indices]
            result = fit(train[columns].to_numpy(), valid[columns].to_numpy(),
                         train.mean_reported_size_ha.to_numpy(), valid.mean_reported_size_ha.to_numpy(),
                         columns, plan)
            fits[label] = result
            evidence['model_fits'] += len(result['rows'])
            evidence['pair_circuits'] += result['resource']['pair_circuits']
            evidence['rows'].extend(dict(fold=old['fold'], pool_size=sector.n, policy=label, **row)
                                    for row in result['rows'])
        cohort = dict(fold=old['fold'], features=old['features'], objective=old['objective'],
                      initial=initial, choices=choices, runs=runs, samples=samples, sqd=sqd, models=fits,
                      sector_states=sector.states.tolist(), sector_objectives=sector.cost.tolist())
        write(output/f'cohort-{number}.json', cohort)
        evidence['cohorts'].append(cohort)
        write(output/'progress.json', evidence)
        print(f'Fold {old["fold"][1]}, pool {sector.n}: basis-start searches complete', flush=True)
    assert evidence['model_fits'] == plan['budget']['model_fits']
    assert evidence['optimizer_calls'] <= plan['budget']['optimizer_calls_max']
    evidence.update(status='complete', seconds=time.perf_counter()-started,
                    classical_draws=len(evidence['cohorts'])*6*plan['shots']*plan['sampling_replicates'])
    write(output/'evidence.json', evidence)
    return {key: evidence[key] for key in ['status', 'seconds', 'model_fits', 'optimizer_calls']}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(run(Path(__file__).resolve().parents[1], args.output.resolve())))

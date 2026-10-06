"""Execute a new nested expanded-model plan, without touching final-year evidence."""
import argparse
import importlib.metadata
import json
from pathlib import Path
import subprocess
import time
import numpy as np
import pandas as pd
from wildfire_lab.annual_classical import errors
from wildfire_lab.forest_run import digest, write
from wildfire_lab.nested_search import tune, prepared, evaluate, grid
from wildfire_lab.search_kernels import parity, distinct_geometry


def run(root, output, path=None):
    path = path or root/'experiments/expanded_tuning.json'
    plan = json.loads(path.read_text())
    for name, expected in plan['input_sha256'].items():
        assert digest(root/name) == expected, f'Frozen data changed: {name}'
    for name in [str(path.relative_to(root)), *plan['code_paths']]:
        assert subprocess.check_output(['git', 'show', 'HEAD:'+name], cwd=root) == (root/name).read_bytes()
    table = pd.read_csv(root/plan['dataset'])
    assert table.year.tolist() == list(range(1988, 2019))
    output.mkdir(parents=True, exist_ok=False)
    intent = dict(plan=plan, plan_sha256=digest(path),
                  revision=subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=root,
                                                   text=True).strip(),
                  code_sha256={name: digest(root/name) for name in plan['code_paths']},
                  packages={name: importlib.metadata.version(name) for name in
                            ['qiskit', 'qiskit-machine-learning', 'scikit-learn', 'numpy', 'scipy']})
    write(output/'intent.json', intent)
    started = time.perf_counter()
    checks = parity(plan['quantum'])
    write(output/'kernel_parity.json', checks)
    geometry = distinct_geometry(plan['quantum']) if plan['quantum'].get('require_distinct_geometry') else []
    write(output/'distinct_geometry.json', geometry)
    evidence = dict(intent=intent, parity=checks, distinct_geometry=geometry,
                    cohorts=[], rows=[], model_fits=0,
                    state_evaluations=sum(row['state_evaluations'] for row in checks+geometry),
                    parity_pair_circuits=sum(row['analytic_pair_circuits'] for row in checks),
                    hardware_jobs=0, final_test_accessed=False)
    for number, fold in enumerate(plan['folds']):
        first, last, vfirst, vlast = fold
        train = table[table.year.between(first, last)]
        valid = table[table.year.between(vfirst, vlast)]
        actual = valid.mean_reported_size_ha.to_numpy()
        mean_prediction = np.repeat(train.mean_reported_size_ha.mean(), len(valid))
        evidence['rows'].append(dict(model='training_mean', panel='no_inputs', fold=fold,
                                    predicted_ha=mean_prediction.tolist(), actual_ha=actual.tolist(),
                                    **errors(actual, mean_prediction)))
        for panel in plan['panels']:
            if time.perf_counter()-started > plan['budget']['elapsed_soft_limit_seconds']:
                raise TimeoutError('Declared cohort boundary reached; saved progress retained')
            tuning = tune(train, panel, plan)
            data = prepared(train, valid, panel, plan)
            conditions = dict(tuning['chosen'])
            conditions['fixed_qsvr'] = plan['fixed_qsvr']
            results = {name: evaluate(data, specification, plan)
                       for name, specification in conditions.items()}
            result = dict(panel=panel, fold=fold, tuning=tuning, results=results)
            write(output/f'cohort-{number}-{panel}.json', result)
            evidence['cohorts'].append(result)
            evidence['model_fits'] += tuning['predictor_fits']+len(results)
            evidence['state_evaluations'] += sum(s['state_evaluations'] for s in tuning['inner_splits'])
            evidence['state_evaluations'] += sum(r['resource']['state_evaluations'] for r in results.values())
            evidence['rows'].extend(dict(panel=panel, fold=fold, model=name, **{
                key: row[key] for key in ['predicted_ha', 'actual_ha', 'mae_ha', 'rmse_ha', 'bias_ha']})
                for name, row in results.items())
            write(output/'progress.json', evidence)
            print(f'Fold {number}, {panel}: {len(grid(plan))} nested candidates, '
                  f'{evidence["model_fits"]} cumulative fits', flush=True)
    assert evidence['model_fits'] == plan['budget']['model_fits']
    evidence.update(status='complete', seconds=time.perf_counter()-started)
    write(output/'evidence.json', evidence)
    return {key: evidence[key] for key in ['status', 'seconds', 'model_fits', 'state_evaluations']}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--plan', type=Path, help='Separately frozen follow-up recipe')
    args = parser.parse_args()
    print(json.dumps(run(Path(__file__).resolve().parents[1], args.output.resolve(),
                         args.plan.resolve() if args.plan else None)))

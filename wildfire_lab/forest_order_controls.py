"""Run two post-hoc graph-matched controls without touching primary evidence."""
import json
import time
from pathlib import Path
import pandas as pd
from wildfire_lab.forest_features import WEATHER
from wildfire_lab.forest_models import fit
from wildfire_lab.forest_run import digest, write


def run(root, output):
    path = root / 'experiments/forest_order_controls.json'
    plan = json.loads(path.read_text())
    dataset = root / plan['dataset']
    parent = root / '.cache/wildfire/forest-expansion-v1/evidence.json'
    assert digest(dataset) == plan['dataset_sha256']
    assert digest(parent) == plan['parent_evidence_sha256']
    table = pd.read_csv(dataset)
    assert table.year.tolist() == list(range(1988, 2019))
    output.mkdir(parents=True, exist_ok=False)
    intent = dict(plan=plan, plan_sha256=digest(path), dataset_sha256=digest(dataset),
                  code_sha256={name: digest(root/name) for name in plan['code_paths']})
    write(output/'intent.json', intent)
    start = time.perf_counter()
    evidence = dict(intent=intent, folds=[], rows=[], pair_circuits=0,
                    model_fits=0, final_test_accessed=False, hardware_jobs=0)
    controls = dict(interleaved_zero8=['zero']*4,
                    interleaved_calendar8=['calendar_linear', 'calendar_square',
                                          'calendar_cube', 'calendar_epoch'])
    for fold in plan['folds']:
        first, last, vfirst, vlast = fold
        train = table[table.year.between(first, last)]
        valid = table[table.year.between(vfirst, vlast)]
        record = dict(fold=fold, conditions={})
        for label, values in controls.items():
            columns = [column for pair in zip(WEATHER, values) for column in pair]
            result = fit(train[columns].to_numpy(), valid[columns].to_numpy(),
                         train.mean_reported_size_ha.to_numpy(),
                         valid.mean_reported_size_ha.to_numpy(), columns, plan)
            record['conditions'][label] = result
            evidence['rows'].extend(dict(fold=fold, condition=label, **r) for r in result['rows'])
            evidence['model_fits'] += len(result['rows'])
            evidence['pair_circuits'] += result['resource']['pair_circuits']
        evidence['folds'].append(record)
        write(output/'progress.json', evidence)
    assert evidence['model_fits'] == plan['budget']['model_fits']
    assert evidence['pair_circuits'] <= plan['budget']['pair_circuits_max']
    evidence.update(status='complete', seconds=time.perf_counter()-start)
    write(output/'evidence.json', evidence)
    return evidence


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    result = run(root, args.output.resolve())
    print(json.dumps({k: result[k] for k in ['seconds', 'model_fits', 'pair_circuits']}))

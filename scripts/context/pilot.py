"""Run only the frozen coarse-height training ablation, in a new exclusive namespace."""
import hashlib
import json
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from wildfire_lab.height_context import append_context, run


def main():
    plan_path = ROOT / 'experiments/coarse_height_context.json'
    plan = json.loads(plan_path.read_text())
    for name, expected in plan['data_hashes'].items():
        assert hashlib.sha256((ROOT / name).read_bytes()).hexdigest() == expected, name
    table = pd.read_csv(ROOT / 'docs/data/annual_training.csv')
    assert table.year.tolist() == list(range(1988, 2019))
    context = json.loads((ROOT / 'docs/data/scanfi_height_context.json').read_text())
    table = append_context(table, context)
    directory = ROOT / '.cache/wildfire/coarse-height-context-v1'
    directory.mkdir(parents=True)
    hashes = {str(path.relative_to(ROOT)): hashlib.sha256(path.read_bytes()).hexdigest()
              for path in [plan_path, Path(__file__), ROOT / 'wildfire_lab/height_context.py']}
    (directory / 'intent.json').write_text(json.dumps({'plan': plan, 'runner_hashes': hashes}, indent=2) + '\n')
    table.to_csv(directory / 'annual.csv', index=False)
    result = run(table, plan, directory)
    result['plan_sha256'] = hashes[str(plan_path.relative_to(ROOT))]
    result['runner_hashes'] = hashes
    (directory / 'result.json').write_text(json.dumps(result, indent=2) + '\n')
    (ROOT / 'docs/results/coarse-height-context.json').write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps({key: result[key] for key in ['status', 'seconds', 'pair_circuits', 'model_fits', 'width_control']}, indent=2))


if __name__ == '__main__':
    main()

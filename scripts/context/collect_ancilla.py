"""Verify saved ancilla amplitudes and kernel identities without new states/fits."""
import argparse
import json
from datetime import datetime, timezone
from pathlib import Path

import numpy as np

from ancilla import ROOT, PLAN, digest, load_parents, saved_identity, control_metrics, check_metrics


def collect():
    plan = json.loads(PLAN.read_text())
    directory = ROOT / plan['output']
    intent = json.loads((directory / 'intent.json').read_text())
    result = json.loads((directory / 'run.json').read_text())
    assert intent['plan'] == plan
    assert intent['source_hashes'] == result['source_hashes']
    assert all(digest(ROOT / name) == value for name, value in result['source_hashes'].items())
    assert digest(directory / 'statevectors.npz') == result['statevectors_sha256']
    parents = load_parents(plan)
    records = saved_identity(parents)
    rows = plan['control_rows']
    reference = parents[0, 'weather_four']
    with np.load(directory / 'statevectors.npz') as saved:
        assert np.array_equal(saved['angles'], reference['angles'][:rows])
        assert saved['base'].shape == (rows, 16) and saved['disconnected'].shape == (rows, 32)
        control = control_metrics(saved['base'], saved['disconnected'], reference['gram'][:rows, :rows])
    check_metrics(records, control, plan)
    assert records == result['saved_identity'] and control == result['tensor_control']
    assert result['resources']['new_statevectors'] == plan['budget']['new_statevectors_max']
    assert result['status'] == 'passed'
    return {
        'checked_utc': datetime.now(timezone.utc).isoformat(), 'status': 'verified_saved_control',
        'run_sha256': digest(directory / 'run.json'),
        'collector_sha256': digest(Path(__file__)),
        'saved_matrix_entries': sum(record['matrix_entries'] for record in records),
        'saved_identity': records, 'tensor_control': control,
        'original_new_statevectors': result['resources']['new_statevectors'],
        'collection_new_statevectors': 0, 'sampler_pair_circuits': 0, 'predictor_fits': 0,
        'hardware_jobs': 0, 'limitation': 'Collector verifies saved amplitudes and algebra. '
          'It does not regenerate circuit execution or independently validate predictive performance.',
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, default=ROOT / '.cache/context/constant-ancilla-v1/collected.json')
    args = parser.parse_args()
    if not args.output.resolve().is_relative_to(ROOT / '.cache'):
        parser.error('Use a new ignored cache output; preserve published evidence')
    result = collect()
    with args.output.open('x') as stream:
        json.dump(result, stream, indent=2)
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    main()

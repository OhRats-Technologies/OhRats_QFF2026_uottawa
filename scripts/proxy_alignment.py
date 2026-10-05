"""Run or collect a fixed training-only surrogate-alignment diagnostic."""
import argparse
import hashlib
import json
import os
import signal
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
import pandas as pd
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from wildfire_lab.evaluation import split
from wildfire_lab.proxy_alignment import inputs, fit_subsets, validate

RECIPES = ['scripts/proxy_alignment.py', 'wildfire_lab/proxy_alignment.py',
    'wildfire_lab/constrained_selection.py', 'wildfire_lab/selection.py',
    'wildfire_lab/evaluation.py', 'experiments/proxy_alignment.json',
    'experiments/constrained_selection.json', 'experiments/quantum_landmarks.json',
    'pyproject.toml', 'uv.lock']


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def context(plan):
    cache = ROOT / plan['parent_cache']
    assert sha(cache / 'outcome.json') == plan['parent_outcome_sha256']
    record = json.loads((cache / 'outcome.json').read_text())
    assert record['status'] == 'complete'
    selector = record['intent']['plan']; parent = record['intent']['parent_plan']
    assert selector == json.loads((ROOT / plan['parent_plan']).read_text())
    assert plan['logistic'] == selector['logistic']
    source = ROOT / parent['dataset'] / 'features.csv'
    assert sha(source) == parent['dataset_sha256']
    frame = pd.read_csv(source)
    assert frame.year.between(1988, 2018).all() and frame.incident_id.is_unique
    train, valid = split(frame, parent['fold'], train_window=(1988, 2018))
    return record, selector, parent, train, valid


def run(cache):
    plan = json.loads((ROOT / 'experiments/proxy_alignment.json').read_text())
    assert not plan['hardware'] and not plan['final_test_access']
    parent_record, selector, parent, train, valid = context(plan)
    assert [r['seed'] for r in parent_record['seeds']] == plan['seeds']
    commit = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip()
    hashes = {}
    for name in RECIPES:
        raw = (ROOT / name).read_bytes()
        assert raw == subprocess.check_output(['git', 'show', f'{commit}:{name}'], cwd=ROOT)
        hashes[name] = hashlib.sha256(raw).hexdigest()
    intent = dict(plan=plan, git_commit=commit, recipe_sha256=hashes,
        started_utc=datetime.now(timezone.utc).isoformat())
    cache.mkdir(parents=True, exist_ok=True)
    with (cache / 'intent.json').open('x') as f:
        json.dump(intent, f, indent=2)
    outcome = dict(status='running', intent=intent, seeds=[])
    start = time.perf_counter()
    def save():
        path = cache / 'outcome.tmp'; path.write_text(json.dumps(outcome, indent=2)+'\n')
        os.replace(path, cache / 'outcome.json')
    def timeout(*_):
        raise TimeoutError('Frozen proxy diagnostic wall cap reached')
    signal.signal(signal.SIGALRM, timeout); signal.alarm(plan['max_wall_seconds'])
    try:
        for record in parent_record['seeds']:
            x, y, v, target, hashes = inputs(train, valid, parent, record, selector['features'])
            rows = fit_subsets(x, y, v, target, record['objective'], plan['logistic'])
            review = validate(rows, x, y, v, target, record['objective'], plan['logistic'], record)
            outcome['seeds'].append(dict(seed=record['seed'], group=record['group'],
                **hashes, rows=rows, review=review))
            save()
        outcome['predictor_fits'] = sum(len(r['rows']) for r in outcome['seeds'])
        assert outcome['predictor_fits'] == plan['max_predictor_fits']
        outcome['status'] = 'complete'
    except Exception as error:
        outcome.update(status='failed_preserved', error_type=type(error).__name__, error=str(error))
        raise
    finally:
        signal.alarm(0); outcome['seconds'] = time.perf_counter()-start; save()
    print(json.dumps({k:outcome[k] for k in ['status', 'predictor_fits', 'seconds']}))


def collect(cache, output):
    start = time.perf_counter()
    record = json.loads((cache / 'outcome.json').read_text())
    intent = json.loads((cache / 'intent.json').read_text()); plan = intent['plan']
    assert record['status'] == 'complete' and record['intent'] == intent
    for name, expected in intent['recipe_sha256'].items():
        raw = subprocess.check_output(['git', 'show', f'{intent["git_commit"]}:{name}'], cwd=ROOT)
        assert hashlib.sha256(raw).hexdigest() == expected and sha(ROOT / name) == expected
    parent_record, selector, parent, train, valid = context(plan)
    assert [r['seed'] for r in record['seeds']] == plan['seeds']
    public = []
    for row, prior in zip(record['seeds'], parent_record['seeds']):
        assert (row['seed'], row['group']) == (prior['seed'], prior['group'])
        x, y, v, target, hashes = inputs(train, valid, parent, prior, selector['features'])
        assert all(row[k] == val for k, val in hashes.items())
        review = validate(row['rows'], x, y, v, target, prior['objective'], plan['logistic'], prior)
        assert review == row['review']
        public.append(dict(seed=row['seed'], group=row['group'], **hashes, review=review,
            rows=[{k:val for k,val in r.items() if k not in
                ['predictions', 'coefficient', 'intercept']} for r in row['rows']]))
    assert sum(len(r['rows']) for r in public) == record['predictor_fits'] == plan['max_predictor_fits']
    assert record['seconds'] <= plan['max_wall_seconds']
    summary = dict(status='audited_training_only_proxy_alignment', plan=plan,
        opening_commit=intent['git_commit'], outcome_sha256=sha(cache / 'outcome.json'),
        intent_sha256=sha(cache / 'intent.json'), dataset_sha256=parent['dataset_sha256'],
        runner_seconds=record['seconds'], audit_seconds=time.perf_counter()-start,
        predictor_fits=record['predictor_fits'], audit_predictor_fits=0,
        new_selector_fits=0, quantum_calls=0, hardware_jobs_submitted=0, final_test_access=False,
        seeds=public)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(summary, separators=(',', ':'))+'\n')
    print(json.dumps({k:summary[k] for k in ['status', 'runner_seconds', 'audit_seconds', 'predictor_fits']}))
    return summary


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=['run', 'collect'])
    parser.add_argument('--cache', type=Path, default=ROOT / '.cache/wildfire/proxy-alignment')
    parser.add_argument('--output', type=Path, default=ROOT / 'docs/results/proxy-alignment.json')
    args = parser.parse_args()
    run(args.cache) if args.action == 'run' else collect(args.cache, args.output)

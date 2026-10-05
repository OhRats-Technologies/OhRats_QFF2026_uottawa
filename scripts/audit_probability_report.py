"""Report frozen final probabilities without fitting or modifying final evidence."""
import argparse
import hashlib
import json
import subprocess
import sys
import time
from pathlib import Path
import numpy as np
import pandas as pd
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from wildfire_lab.final_checks import metric
from wildfire_lab.probability_report import summarize

RECIPES = ['configs/wildfires/probability_report.json', 'scripts/audit_probability_report.py',
    'wildfire_lab/probability_report.py', 'wildfire_lab/final_checks.py', 'wildfire_lab/evaluation.py']


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def audit(output):
    start = time.perf_counter()
    plan = json.loads((ROOT / RECIPES[0]).read_text())
    commit = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip()
    recipes = {}
    for name in RECIPES:
        raw = (ROOT / name).read_bytes()
        assert raw == subprocess.check_output(['git', 'show', f'{commit}:{name}'], cwd=ROOT)
        recipes[name] = hashlib.sha256(raw).hexdigest()
    cache = ROOT / '.cache/wildfire/final-test'
    outcome = cache / 'outcome.json'; evidence = ROOT / 'docs/results/final-evaluation.json'
    assert digest(outcome) == plan['final_outcome_sha256']
    assert digest(evidence) == plan['final_evidence_sha256']
    record = json.loads(outcome.read_text()); public = json.loads(evidence.read_text())
    assert record['status'] == 'complete' and record['plan'] == public['plan']
    assert digest(cache / 'intent.json') == public['intent_sha256']
    assert digest(cache / 'features.csv') == record['test_dataset']['data_sha256']
    test = pd.read_csv(cache / 'features.csv', usecols=['incident_id', 'year', 'target'])
    assert test.incident_id.is_unique and test.year.between(2019, 2024).all()
    assert len(test) == record['test_dataset']['rows']
    p0 = public['training_positive_fraction']
    rows = []
    expected = {(g, p) for g in record['plan']['feature_groups'] for p in ['logistic', 'tree']}
    saved = record['rows']['full_training_models']
    assert len(saved) == len(expected) and {(r['group'], r['predictor']) for r in saved} == expected
    for row in saved:
        metric(row, test.target.to_numpy(), True)
        p = np.asarray(row['predictions'])
        summary = summarize(test.target.to_numpy(), p, plan['bins'], p0)
        assert np.isclose(summary['brier'], row['metric']['brier'], atol=1e-12, rtol=0)
        by_year = {}
        for year in sorted(test.year.unique()):
            mask = test.year.eq(year).to_numpy()
            by_year[str(year)] = summarize(test.target.to_numpy()[mask], p[mask], plan['bins'], p0)
        rows.append(dict(group=row['group'], predictor=row['predictor'], pooled=summary, by_year=by_year))
    report = dict(status='audited_saved_probability_reporting', reporting_commit=commit,
        plan=plan, recipe_sha256=recipes, final_opening_commit=public['opening_commit'],
        training_positive_fraction=p0, test_data_sha256=record['test_dataset']['data_sha256'],
        audit_seconds=time.perf_counter()-start, model_fits=0, calibrator_fits=0,
        quantum_calls=0, hardware_jobs_submitted=0, final_predictions_changed=False, rows=rows)
    output.parent.mkdir(parents=True, exist_ok=True)
    header = {k:v for k,v in report.items() if k != 'rows'}
    lines = [json.dumps(header, separators=(',', ':'))[:-1]+',"rows":[']
    lines.extend(json.dumps(row, separators=(',', ':'))+(',' if i<len(rows)-1 else '')
        for i, row in enumerate(rows))
    lines.append(']}'); output.write_text('\n'.join(lines)+'\n')
    print(json.dumps({k:report[k] for k in ['status', 'audit_seconds', 'model_fits', 'calibrator_fits']}))
    return report


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, default=ROOT / 'docs/data/probability_report.json')
    args = parser.parse_args(); audit(args.output)

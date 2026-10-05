"""Audit saved final predictions and export compact measured evidence; no refit."""
import argparse
import hashlib
import json
import subprocess
import sys
from pathlib import Path
import pandas as pd

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from wildfire_lab.final_features import digest,preflight
from wildfire_lab.final_checks import validate


def audit(cache,output):
    path=cache/'outcome.json';record=json.loads(path.read_text());intent=json.loads((cache/'intent.json').read_text())
    if record['intent']!=intent:raise ValueError('Stored final intent differs from outcome')
    if digest(cache/'features.csv')!=record['test_dataset']['data_sha256']:raise ValueError('Test table changed')
    commit=intent['git_commit'];frozen=intent['recipe_sha256']
    for file,expected in frozen.items():
        raw=subprocess.check_output(['git','show',f'{commit}:{file}'],cwd=ROOT)
        if hashlib.sha256(raw).hexdigest()!=expected:raise ValueError('Opening recipe not recoverable in Git')
    plans=[file for file,expected in frozen.items() if expected==intent['plan_sha256']]
    if len(plans)!=1:raise ValueError('Opening protocol not recoverable')
    raw=subprocess.check_output(['git','show',f'{commit}:{plans[0]}'],cwd=ROOT)
    if json.loads(raw)!=record['plan']:raise ValueError('Opening protocol differs from outcome')
    train,manifest,_=preflight(record['plan'],ROOT)
    if manifest!=record['training_dataset']:raise ValueError('Training manifest changed')
    test=pd.read_csv(cache/'features.csv');checks=validate(record,train,test)
    rows={section:[{k:v for k,v in row.items() if k!='predictions'} for row in values] for section,values in record['rows'].items()}
    summary=dict(status='audited_final',final_test_performance_opened=True,outcome_sha256=digest(path),
        intent_sha256=digest(cache/'intent.json'),opening_commit=commit,plan_sha256=intent['plan_sha256'],plan=record['plan'],
        audit_recipe_sha256={str(p.relative_to(ROOT)):digest(p) for p in [Path(__file__),ROOT/'wildfire_lab/final_checks.py']},
        training_rows=len(train),training_positive_fraction=float(train.target.mean()),training_data_sha256=manifest['data_sha256'],
        test_dataset=record['test_dataset'],test_positive_fraction=float(test.target.mean()),recomputed_checks=checks,
        timings={k:record[k] for k in ['preflight_seconds','feature_join_seconds','model_seconds','total_seconds']},
        rows=rows,limitations='One frozen final opening. Metrics recomputed from saved predictions; no refit. Seed samples overlap and are not independent temporal replication. Full-training models and capped matrix have different label budgets. No causal, deployment or quantum-advantage claim.')
    # One compact model per line keeps the committed evidence easy to review.
    header={k:v for k,v in summary.items() if k!='rows'}
    lines=[json.dumps(header,separators=(',',':'))[:-1]+',"rows":{']
    for i,(section,values) in enumerate(rows.items()):
        lines.append(json.dumps(section)+':[')
        lines.extend(json.dumps(row,separators=(',',':'))+(',' if j<len(values)-1 else '') for j,row in enumerate(values))
        lines.append(']'+(',' if i<len(rows)-1 else ''))
    lines.append('}}');output.parent.mkdir(parents=True,exist_ok=True);output.write_text('\n'.join(lines)+'\n')
    print(json.dumps(dict(checks=checks,timings=summary['timings'],training_rows=len(train),test_rows=len(test)),indent=2))
    return summary


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--cache',type=Path,default=ROOT/'.cache/wildfire/final-test')
    parser.add_argument('--output',type=Path,default=ROOT/'docs/results/final-evaluation.json')
    args=parser.parse_args();audit(args.cache,args.output)

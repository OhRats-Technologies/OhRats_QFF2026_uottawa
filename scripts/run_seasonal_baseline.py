"""Exclusive training-only seasonal controls; no final test or quantum calls."""
import argparse
import hashlib
import json
import os
import signal
import subprocess
import sys
import time
from datetime import datetime,timezone
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
RECIPES=['scripts/run_seasonal_baseline.py','wildfire_lab/seasonal_baseline.py',
    'wildfire_lab/evaluation.py','experiments/seasonal_baseline.json','pyproject.toml','uv.lock']


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',type=Path,default=ROOT/'.cache/wildfire/seasonal-baseline')
    args=parser.parse_args();plan=json.loads((ROOT/'experiments/seasonal_baseline.json').read_text())
    assert plan['status']=='frozen_training_only_control_followup'
    assert not plan['hardware'] and not plan['final_test_access'] and plan['train_years'][1]<=2018
    commit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip();hashes={}
    for name in RECIPES:
        raw=(ROOT/name).read_bytes();assert raw==subprocess.check_output(['git','show',commit+':'+name],cwd=ROOT),name
        hashes[name]=hashlib.sha256(raw).hexdigest()
    source=ROOT/plan['dataset']/'features.csv';assert hashlib.sha256(source.read_bytes()).hexdigest()==plan['dataset_sha256']
    args.output.mkdir(parents=True,exist_ok=True)
    intent=dict(plan=plan,git_commit=commit,recipe_hashes=hashes,started_utc=datetime.now(timezone.utc).isoformat())
    with (args.output/'intent.json').open('x') as f:json.dump(intent,f,indent=2)
    start=time.perf_counter();outcome=dict(status='running',intent=intent,rows=[])
    def save():
        temp=args.output/'outcome.tmp';temp.write_text(json.dumps(outcome,indent=2)+'\n');os.replace(temp,args.output/'outcome.json')
    def timeout(*_):raise TimeoutError('Declared baseline wall cap reached')
    def checkpoint():
        if time.perf_counter()-start>=plan['max_wall_seconds']:timeout()
    signal.signal(signal.SIGALRM,timeout);signal.alarm(plan['max_wall_seconds'])
    try:
        import pandas as pd
        from wildfire_lab.seasonal_baseline import run,validate
        frame=pd.read_csv(source);outcome['rows']=run(frame,plan,checkpoint)
        outcome.update(status='complete',checks=validate(frame,plan,outcome['rows']))
    except Exception as error:
        outcome.update(status='failed_preserved',error_type=type(error).__name__,error=str(error));raise
    finally:
        signal.alarm(0);outcome['seconds']=time.perf_counter()-start;save()
    print(json.dumps(dict(status=outcome['status'],conditions=len(outcome['rows']),seconds=outcome['seconds'])))


if __name__=='__main__':main()

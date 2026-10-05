"""Exclusive, bounded owner-requested training-only library pilot. No IBM calls."""
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
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))

ROOT=Path(__file__).resolve().parents[1]
RECIPES=['scripts/run_library_followup.py','wildfire_lab/library_screen.py',
    'wildfire_lab/library_kernel.py','wildfire_lab/sqd_selection.py',
    'wildfire_lab/evaluation.py','wildfire_lab/encoding_screen.py',
    'wildfire_lab/kernel.py','wildfire_lab/selection.py','wildfire_lab/qaoa.py',
    'pyproject.toml','uv.lock','experiments/qiskit_library_followup.json']


def digest(raw):return hashlib.sha256(raw).hexdigest()


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',type=Path,default=ROOT/'.cache/wildfire/library-followup')
    args=parser.parse_args()
    plan=json.loads((ROOT/'experiments/qiskit_library_followup.json').read_text())
    commit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT).decode().strip()
    hashes={}
    for name in RECIPES:
        raw=(ROOT/name).read_bytes()
        assert raw==subprocess.check_output(['git','show',f'{commit}:{name}'],cwd=ROOT),name
        hashes[name]=digest(raw)
    source=ROOT/plan['dataset']/'features.csv'
    assert digest(source.read_bytes())==plan['dataset_sha256']
    assert plan['hardware'] is False and plan['final_test_access'] is False
    args.output.mkdir(parents=True,exist_ok=True)
    intent=dict(plan=plan,git_commit=commit,recipe_hashes=hashes,
                started_utc=datetime.now(timezone.utc).isoformat())
    with (args.output/'intent.json').open('x') as f:json.dump(intent,f,indent=2)
    start=time.perf_counter();outcome=dict(status='running',intent=intent,seeds=[])
    def save():
        tmp=args.output/'outcome.tmp';tmp.write_text(json.dumps(outcome,indent=2)+'\n')
        os.replace(tmp,args.output/'outcome.json')
    def timeout(*_):raise TimeoutError('Declared local pilot wall budget reached')
    signal.signal(signal.SIGALRM,timeout);signal.alarm(plan['max_wall_seconds'])
    def checkpoint(progress=None):
        if progress is not None:outcome['progress']=progress;save()
        if time.perf_counter()-start>=plan['max_wall_seconds']:timeout()
    try:
        import pandas as pd
        from wildfire_lab.evaluation import split
        from wildfire_lab.library_screen import run
        frame=pd.read_csv(source)
        assert frame.year.between(1988,2018).all() and frame.incident_id.is_unique
        train,valid=split(frame,plan['fold'],train_window=(1988,2018))
        for seed in plan['seeds']:
            checkpoint();outcome['seeds'].append(run(train,valid,plan,seed,checkpoint));save()
            print(json.dumps(dict(seed=seed,status=outcome['seeds'][-1]['status'])),flush=True)
        outcome['status']='complete'
    except Exception as error:
        outcome.update(status='failed_preserved',error_type=type(error).__name__,error=str(error))
        raise
    finally:
        signal.alarm(0);outcome['seconds']=time.perf_counter()-start;save()
    print(json.dumps(dict(status=outcome['status'],seconds=outcome['seconds'])))


if __name__=='__main__':main()

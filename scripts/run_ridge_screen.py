"""Exclusive bounded training-only ridge comparison; no shots or hardware."""
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
RECIPES=['scripts/run_ridge_screen.py','wildfire_lab/ridge_screen.py','wildfire_lab/ridge_inputs.py',
    'wildfire_lab/ridge_kernel.py','wildfire_lab/ridge_review.py','wildfire_lab/landmarks.py',
    'wildfire_lab/evaluation.py','wildfire_lab/encoding_screen.py','wildfire_lab/kernel.py',
    'experiments/kernel_ridge.json','experiments/quantum_landmarks.json','pyproject.toml','uv.lock']


def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',type=Path,default=ROOT/'.cache/wildfire/kernel-ridge')
    args=parser.parse_args();plan=json.loads((ROOT/'experiments/kernel_ridge.json').read_text())
    parent=json.loads((ROOT/plan['parent_plan']).read_text())
    assert not plan['hardware'] and not plan['final_test_access'] and not parent['final_test_access']
    groups={'diagnostic':plan['diagnostic_seeds'],'sampling_check':plan['sampling_check_seeds']}
    seeds=sum(groups.values(),[]);assert len(set(seeds))==len(seeds)
    assert len(seeds)*(parent['train_cap']+parent['validation_cap'])<=plan['max_simulated_state_preparations']
    commit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT).decode().strip();hashes={}
    for name in RECIPES:
        raw=(ROOT/name).read_bytes()
        assert raw==subprocess.check_output(['git','show',f'{commit}:{name}'],cwd=ROOT),name
        hashes[name]=hashlib.sha256(raw).hexdigest()
    source=ROOT/parent['dataset']/'features.csv';assert sha(source)==parent['dataset_sha256']
    intent=dict(plan=plan,parent_plan=parent,parent_evidence_sha256=sha(ROOT/plan['parent_evidence']),
        git_commit=commit,recipe_hashes=hashes,started_utc=datetime.now(timezone.utc).isoformat())
    args.output.mkdir(parents=True,exist_ok=True)
    with (args.output/'intent.json').open('x') as f:json.dump(intent,f,indent=2)
    start=time.perf_counter();outcome=dict(status='running',intent=intent,seeds=[])
    def save():
        tmp=args.output/'outcome.tmp';tmp.write_text(json.dumps(outcome,indent=2)+'\n');os.replace(tmp,args.output/'outcome.json')
    def timeout(*_):raise TimeoutError('Declared ridge wall budget reached')
    signal.signal(signal.SIGALRM,timeout);signal.alarm(plan['max_wall_seconds'])
    def checkpoint(progress=None):
        if progress is not None:outcome['progress']=progress;save()
        if time.perf_counter()-start>=plan['max_wall_seconds']:timeout()
    try:
        import pandas as pd
        from wildfire_lab.evaluation import split
        from wildfire_lab.ridge_screen import run
        from wildfire_lab.ridge_review import review
        frame=pd.read_csv(source);assert frame.year.between(1988,2018).all() and frame.incident_id.is_unique
        train,valid=split(frame,parent['fold'],train_window=(1988,2018))
        for group,seeds in groups.items():
            for seed in seeds:
                outcome['seeds'].append(run(train,valid,parent,plan,seed,group,checkpoint));save()
                print(json.dumps(dict(seed=seed,group=group,status='complete')),flush=True)
        outcome.update(status='complete',review=review(outcome['seeds'],plan))
    except Exception as error:
        outcome.update(status='failed_preserved',error_type=type(error).__name__,error=str(error));raise
    finally:
        signal.alarm(0);outcome['seconds']=time.perf_counter()-start;save()
    print(json.dumps(dict(status=outcome['status'],seconds=outcome['seconds'],review=outcome['review'])))


if __name__=='__main__':main()

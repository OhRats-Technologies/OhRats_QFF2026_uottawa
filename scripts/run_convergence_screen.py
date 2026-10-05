"""Exclusive training-only convergence diagnostic; original outcomes stay frozen."""
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
RECIPES=['scripts/run_convergence_screen.py','wildfire_lab/convergence_screen.py',
    'wildfire_lab/solver_diagnostics.py','wildfire_lab/landmarks.py','wildfire_lab/evaluation.py',
    'wildfire_lab/encoding_screen.py','wildfire_lab/kernel.py','experiments/kernel_convergence.json',
    'experiments/quantum_landmarks.json','pyproject.toml','uv.lock']


def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',type=Path,default=ROOT/'.cache/wildfire/kernel-convergence')
    args=parser.parse_args();plan=json.loads((ROOT/'experiments/kernel_convergence.json').read_text())
    parent=json.loads((ROOT/plan['parent_plan']).read_text());public=json.loads((ROOT/plan['parent_evidence']).read_text())
    original_path=ROOT/'.cache/wildfire/quantum-landmarks/outcome.json'
    assert sha(original_path)==public['outcome_sha256'] and public['plan']==parent
    original=json.loads(original_path.read_text());assert original['status']=='complete'
    assert plan['seeds']==parent['seeds'] and plan['C']==parent['C']
    assert not plan['hardware'] and not plan['final_test_access'] and not parent['final_test_access']
    commit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT).decode().strip();hashes={}
    for name in RECIPES:
        raw=(ROOT/name).read_bytes()
        assert raw==subprocess.check_output(['git','show',f'{commit}:{name}'],cwd=ROOT),name
        hashes[name]=hashlib.sha256(raw).hexdigest()
    source=ROOT/parent['dataset']/'features.csv';assert sha(source)==parent['dataset_sha256']
    intent=dict(plan=plan,parent_plan=parent,parent_outcome_sha256=sha(original_path),
        parent_evidence_sha256=sha(ROOT/plan['parent_evidence']),git_commit=commit,recipe_hashes=hashes,
        started_utc=datetime.now(timezone.utc).isoformat())
    args.output.mkdir(parents=True,exist_ok=True)
    with (args.output/'intent.json').open('x') as f:json.dump(intent,f,indent=2)
    start=time.perf_counter();outcome=dict(status='running',intent=intent,seeds=[])
    def save():
        tmp=args.output/'outcome.tmp';tmp.write_text(json.dumps(outcome,indent=2)+'\n');os.replace(tmp,args.output/'outcome.json')
    def timeout(*_):raise TimeoutError('Declared convergence wall budget reached')
    signal.signal(signal.SIGALRM,timeout);signal.alarm(plan['max_wall_seconds'])
    def checkpoint(progress=None):
        if progress is not None:outcome['progress']=progress;save()
        if time.perf_counter()-start>=plan['max_wall_seconds']:timeout()
    try:
        import pandas as pd
        from wildfire_lab.evaluation import split
        from wildfire_lab.convergence_screen import run
        frame=pd.read_csv(source);assert frame.year.between(1988,2018).all() and frame.incident_id.is_unique
        train,valid=split(frame,parent['fold'],train_window=(1988,2018))
        for seed,prior in zip(plan['seeds'],original['seeds']):
            assert prior['seed']==seed
            outcome['seeds'].append(run(train,valid,parent,plan,seed,prior,checkpoint));save()
            print(json.dumps(dict(seed=seed,status='complete')),flush=True)
        outcome['status']='complete'
    except Exception as error:
        outcome.update(status='failed_preserved',error_type=type(error).__name__,error=str(error));raise
    finally:
        signal.alarm(0);outcome['seconds']=time.perf_counter()-start;save()
    print(json.dumps(dict(status=outcome['status'],seconds=outcome['seconds'])))


if __name__=='__main__':main()

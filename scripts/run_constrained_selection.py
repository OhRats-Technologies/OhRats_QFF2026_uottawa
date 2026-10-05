"""Exclusive fixed-cardinality selector pilot; exact simulation, no hardware."""
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
import pandas as pd
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from wildfire_lab.evaluation import split
from wildfire_lab.constrained_selection import run

RECIPES=['scripts/run_constrained_selection.py','scripts/collect_constrained_selection.py','wildfire_lab/constrained_checks.py',
    'wildfire_lab/constrained_selection.py','wildfire_lab/constrained_qaoa.py',
    'wildfire_lab/selection.py','wildfire_lab/evaluation.py','experiments/constrained_selection.json',
    'experiments/quantum_landmarks.json','pyproject.toml','uv.lock']


def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',type=Path,default=ROOT/'.cache/wildfire/constrained-selection')
    args=parser.parse_args();plan=json.loads((ROOT/'experiments/constrained_selection.json').read_text());parent=json.loads((ROOT/plan['parent_plan']).read_text())
    assert not plan['hardware'] and not plan['final_test_access'] and plan['depth']==1
    seed_count=len(plan['diagnostic_seeds'])+len(plan['sampling_check_seeds'])
    variants=len(plan['initial_states'])*len(plan['mixers'])
    assert seed_count*variants*(plan['max_objective_calls']+1)<=plan['max_quantum_state_evaluations']
    assert seed_count*(variants+len(plan['classical_controls']))<=plan['max_predictor_fits']
    assert seed_count<=plan['max_l1_selector_fits']
    commit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip();hashes={}
    for name in RECIPES:
        raw=(ROOT/name).read_bytes();assert raw==subprocess.check_output(['git','show',f'{commit}:{name}'],cwd=ROOT),name
        hashes[name]=hashlib.sha256(raw).hexdigest()
    source=ROOT/parent['dataset']/'features.csv';assert sha(source)==parent['dataset_sha256']
    args.output.mkdir(parents=True,exist_ok=True)
    intent=dict(plan=plan,parent_plan=parent,git_commit=commit,recipe_sha256=hashes,started_utc=datetime.now(timezone.utc).isoformat())
    with (args.output/'intent.json').open('x') as f:json.dump(intent,f,indent=2)
    outcome=dict(status='running',intent=intent,seeds=[]);start=time.perf_counter()
    def save():
        temp=args.output/'outcome.tmp';temp.write_text(json.dumps(outcome,indent=2)+'\n');os.replace(temp,args.output/'outcome.json')
    def timeout(*_):raise TimeoutError('Declared selector wall budget reached')
    signal.signal(signal.SIGALRM,timeout);signal.alarm(plan['max_wall_seconds'])
    def checkpoint(progress=None):
        if progress is not None:outcome['progress']=progress
        save()
        if time.perf_counter()-start>plan['max_wall_seconds']:timeout()
    try:
        frame=pd.read_csv(source);assert frame.year.between(1988,2018).all() and frame.incident_id.is_unique
        train,valid=split(frame,parent['fold'],train_window=(1988,2018))
        for group,seeds in [('diagnostic',plan['diagnostic_seeds']),('sampling_check',plan['sampling_check_seeds'])]:
            for seed in seeds:
                outcome['seeds'].append(run(train,valid,parent,plan,seed,group,checkpoint));save()
                print(json.dumps(dict(group=group,seed=seed,status='complete')),flush=True)
        outcome['quantum_state_evaluations']=sum(q['quantum_state_evaluations'] for s in outcome['seeds'] for q in s['quantum'])
        outcome['predictor_fits']=sum(r['status']=='complete' for s in outcome['seeds'] for r in s['rows'])
        outcome['l1_selector_fits']=len(outcome['seeds'])
        assert outcome['quantum_state_evaluations']<=plan['max_quantum_state_evaluations']
        assert outcome['predictor_fits']<=plan['max_predictor_fits'] and outcome['l1_selector_fits']<=plan['max_l1_selector_fits']
        outcome['status']='complete'
    except Exception as error:
        outcome.update(status='failed_preserved',error_type=type(error).__name__,error=str(error));raise
    finally:
        signal.alarm(0);outcome['seconds']=time.perf_counter()-start;save()
    print(json.dumps({k:outcome[k] for k in ['status','seconds','quantum_state_evaluations','predictor_fits','l1_selector_fits']}))


if __name__=='__main__':main()

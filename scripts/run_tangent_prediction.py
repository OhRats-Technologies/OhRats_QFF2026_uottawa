"""Exclusive bounded ridge-control follow-up; reuse saved states and kernels."""
import argparse
import json
import os
import signal
import subprocess
import sys
import time
from datetime import datetime,timezone
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from wildfire_lab.geometry_inputs import sha
from wildfire_lab.tangent_inputs import load
from wildfire_lab.tangent_prediction import run,review

RECIPES=['scripts/run_tangent_prediction.py','scripts/collect_tangent_prediction.py','wildfire_lab/tangent_inputs.py',
    'wildfire_lab/tangent_prediction.py','wildfire_lab/tangent_checks.py','wildfire_lab/geometry_inputs.py',
    'wildfire_lab/ridge_kernel.py','wildfire_lab/ridge_checks.py','wildfire_lab/encoding_screen.py','wildfire_lab/kernel.py',
    'wildfire_lab/evaluation.py','experiments/tangent_prediction.json','pyproject.toml','uv.lock']


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',type=Path,default=ROOT/'.cache/wildfire/tangent-prediction')
    args=parser.parse_args();plan=json.loads((ROOT/'experiments/tangent_prediction.json').read_text())
    assert not any(plan[k] for k in ['new_state_preparations','pair_circuits','shots','hardware','final_test_access'])
    assert len(plan['seeds'])*(len(plan['classical_controls'])+len(plan['angle_scales']))<=plan['max_predictor_fits']
    assert 2*len(plan['seeds'])<=plan['max_primal_reference_solves']
    commit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip();hashes={}
    for name in RECIPES:
        raw=(ROOT/name).read_bytes();assert raw==subprocess.check_output(['git','show',f'{commit}:{name}'],cwd=ROOT),name;hashes[name]=sha(ROOT/name)
    intent=dict(plan=plan,git_commit=commit,recipe_sha256=hashes,started_utc=datetime.now(timezone.utc).isoformat())
    args.output.mkdir(parents=True,exist_ok=True)
    with (args.output/'intent.json').open('x') as f:json.dump(intent,f,indent=2)
    outcome=dict(status='running',intent=intent,seeds=[]);start=time.perf_counter()
    def save():
        tmp=args.output/'outcome.tmp';tmp.write_text(json.dumps(outcome,indent=2)+'\n');os.replace(tmp,args.output/'outcome.json')
    def timeout(*_):raise TimeoutError('Tangent-control wall budget reached')
    signal.signal(signal.SIGALRM,timeout);signal.alarm(plan['max_wall_seconds'])
    try:
        parent,samples=load(ROOT,plan)
        for sample in samples:outcome['seeds'].append(run(sample,plan));save()
        outcome.update(status='complete',review=review(outcome['seeds'],plan),
            predictor_fits=sum(len(s['rows']) for s in outcome['seeds']),
            primal_reference_solves=sum('primal_coefficients' in row for s in outcome['seeds'] for row in s['rows']))
    except Exception as error:
        outcome.update(status='failed_preserved',error_type=type(error).__name__,error=str(error));raise
    finally:
        signal.alarm(0);outcome['seconds']=time.perf_counter()-start;save()
    print(json.dumps({k:outcome[k] for k in ['status','seconds','predictor_fits','primal_reference_solves','review']}))


if __name__=='__main__':main()

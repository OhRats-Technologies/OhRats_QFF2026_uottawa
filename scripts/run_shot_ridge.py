"""One exclusive finite-shot measurement-model ridge check; no circuit execution."""
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
from wildfire_lab.shot_ridge_inputs import load
from wildfire_lab.shot_ridge import run,review
from wildfire_lab.landmarks import pair_count

RECIPES=['scripts/run_shot_ridge.py','scripts/collect_shot_ridge.py','wildfire_lab/shot_ridge_inputs.py',
    'wildfire_lab/shot_ridge.py','wildfire_lab/landmark_noise.py','wildfire_lab/geometry_inputs.py',
    'wildfire_lab/ridge_kernel.py','wildfire_lab/ridge_checks.py','wildfire_lab/landmarks.py',
    'wildfire_lab/encoding_screen.py','wildfire_lab/evaluation.py','experiments/landmark_shot_ridge.json','pyproject.toml','uv.lock']


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',type=Path,default=ROOT/'.cache/wildfire/landmark-shot-ridge')
    args=parser.parse_args();plan=json.loads((ROOT/'experiments/landmark_shot_ridge.json').read_text())
    assert not any(plan[k] for k in ['new_quantum_states','pair_circuits_executed','hardware','final_test_access'])
    n=len(plan['seeds']);r=len(plan['noise_seeds'])*len(plan['shots'])
    assert n*(4+r)<=plan['max_predictor_fits'] and n*(2+r)<=plan['max_primal_reference_solves']
    commit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip();hashes={}
    for name in RECIPES:
        assert (ROOT/name).read_bytes()==subprocess.check_output(['git','show',f'{commit}:{name}'],cwd=ROOT),name
        hashes[name]=sha(ROOT/name)
    intent=dict(plan=plan,git_commit=commit,recipe_sha256=hashes,started_utc=datetime.now(timezone.utc).isoformat())
    args.output.mkdir(parents=True,exist_ok=True)
    with (args.output/'intent.json').open('x') as f:json.dump(intent,f,indent=2)
    outcome=dict(status='running',intent=intent,seeds=[]);start=time.perf_counter()
    def save():
        tmp=args.output/'outcome.tmp';tmp.write_text(json.dumps(outcome,indent=2)+'\n');os.replace(tmp,args.output/'outcome.json')
    def timeout(*_):raise TimeoutError('Shot-ridge wall budget reached')
    signal.signal(signal.SIGALRM,timeout);signal.alarm(plan['max_wall_seconds'])
    try:
        parent,samples=load(ROOT,plan)
        pairs=pair_count(parent['train_cap'],parent['validation_cap'],plan['landmarks'])
        assert pairs*n*r<=plan['max_binomial_pair_estimates']
        assert pairs*n*len(plan['noise_seeds'])*sum(plan['shots'])<=plan['max_modeled_shot_exposure']
        for sample in samples:outcome['seeds'].append(run(sample,plan,args.output));save()
        rows=[row for seed in outcome['seeds'] for row in seed['rows']]
        outcome.update(status='complete',review=review(outcome['seeds'],plan),predictor_fits=len(rows),
            primal_reference_solves=sum('primal_coefficients' in row for row in rows),
            binomial_pair_estimates=sum(row['kernel_diagnostic'].get('binomial_pair_estimates',0) for row in rows),
            modeled_shot_exposure=sum(row['kernel_diagnostic'].get('modeled_shot_exposure',0) for row in rows))
    except Exception as error:
        outcome.update(status='failed_preserved',error_type=type(error).__name__,error=str(error));raise
    finally:
        signal.alarm(0);outcome['seconds']=time.perf_counter()-start;save()
    print(json.dumps({k:outcome[k] for k in ['status','seconds','predictor_fits','primal_reference_solves','binomial_pair_estimates','modeled_shot_exposure','review']}))


if __name__=='__main__':main()

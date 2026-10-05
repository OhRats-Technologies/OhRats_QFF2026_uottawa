"""Collect shot-model ridge evidence without drawing, solving or circuit execution."""
import argparse
import hashlib
import json
import subprocess
import sys
import time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from wildfire_lab.geometry_inputs import sha
from wildfire_lab.shot_ridge_inputs import load
from wildfire_lab.shot_ridge import audit,review


def collect(cache,output):
    start=time.perf_counter();record=json.loads((cache/'outcome.json').read_text());intent=json.loads((cache/'intent.json').read_text())
    assert record['status']=='complete' and record['intent']==intent;plan=intent['plan'];commit=intent['git_commit']
    for name,expected in intent['recipe_sha256'].items():
        raw=subprocess.check_output(['git','show',f'{commit}:{name}'],cwd=ROOT);assert hashlib.sha256(raw).hexdigest()==expected,name
        if name.startswith('wildfire_lab/'):assert sha(ROOT/name)==expected,name
        if name=='experiments/landmark_shot_ridge.json':assert json.loads(raw)==plan
    parent,samples=load(ROOT,plan);assert len(samples)==len(record['seeds']);checks=[]
    for sample,row in zip(samples,record['seeds']):checks.append(audit(sample,row,plan,cache))
    assert sum(c['predictor_conditions'] for c in checks)==record['predictor_fits']<=plan['max_predictor_fits']
    assert sum(c['primal_reference_solves'] for c in checks)==record['primal_reference_solves']<=plan['max_primal_reference_solves']
    rows=[row for seed in record['seeds'] for row in seed['rows']]
    for field in ['binomial_pair_estimates','modeled_shot_exposure']:
        assert sum(row['kernel_diagnostic'].get(field,0) for row in rows)==record[field]<=plan['max_'+field]
    assert record['seconds']<=plan['max_wall_seconds'] and record['review']==review(record['seeds'],plan)
    seeds=[dict(**{k:v for k,v in s.items() if k!='rows'},rows=[{k:v for k,v in row.items() if k not in ['coefficients','primal_coefficients','predictions']} for row in s['rows']]) for s in record['seeds']]
    result=dict(status='audited_landmark_shot_ridge_model',opening_commit=commit,intent_sha256=sha(cache/'intent.json'),
        outcome_sha256=sha(cache/'outcome.json'),plan=plan,dataset_sha256=parent['dataset_sha256'],review=record['review'],seeds=seeds,checks=checks,
        runner_seconds=record['seconds'],audit_seconds=time.perf_counter()-start,**{k:record[k] for k in ['predictor_fits','primal_reference_solves','binomial_pair_estimates','modeled_shot_exposure']},
        new_quantum_states=0,pair_circuits_executed=0,hardware_jobs_submitted=0,individually_executed_shots=0,audit_draws=0,audit_solves=0,final_test_access=False,
        audit_recipe_sha256={n:sha(ROOT/n) for n in ['scripts/collect_shot_ridge.py','wildfire_lab/shot_ridge.py','wildfire_lab/shot_ridge_inputs.py','wildfire_lab/landmark_noise.py']})
    header={k:v for k,v in result.items() if k!='seeds'};output.parent.mkdir(parents=True,exist_ok=True)
    output.write_text(json.dumps(header,separators=(',',':'))[:-1]+',"seeds":[\n'+',\n'.join(json.dumps(s,separators=(',',':')) for s in seeds)+'\n]}\n')
    print(json.dumps({k:result[k] for k in ['status','runner_seconds','audit_seconds','predictor_fits','primal_reference_solves','binomial_pair_estimates','modeled_shot_exposure','review']}));return result


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--cache',type=Path,default=ROOT/'.cache/wildfire/landmark-shot-ridge')
    parser.add_argument('--output',type=Path,default=ROOT/'docs/results/landmark-shot-ridge.json')
    args=parser.parse_args();collect(args.cache.resolve(),args.output)

"""Verify saved tangent/quantum ridge predictions without new fits or states."""
import argparse
import hashlib
import json
import subprocess
import sys
import time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from wildfire_lab.geometry_inputs import sha
from wildfire_lab.tangent_inputs import load
from wildfire_lab.tangent_checks import validate
from wildfire_lab.tangent_prediction import review


def collect(cache,output):
    start=time.perf_counter();record=json.loads((cache/'outcome.json').read_text());intent=json.loads((cache/'intent.json').read_text())
    assert record['status']=='complete' and record['intent']==intent;plan=intent['plan'];commit=intent['git_commit']
    for name,expected in intent['recipe_sha256'].items():
        raw=subprocess.check_output(['git','show',f'{commit}:{name}'],cwd=ROOT);assert hashlib.sha256(raw).hexdigest()==expected,name
        if name.startswith('wildfire_lab/'):assert sha(ROOT/name)==expected,name
        if name=='experiments/tangent_prediction.json':assert json.loads(raw)==plan
    parent,samples=load(ROOT,plan);assert len(samples)==len(record['seeds']);checks=[]
    for sample,row in zip(samples,record['seeds']):checks.append(validate(sample,row,plan))
    assert sum(c['predictor_conditions'] for c in checks)==record['predictor_fits']<=plan['max_predictor_fits']
    assert sum(c['primal_reference_solves'] for c in checks)==record['primal_reference_solves']<=plan['max_primal_reference_solves']
    assert record['seconds']<=plan['max_wall_seconds'] and record['review']==review(record['seeds'],plan)
    seeds=[]
    for row in record['seeds']:
        public={k:v for k,v in row.items() if k!='rows'}
        public['rows']=[{k:v for k,v in r.items() if k not in ['coefficients','primal_coefficients','predictions']} for r in row['rows']];seeds.append(public)
    result=dict(status='audited_tangent_predictive_control',opening_commit=commit,intent_sha256=sha(cache/'intent.json'),
        outcome_sha256=sha(cache/'outcome.json'),plan=plan,parent_geometry_outcome_sha256=plan['parent_geometry_outcome_sha256'],
        dataset_sha256=parent['dataset_sha256'],review=record['review'],seeds=seeds,checks=checks,runner_seconds=record['seconds'],
        audit_seconds=time.perf_counter()-start,predictor_fits=record['predictor_fits'],primal_reference_solves=record['primal_reference_solves'],
        audit_predictor_fits=0,new_state_preparations=0,pair_circuits_executed=0,shots_executed=0,hardware_jobs_submitted=0,
        final_test_access=False,audit_recipe_sha256={n:sha(ROOT/n) for n in ['scripts/collect_tangent_prediction.py','wildfire_lab/tangent_checks.py','wildfire_lab/tangent_inputs.py']},limitations=plan['interpretation'])
    output.parent.mkdir(parents=True,exist_ok=True);header={k:v for k,v in result.items() if k!='seeds'}
    output.write_text(json.dumps(header,separators=(',',':'))[:-1]+',"seeds":[\n'+',\n'.join(json.dumps(r,separators=(',',':')) for r in seeds)+'\n]}\n')
    print(json.dumps({k:result[k] for k in ['status','runner_seconds','audit_seconds','predictor_fits','primal_reference_solves','review']}));return result


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--cache',type=Path,default=ROOT/'.cache/wildfire/tangent-prediction')
    parser.add_argument('--output',type=Path,default=ROOT/'docs/results/tangent-prediction.json')
    args=parser.parse_args();collect(args.cache.resolve(),args.output)

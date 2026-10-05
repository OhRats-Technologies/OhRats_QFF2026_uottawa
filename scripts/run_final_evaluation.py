"""One committed final protocol, one held-out evaluation; never submits hardware."""
import argparse
import hashlib
import json
import sys
import time
from datetime import datetime,timezone
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from wildfire_lab.final_gate import validate_plan,reserve
from wildfire_lab.final_features import preflight,held_out
from wildfire_lab.group_screen import run as groups
from wildfire_lab.combination_screen import run as combinations
from wildfire_lab.final_checks import validate


def evaluate(train,test,plan):
    if set(train.incident_id)&set(test.incident_id):raise ValueError('Train/test identities overlap')
    if train.year.max()>2018 or test.year.min()<2019 or test.year.max()>2024:raise ValueError('Final year windows invalid')
    full=groups(train,test,plan,plan['seeds'][0])
    capped=[]
    for seed in plan['seeds']:capped.extend(combinations(train,test,plan,seed))
    return dict(full_training_models=full,capped_crossed_matrix=capped)


def run(plan_path):
    total=time.perf_counter();plan_path=plan_path.resolve()
    plan=json.loads(plan_path.read_text());validate_plan(plan)
    cache=ROOT/'.cache/wildfire/final-test'
    if (cache/'intent.json').exists():raise FileExistsError('Final opening already exists; preserve it and collect the saved outcome')
    train,manifest,sources=preflight(plan,ROOT)
    preflight_seconds=time.perf_counter()-total
    recipes=[Path(__file__),ROOT/'uv.lock',ROOT/'pyproject.toml',*sorted((ROOT/'wildfire_lab').glob('*.py'))]
    plan,intent=reserve(plan_path,cache,ROOT,recipes)
    record=dict(stage='final_evaluation',status='running',plan=plan,intent=intent,training_dataset=manifest,
                final_test_opened=True,hardware_jobs_submitted=0,rows={})
    try:
        start=time.perf_counter();test,metadata=held_out(plan,manifest,sources)
        record['feature_join_seconds']=time.perf_counter()-start
        test.to_csv(cache/'features.csv',index=False)
        metadata['data_sha256']=hashlib.sha256((cache/'features.csv').read_bytes()).hexdigest()
        record['test_dataset']=metadata
        start=time.perf_counter();record['rows']=evaluate(train,test,plan)
        record['model_seconds']=time.perf_counter()-start
        if any(hashlib.sha256((ROOT/path).read_bytes()).hexdigest()!=digest for path,digest in intent['recipe_sha256'].items()):
            raise RuntimeError('Final recipe changed during execution')
        record.update(status='complete',quality_checks=dict(identities_disjoint=True,years_disjoint=True,committed_protocol=True,frozen_recipe=True,no_new_hardware=True))
        record['recomputed_checks']=validate(record,train,test)
    except Exception as error:
        record.update(status='failed',error=str(error));raise
    finally:
        record.update(preflight_seconds=preflight_seconds,total_seconds=time.perf_counter()-total,finished_utc=datetime.now(timezone.utc).isoformat())
        with (cache/'outcome.json').open('x') as stream:json.dump(record,stream,indent=2);stream.write('\n')
    print(cache/'outcome.json')
    print(json.dumps({k:record[k] for k in ['status','preflight_seconds','feature_join_seconds','model_seconds','total_seconds']},indent=2))


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--plan',type=Path,default=ROOT/'experiments/final_evaluation.json')
    args=parser.parse_args();run(args.plan)

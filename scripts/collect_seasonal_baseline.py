"""Reconstruct saved baseline predictions and metrics without fitting."""
import argparse
import hashlib
import json
import subprocess
import sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))


def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--input',type=Path,default=ROOT/'.cache/wildfire/seasonal-baseline')
    parser.add_argument('--output',type=Path,default=ROOT/'docs/results/seasonal-baseline.json')
    args=parser.parse_args();intent=json.loads((args.input/'intent.json').read_text())
    outcome=json.loads((args.input/'outcome.json').read_text());plan=json.loads((ROOT/'experiments/seasonal_baseline.json').read_text())
    assert outcome['status']=='complete' and outcome['intent']==intent and intent['plan']==plan
    for name,digest in intent['recipe_hashes'].items():
        assert hashlib.sha256(subprocess.check_output(['git','show',intent['git_commit']+':'+name],cwd=ROOT)).hexdigest()==digest,name
    source=ROOT/plan['dataset']/'features.csv';assert sha(source)==plan['dataset_sha256']
    import numpy as np
    import pandas as pd
    from wildfire_lab.seasonal_baseline import validate
    checks=validate(pd.read_csv(source),plan,outcome['rows'])
    reference=json.loads((ROOT/plan['reference_evidence']).read_text())
    original=next(m for s in reference['studies'] for m in s['models'] if m['name']==plan['reference_model'])
    combined=[r for r in outcome['rows'] if r['group']=='geography_season']
    deltas={str(r['fold']):r['metric']['average_precision']-original['condition_average_precision'][str(r['fold'])] for r in combined}
    reference_matches=all(abs(v)<=plan['reference_AP_atol'] for v in deltas.values())
    means={g:{k:float(np.mean([r['metric'][k] for r in outcome['rows'] if r['group']==g]))
              for k in ('average_precision','roc_auc','brier','prevalence')} for g in plan['feature_groups']}
    public=dict(status='audited_training_only_controls',plan=plan,recipe_commit=intent['git_commit'],
        recipe_hashes=intent['recipe_hashes'],outcome_sha256=sha(args.input/'outcome.json'),intent_sha256=sha(args.input/'intent.json'),
        collector_recipe_sha256={n:sha(ROOT/n) for n in ['scripts/collect_seasonal_baseline.py','wildfire_lab/seasonal_baseline.py']},
        runner_seconds=outcome['seconds'],checks=checks,reference_evidence_sha256=sha(ROOT/plan['reference_evidence']),
        combined_reference_ap_deltas=deltas,combined_reference_matches=reference_matches,means=means,
        rows=[{k:v for k,v in r.items() if k not in ('predictions','parameters')} for r in outcome['rows']],
        limitations='Same recorded-fire cohort/years, deterministic folds, no seed replications or final-year reads. Different feature counts are declared groups. Read-only parameter reconstruction is not proof of historical source availability or causality.')
    args.output.write_text(json.dumps(public,indent=2)+'\n')
    print(json.dumps(dict(status=public['status'],means=means,combined_reference_matches=reference_matches)))


if __name__=='__main__':main()

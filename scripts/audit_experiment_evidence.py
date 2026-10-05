"""Audit saved local experiment inputs/budgets and recoverable Git recipe hashes."""
import argparse
import hashlib
import json
import subprocess
import sys
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from wildfire_lab.evidence_checks import validate


def audit(cache,output):
    feature_paths={p.parent.name:p.parent for p in (cache/'features').glob('*/*/manifest.json')}
    results=[];blobs={}
    def blob_hash(commit,path):
        key=(commit,path)
        if key not in blobs:
            result=subprocess.run(['git','show',f'{commit}:{path}'],cwd=ROOT,capture_output=True)
            blobs[key]=hashlib.sha256(result.stdout).hexdigest() if result.returncode==0 else None
        return blobs[key]
    for path in sorted((cache/'experiments').glob('*/attempt-*-outcome.json')):
        record=json.loads(path.read_text())
        entry=dict(attempt=record['id'],study=record['plan']['id'],status=record['status'],outcome_sha256=hashlib.sha256(path.read_bytes()).hexdigest())
        if record['status']=='complete':
            reservation=json.loads(path.with_name(path.name.replace('-outcome','')).read_text())
            entry['checks']=validate(record,reservation,feature_paths[record['dataset']['fingerprint']])
            changed=[p for p,h in record['code_hashes'].items() if blob_hash(reservation['git_commit'],p)!=h]
            missing=[]
            for p in changed:
                digest=record['code_hashes'][p]
                commits=subprocess.check_output(['git','log','--format=%H','--',p],cwd=ROOT).decode().splitlines()
                if not any(blob_hash(commit,p)==digest for commit in commits):missing.append(p)
            entry.update(recipe_matches_reserved_commit=not changed,recipe_hashes_recoverable_in_git=not missing,unrecoverable_recipe_paths=missing,
                         seconds=record['seconds'],annotation_present=(cache/'annotations'/f"{record['id']}.json").exists())
        results.append(entry)
    result=dict(status='audited',final_test_performance_sealed=True,attempts=len(results),
                completed_attempts=sum(r['status']=='complete' for r in results),
                measured_attempt_wall_seconds=sum(r.get('seconds',0) for r in results),
                limitations='Metadata/input audit does not recompute fitted predictions or reproduce hardware/noise. Per-file Git recovery does not assert all versions belong to one commit. Annotation flags must be read before using corrected metadata.',results=results)
    output.parent.mkdir(parents=True,exist_ok=True)
    output.write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({k:v for k,v in result.items() if k!='results'},indent=2))
    print('unrecoverable recipes',sum(not r.get('recipe_hashes_recoverable_in_git',True) for r in results))


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--cache',type=Path,default=ROOT/'.cache/wildfire')
    parser.add_argument('--output',type=Path,default=ROOT/'docs/data/experiment_audit.json')
    args=parser.parse_args();audit(args.cache,args.output)

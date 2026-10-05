"""Collect training-only geography of fixed weather/woodland cohort exclusions."""
import argparse
import csv
import hashlib
import io
import json
import math
import subprocess
import sys
import time
from datetime import datetime,timezone
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from wildfire_lab.label_quality import geographic_retention,select_cohort
from wildfire_lab.nfdb import incidents


def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()


def collect(root,config):
    start=time.perf_counter();plan=json.loads(config.read_text())
    if plan['status']!='frozen_training_only_source_audit':raise ValueError('Unfrozen geography plan')
    parent=root/plan['parent_config'];evidence=root/plan['parent_evidence']
    if sha(parent)!=plan['parent_config_sha256'] or sha(evidence)!=plan['parent_evidence_sha256']:
        raise ValueError('Changed parent recipe/evidence')
    recipe=json.loads(parent.read_text());reference=json.loads(evidence.read_text())
    if recipe['years'][1]>plan['max_training_year'] or plan['max_training_year']>2018:
        raise ValueError('Training-period geography only')
    archive=root/recipe['source_archive']
    if sha(archive)!=recipe['source_sha256']:raise ValueError('Changed NFDB snapshot')
    accepted,_=incidents(archive,recipe['agency'],*recipe['years'],float(recipe['target_threshold_ha']))
    source={row['incident_id']:row for row in accepted}
    if len(source)!=len(accepted) or any(not recipe['years'][0]<=r['year']<=recipe['years'][1] for r in accepted):
        raise ValueError('Duplicate or non-training source identity')
    cohorts={};provenance={}
    for name,spec in recipe['cohorts'].items():
        dataset=root/spec['dataset'];manifest=json.loads((dataset/'manifest.json').read_text());raw=(dataset/'features.csv').read_bytes()
        if hashlib.sha256(raw).hexdigest()!=spec['sha256'] or manifest['data_sha256']!=spec['sha256']:
            raise ValueError('Changed cohort table')
        if manifest['protocol']['years']!=recipe['years'] or manifest['protocol']['source_sha256']!=recipe['source_sha256']:
            raise ValueError('Changed cohort source/window')
        rows=list(csv.DictReader(io.StringIO(raw.decode('utf-8'))))
        cohorts[name]=select_cohort(source,rows,recipe['years'])
        if len(cohorts[name])!=manifest['rows']:raise ValueError('Changed cohort count')
        for row in rows:
            original=source[row['incident_id']]
            if any(not math.isclose(float(row[field]),original[field],rel_tol=0,abs_tol=1e-12) for field in ['latitude','longitude']):
                raise ValueError('Changed reported coordinate')
        provenance[name]=dict(data_sha256=spec['sha256'],manifest_sha256=sha(dataset/'manifest.json'))
    stages=dict(weather=geographic_retention(source,cohorts['weather_matched'],plan['latitude_edges']),
        woodland=geographic_retention(cohorts['weather_matched'],cohorts['fixed_cover_matched'],plan['latitude_edges']))
    for name,stage in stages.items():
        for label,row in stage['by_target'].items():
            if any(row[field]!=reference['retention'][name][label][field] for field in ['before_rows','retained_rows','excluded_rows']):
                raise ValueError('Does not reproduce prior class counts')
    return dict(status='audited_training_cohort_geography',created_utc=datetime.now(timezone.utc).isoformat(),
        code_commit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=root,text=True).strip(),
        recipe_sha256={n:sha(root/n) for n in ['scripts/audit_cohort_geography.py','wildfire_lab/label_quality.py','wildfire_lab/nfdb.py']},
        config_sha256=sha(config),plan=plan,parent_source_sha256=recipe['source_sha256'],years=recipe['years'],
        cohort_provenance=provenance,stages=stages,seconds=time.perf_counter()-start,
        model_fits=0,quantum_calls=0,final_test_access=False,
        limitations=['Approximate agency-associated coordinates do not certify location accuracy or province membership.',
            'Latitude-associated exclusions do not establish station availability, missing-month causes or random sampling.',
            'Coarse latitude bands aggregate different years and locations; rates are descriptive, not independent probabilities.',
            'Only training years are described; no source, target, feature or final model changes.'])


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--config',type=Path,default=ROOT/'configs/wildfires/cohort_geography.json')
    parser.add_argument('--output',type=Path,default=ROOT/'docs/data/cohort_geography.json')
    args=parser.parse_args();result=collect(ROOT,args.config)
    args.output.parent.mkdir(parents=True,exist_ok=True);args.output.write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({name:{key:stage[key] for key in ['before','retained','excluded']} for name,stage in result['stages'].items()}))

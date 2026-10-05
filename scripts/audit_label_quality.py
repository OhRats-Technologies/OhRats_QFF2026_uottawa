"""Collect training-only reported-size granularity, boundary and cohort counts."""
import argparse
import csv
import hashlib
import io
import json
import subprocess
import sys
from datetime import datetime,timezone
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from wildfire_lab.label_quality import training_sizes,select_cohort,summarize,retention


def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()


def evidence_text(value,depth=0):
    """Keep each aggregate list record on one readable line."""
    prefix='  '*depth
    if isinstance(value,dict):
        return '{\n'+',\n'.join(prefix+'  '+json.dumps(k)+': '+evidence_text(v,depth+1) for k,v in value.items())+'\n'+prefix+'}'
    if isinstance(value,list) and value and isinstance(value[0],dict):
        return '[\n'+',\n'.join(prefix+'  '+json.dumps(row) for row in value)+'\n'+prefix+']'
    return json.dumps(value)


def collect(root,config):
    plan=json.loads(config.read_text());archive=root/plan['source_archive']
    if sha(archive)!=plan['source_sha256']:raise ValueError('Changed NFDB snapshot')
    source,excluded=training_sizes(archive,plan);cohorts={'eligible_nfdb':source};provenance={}
    for name,spec in plan['cohorts'].items():
        dataset=root/spec['dataset'];manifest=json.loads((dataset/'manifest.json').read_text());raw=(dataset/'features.csv').read_bytes()
        if hashlib.sha256(raw).hexdigest()!=spec['sha256'] or manifest['data_sha256']!=spec['sha256']:raise ValueError('Changed cohort')
        assert manifest['protocol']['years']==plan['years'] and manifest['protocol']['source_sha256']==plan['source_sha256']
        rows=csv.DictReader(io.StringIO(raw.decode('utf-8')))
        cohorts[name]=select_cohort(source,rows,plan['years'])
        assert len(cohorts[name])==manifest['rows']
        provenance[name]=dict(dataset=spec['dataset'],data_sha256=spec['sha256'],manifest_sha256=sha(dataset/'manifest.json'))
    return dict(status='audited_training_size_boundary',created_utc=datetime.now(timezone.utc).isoformat(),
        code_commit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=root,text=True).strip(),
        recipe_sha256={n:sha(root/n) for n in ['scripts/audit_label_quality.py','wildfire_lab/label_quality.py','wildfire_lab/nfdb.py']},
        config_sha256=sha(config),source_sha256=plan['source_sha256'],plan=plan,cohort_provenance=provenance,
        exclusions=excluded,cohorts={name:summarize(rows,plan) for name,rows in cohorts.items()},
        retention=dict(weather=retention(source,cohorts['weather_matched']),
                       woodland=retention(cohorts['weather_matched'],cohorts['fixed_cover_matched'])),
        model_fits=0,quantum_calls=0,final_test_access=False,
        limitations=['Numeric multiples are recording patterns, not measured precision or uncertainty.',
            'Boundary bands do not estimate label error; descriptive thresholds do not select a replacement target.',
            'Annual prevalence varies with recorded incidents and selection; no causal or completeness conclusion.',
            'Reported size is not guaranteed final area; zero is retained by the frozen nonnegative-size rule.'])


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--config',type=Path,default=ROOT/'configs/wildfires/label_quality.json')
    parser.add_argument('--output',type=Path,default=ROOT/'docs/data/label_quality.json')
    args=parser.parse_args();result=collect(ROOT,args.config)
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(evidence_text(result)+'\n')
    print(json.dumps({n:{k:r[k] for k in ['rows','positive_rows','positive_fraction','zero_size_rows','exact_threshold_rows']} for n,r in result['cohorts'].items()}))

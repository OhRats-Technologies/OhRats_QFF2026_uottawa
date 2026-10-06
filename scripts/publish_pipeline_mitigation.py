"""Publish compact saved mitigation evidence; never run circuits or fit models."""
import argparse
import hashlib
import json
from pathlib import Path
import sys
from zipfile import ZipFile, ZIP_DEFLATED
import numpy as np
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from wildfire_lab.mitigation_collect import collect
from wildfire_lab.annual_classical import errors

def publish(output):
    audit = collect(ROOT,output)
    data = json.loads((output/'evidence.json').read_text())
    rows = data['predictions']
    control_checks = {}
    for row in rows:
        for key,value in errors(np.array(data['actual_ha']),np.array(row['predicted_ha'])).items():
            if not np.isclose(value,row[key]):
                raise ValueError('Stored metric differs from saved prediction')
    raw_y = np.expm1(np.asarray(data['scaled_targets'])*data['y_scale']+data['y_mean'])
    mean = next(row for row in rows if row['label']=='training_mean')
    np.testing.assert_allclose(mean['predicted_ha'],np.repeat(raw_y.mean(),len(data['actual_ha'])))
    control_checks.update(all_prediction_metrics_checked=len(rows), training_mean_reconstructed=True,
                          rbf_predictor_equation_reconstructed=False,
                          limitation='RBF control predictions/metrics are retained; its fitted coefficients were not saved.')
    summaries = []
    for kind in ['kernel','selector','control']:
        for label in dict.fromkeys(r['label'] for r in rows if r['kind']==kind):
            matching = [r for r in rows if r['kind']==kind and r['label']==label]
            summary = dict(kind=kind,label=label,records=len(matching))
            for metric in ['mae_ha','rmse_ha','train_kernel_rmse','cross_kernel_rmse',
                           'feasible_fraction','logical_feasible_probability','gap_to_exact',
                           'negative_spectral_mass','effective_rank','exact_alignment']:
                values = [r[metric] for r in matching if metric in r]
                if values:
                    summary[metric] = dict(mean=float(np.mean(values)),minimum=min(values),maximum=max(values))
            if kind=='selector':
                summary['selected_subsets'] = [r['selected_subset'] for r in matching]
            summaries.append(summary)
    target = ROOT/'docs/data/pipeline_mitigation_evidence.zip'
    members = ['evidence.json','intent.json','manifest.json','kernel_base.qpy','selector_base.qpy','audit.json']
    with ZipFile(target,'w',compression=ZIP_DEFLATED) as archive:
        for name in members:
            archive.write(output/name,name)
    result = dict(study=data['plan']['study'],wall_seconds=data['wall_seconds'],
                  train_years=data['train_years'],validation_years=data['validation_years'],
                  seeds=data['plan']['seeds'],predictor_fits=data['predictor_fits'],
                  prediction_records=len(rows),collection=audit,control_checks=control_checks,
                  kernel_resources=data['kernel_resources'],selector_resources={
                      k:v for k,v in data['selector_resources'].items() if k!='objective'},
                  summaries=summaries,bundle=str(target.relative_to(ROOT)),
                  bundle_sha256=hashlib.sha256(target.read_bytes()).hexdigest(),
                  bundle_bytes=target.stat().st_size,hardware_jobs_submitted=0,final_test_accessed=False)
    result['total_local_shots'] = (data['kernel_resources']['forward_shots']+
        data['selector_resources']['forward_shots']+12*data['plan']['calibration_shots'])
    path = ROOT/'docs/results/pipeline-mitigation.json'
    path.write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(dict(summary=str(path.relative_to(ROOT)),bundle_bytes=target.stat().st_size)))

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',type=Path,required=True)
    publish(parser.parse_args().output)


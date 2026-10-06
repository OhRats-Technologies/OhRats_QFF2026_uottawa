"""Publish portable, hash-linked forest-study evidence and descriptive summaries."""
import json
from zipfile import ZipFile, ZipInfo, ZIP_DEFLATED
import numpy as np
import pandas as pd
from wildfire_lab.forest_run import digest, write
from wildfire_lab.forest_collect import audit as audit_primary
from wildfire_lab.selector_collect import audit, audit_order

STUDIES = {'forest-expansion':('forest-expansion-v1',audit_primary),
           'forest-order-controls':('forest-order-controls-v1',audit_order),
           'selector-scaling':('selector-scaling-v1',audit)}


def summary(evidence):
    rows = pd.DataFrame(evidence['rows'])
    axes = ['pool_size','selector','model'] if 'cohorts' in evidence else ['condition','model']
    aggregate = rows.groupby(axes).agg(mae_ha=('mae_ha','mean'),rmse_ha=('rmse_ha','mean')).reset_index()
    result = dict(aggregate=aggregate.to_dict('records'),seconds=evidence['seconds'],
                  model_fits=evidence['model_fits'],pair_circuits=evidence['pair_circuits'])
    if 'cohorts' in evidence:
        samples = pd.DataFrame(dict(pool_size=len(c['features']),**{k:r[k] for k in
                                    ['policy','shots','gap','optimum_found']})
                               for c in evidence['cohorts'] for r in c['samples'])
        sampling = samples.groupby(['pool_size','policy','shots']).agg(
            mean_gap=('gap','mean'),trials=('gap','size'),optimum_wins=('optimum_found','sum')).reset_index()
        result['sampling'] = sampling.to_dict('records')
        result['resources'] = [dict(pool_size=len(c['features']),fold=c['fold'],
                                   feasible_subsets=c['feasible_subsets'],
                                   enumeration_seconds=c['enumeration_seconds'],
                                   mixer_setup_seconds=c['mixer_setup_seconds'],
                                   optimizer_seconds={k:v['seconds'] for k,v in c['policies'].items()},
                                   optimizer_calls={k:v['objective_calls'] for k,v in c['policies'].items()})
                               for c in evidence['cohorts']]
        result['classical_sample_draws'] = evidence['classical_sample_draws']
    return result


def publish(root):
    for name,(cache,checker) in STUDIES.items():
        path = root/'.cache/wildfire'/cache/'evidence.json'
        evidence = json.loads(path.read_text())
        receipt = checker(root,evidence)
        bundle = root/'docs/data'/f'{name}-evidence.zip'
        info = ZipInfo('evidence.json',date_time=(1980,1,1,0,0,0))
        info.compress_type = ZIP_DEFLATED
        with ZipFile(bundle,'w') as archive:
            archive.writestr(info,path.read_bytes())
        result = dict(status='published',study=name,bundle=str(bundle.relative_to(root)),
                      bundle_sha256=digest(bundle),evidence_sha256=digest(path),
                      audit=receipt,**summary(evidence),final_test_accessed=False,hardware_jobs=0)
        write(root/'docs/results'/f'{name}.json',result)
    return {name:json.loads((root/'docs/results'/f'{name}.json').read_text()) for name in STUDIES}


def collect(root, name, output):
    """Read only published bytes; no model/state/draw execution or source requests."""
    _, checker = STUDIES[name]
    result = json.loads((root/'docs/results'/f'{name}.json').read_text())
    bundle = root/result['bundle']
    assert digest(bundle)==result['bundle_sha256']
    with ZipFile(bundle) as archive:
        assert archive.namelist()==['evidence.json']
        raw = archive.read('evidence.json')
    import hashlib
    assert hashlib.sha256(raw).hexdigest()==result['evidence_sha256']
    evidence = json.loads(raw)
    receipt = checker(root,evidence)
    output.mkdir(parents=True,exist_ok=False)
    (output/'evidence.json').write_bytes(raw)
    write(output/'audit.json',receipt)
    return receipt

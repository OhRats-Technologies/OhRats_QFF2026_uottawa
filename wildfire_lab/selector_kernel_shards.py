"""Declared scheduler correction: unchanged kernel circuits in per-subset jobs."""
import json
from pathlib import Path
from qiskit import qpy
from wildfire_lab.mitigation_hardware import service,sha,write,now
from wildfire_lab.selector_hardware import submit as submit_pair, collect as collect_pair
from wildfire_lab.selector_kernel_analysis import analyze as analyze_pair


def prepare(root,output):
    path = root/'experiments/selector_kernel_shards.json'
    plan = json.loads(path.read_text())
    parent = root/plan['failed_namespace']
    receipt = json.loads((parent/'prepared.json').read_text())
    assert sha(parent/'circuits.qpy') == receipt['circuits_sha256']
    assert sha(root/plan['parent_plan']) == receipt['plan_sha256']
    for arm in plan['arms']:
        assert json.loads((parent/f'{arm}_status.json').read_text())['status'] == 'ERROR'
        assert not (parent/f'{arm}_counts.json').exists()
    svc = service()
    svc.backend(plan['backend'])
    usage = svc.usage()
    assert usage['usage_remaining_seconds'] >= plan['reserve_seconds']
    output.mkdir(parents=True,exist_ok=False)
    write(output/'intent.json',dict(plan_sha256=sha(path),created_utc=now(),parent_prepared_sha256=sha(parent/'prepared.json')))
    write(output/'account_usage_before.json',usage)
    models = json.loads((parent/'models.json').read_text())
    assert sha(parent/'models.json') == receipt['models_sha256']
    with (parent/'circuits.qpy').open('rb') as stream:
        circuits = qpy.load(stream)
    for key in plan['model_keys']:
        indices = [i for i,r in enumerate(receipt['records']) if r.get('model_key') == key]
        indices += [len(circuits)-2,len(circuits)-1]
        assert len(indices) == plan['pubs_per_job'] < 1000
        child = output/key
        child.mkdir()
        with (child/'circuits.qpy').open('wb') as stream:
            qpy.dump([circuits[i] for i in indices],stream)
        write(child/'models.json',{key:models[key]})
        child_plan = dict(receipt['plan'],study=plan['study'],model_keys=[key],
                          max_execution_time_per_job_seconds=plan['max_execution_time_per_job_seconds'])
        prepared = dict(receipt,plan=child_plan,plan_relative_path=str(path.relative_to(root)),
                        plan_sha256=sha(path),circuits_sha256=sha(child/'circuits.qpy'),
                        models_sha256=sha(child/'models.json'),records=[receipt['records'][i] for i in indices],
                        prepared_utc=now(),code_sha256={p:sha(root/p) for p in
                          ['wildfire_lab/selector_kernel_shards.py','wildfire_lab/selector_hardware.py',
                           'scripts/run_selector_kernel_shards.py']})
        write(child/'prepared.json',prepared)
    write(output/'prepared.json',dict(plan=plan,plan_sha256=sha(path),monthly_remaining_before=usage['usage_remaining_seconds']))
    return dict(subsets=len(models),jobs=plan['max_jobs'],pubs_per_job=plan['pubs_per_job'],
                reserve_seconds=plan['reserve_seconds'],monthly_remaining_seconds=usage['usage_remaining_seconds'])


def submit(root,output):
    receipt = json.loads((output/'prepared.json').read_text())
    plan = receipt['plan']
    assert sha(root/'experiments/selector_kernel_shards.json') == receipt['plan_sha256']
    svc = service()
    svc.backend(plan['backend'])
    assert svc.usage()['usage_remaining_seconds'] >= plan['reserve_seconds']
    assert all(not (output/key/f'{arm}_intent.json').exists() for key in plan['model_keys'] for arm in plan['arms'])
    accepted = {}
    for key in plan['model_keys']:
        accepted[key] = submit_pair(root,output/key)
    return dict(accepted_subsets=list(accepted),accepted_jobs=2*len(accepted),per_job_cap_seconds=20)


def collect(output):
    plan = json.loads((output/'prepared.json').read_text())['plan']
    return {key:collect_pair(output/key) for key in plan['model_keys']}


def analyze(root,output):
    if (output/'analysis.json').exists():
        return json.loads((output/'analysis.json').read_text())
    receipt = json.loads((output/'prepared.json').read_text())
    plan = receipt['plan']
    # Pair analyzer publishes into this private scratch tree, never over the failure record.
    scratch = output/'publication'
    (scratch/'docs/results').mkdir(parents=True,exist_ok=True)
    shards = {key:analyze_pair(scratch,output/key) for key in plan['model_keys']}
    result = dict(status='collected',study=plan['study'],plan_sha256=receipt['plan_sha256'],
                  backend=plan['backend'],shards=shards,hardware_jobs=sum(s['hardware_jobs'] for s in shards.values()),
                  physical_shots=sum(s['physical_shots'] for s in shards.values()),
                  quantum_seconds_total=sum(s['quantum_seconds_total'] for s in shards.values()),
                  predictor_fits=sum(s['predictor_fits'] for s in shards.values()),
                  preserved_failure='docs/results/selector-hardware-kernels.json',final_test_accessed=False,
                  limitation='Same frozen kernels split after documented scheduler failure. Per-subset/arm calibration and execution times differ; one pair per subset, reused development years. No selection from prediction errors or quantum advantage.')
    write(output/'analysis.json',result)
    write(root/'docs/results/selector-hardware-kernel-shards.json',result)
    return {k:result[k] for k in ['status','hardware_jobs','physical_shots','quantum_seconds_total','predictor_fits']}

"""Small uniform-shot IBM jobs with exclusive intents and private identifiers."""
import json
import time
from qiskit import qpy
from qiskit_ibm_runtime.executor_sampler import Sampler
from wildfire_lab.mitigation_hardware import service, now, sha, write


def submit(root, output):
    receipt = json.loads((output/'prepared.json').read_text())
    plan = receipt['plan']
    assert sha(root/receipt['plan_path']) == receipt['plan_sha256']
    for name, expected in receipt['code_sha256'].items():
        assert sha(root/name) == expected
    svc = service(plan.get('credential_env', 'IBM_QUANTUM_API_TOKEN'),
                  plan.get('instance_env', 'IBM_QUANTUM_INSTANCE'))
    usage = svc.usage()
    reserve = sum(job['cap_seconds'] for job in receipt['jobs'])
    assert usage['usage_remaining_seconds'] >= max(reserve, plan.get('remaining_reserve_seconds', reserve))
    write(output/'submission_usage.json', usage)
    # A retry of the entry point cannot duplicate even an earlier accepted arm.
    assert all(not (output/job['label']/'submission_intent.json').exists()
               for job in receipt['jobs']), 'Existing intent: collect only'
    accepted = []
    backend = svc.backend(plan['backend'])
    for job in receipt['jobs']:
        child = output/job['label']
        assert sha(child/'circuits.qpy') == job['circuits_sha256']
        with (child/'circuits.qpy').open('rb') as stream:
            circuits = qpy.load(stream)
        enabled = job['arm'] == 'dd_twirl'
        options = dict(max_execution_time=job['cap_seconds'],
                       dynamical_decoupling=dict(enable=enabled, sequence_type='XpXm',
                                                skip_reset_qubits=True),
                       twirling=dict(enable_gates=enabled, enable_measure=enabled,
                                     num_randomizations=4 if enabled else 1,
                                     shots_per_randomization=job['shots']//4 if enabled else job['shots']))
        sampler = Sampler(mode=backend, options=options)
        with (child/'submission_intent.json').open('x') as stream:
            json.dump(dict(created_utc=now(), options=options, shots=job['shots'],
                           pubs=len(circuits)), stream)
        started = time.perf_counter()
        handle = sampler.run([(qc, None, job['shots']) for qc in circuits])
        write(child/'submitted.json', dict(job_id=handle.job_id(), accepted_utc=now(),
                                          roundtrip_seconds=time.perf_counter()-started))
        accepted.append(job['label'])
    return dict(accepted=accepted, configured_reserve_seconds=reserve)


def collect(output):
    receipt = json.loads((output/'prepared.json').read_text())
    plan = receipt['plan']
    svc = service(plan.get('credential_env', 'IBM_QUANTUM_API_TOKEN'),
                  plan.get('instance_env', 'IBM_QUANTUM_INSTANCE'))
    status = {}
    for job in receipt['jobs']:
        child = output/job['label']
        submitted = child/'submitted.json'
        if not submitted.exists():
            status[job['label']] = 'NOT_SUBMITTED'
            continue
        handle = svc.job(json.loads(submitted.read_text())['job_id'])
        state = str(handle.status()).upper()
        status[job['label']] = state
        write(child/'status.json', dict(status=state, observed_utc=now()))
        if state in {'DONE', 'ERROR', 'CANCELLED'} and not (child/'metrics.json').exists():
            write(child/'metrics.json', handle.metrics())
            write(child/'usage.json', handle.usage())
        if state == 'DONE' and not (child/'counts.json').exists():
            counts = [pub.data.meas.get_counts() for pub in handle.result()]
            assert len(counts) == len(job['records'])
            assert all(sum(record.values()) == job['shots'] for record in counts)
            write(child/'counts.json', dict(counts=counts, collected_utc=now()))
    return status

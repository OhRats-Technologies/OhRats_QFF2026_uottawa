"""Frozen larger-selector IBM acquisition with polynomial preparation and no retries."""
import json
import time
from zipfile import ZipFile
import numpy as np
from qiskit import QuantumCircuit, qpy
from qiskit.transpiler import generate_preset_pass_manager
from qiskit_ibm_runtime.executor_sampler import Sampler
from wildfire_lab.dicke_selector import circuit, preparation
from wildfire_lab.mitigation_hardware import service, measured_wires, now, sha, write


def parent(root, plan):
    index = json.loads((root/'docs/results/selector-scaling.json').read_text())
    bundle = root/index['bundle']
    assert sha(bundle)==index['bundle_sha256']
    with ZipFile(bundle) as archive:
        raw = archive.read('evidence.json')
    import hashlib
    assert hashlib.sha256(raw).hexdigest()==plan['parent_evidence_sha256']
    return json.loads(raw)


def compile_records(backend, logical, labels, shots):
    pm = generate_preset_pass_manager(backend=backend,optimization_level=3,seed_transpiler=137)
    circuits, records = [], []
    for qc, label in zip(logical,labels,strict=True):
        compiled = pm.run(qc)
        serial = 0.
        for item in compiled.data:
            if item.operation.name in {'barrier','delay'}:
                continue
            qubits = tuple(compiled.find_bit(q).index for q in item.qubits)
            serial += backend.target[item.operation.name][qubits].duration or 0.
        records.append(dict(label=label,depth=compiled.depth(),operations=dict(compiled.count_ops()),
                            measured_wires=measured_wires(compiled),serial_duration_seconds=serial))
        circuits.append(compiled)
    estimate = 2+sum((r['serial_duration_seconds']+backend.default_rep_delay)*shots for r in records)
    return circuits, records, estimate


def prepare(root, output):
    path = root/'experiments/selector_hardware.json'
    plan = json.loads(path.read_text())
    source = parent(root,plan)
    output.mkdir(parents=True,exist_ok=False)
    write(output/'intent.json',dict(plan_sha256=sha(path),created_utc=now()))
    svc = service()
    backend = svc.backend(plan['backend'])
    usage = svc.usage()
    write(output/'account_usage_before.json',usage)
    assert usage['usage_remaining_seconds']>=plan['max_reserved_qpu_seconds']
    logical, labels = [], []
    for cohort in source['cohorts']:
        if cohort['fold']!=plan['fold']:
            continue
        n = len(cohort['features'])
        obj = {k:np.array(v) if isinstance(v,list) else v for k,v in cohort['objective'].items()}
        for policy in ['uniform','optimized2']:
            qc = preparation(n,4) if policy=='uniform' else circuit(obj,cohort['policies'][policy]['parameters'])
            qc.measure_all()
            logical.append(qc)
            labels.append(dict(kind='selector',pool_size=n,policy=policy,counter_qubits=4 .bit_length()))
    compiled, records, estimate = compile_records(backend,logical,labels,plan['selector_shots'])
    calibration = []
    for record in list(records):
        wires = record['measured_wires']
        for bit in [0,1]:
            qc = QuantumCircuit(len(wires))
            if bit:
                qc.x(range(len(wires)))
            qc.measure_all()
            qc = generate_preset_pass_manager(backend=backend,initial_layout=wires,
                  optimization_level=1,seed_transpiler=137).run(qc)
            calibration.append(qc)
            records.append(dict(label=dict(kind='calibration',pool_size=record['label']['pool_size'],
                                           policy=record['label']['policy'],prepared_bit=bit),
                                depth=qc.depth(),operations=dict(qc.count_ops()),measured_wires=measured_wires(qc)))
    compiled.extend(calibration)
    estimate += len(calibration)*plan['selector_shots']*(backend.default_rep_delay+.00002)
    assert len(logical)==6 and len(compiled)==18
    assert estimate<=plan['max_execution_time_per_job_seconds']
    with (output/'circuits.qpy').open('wb') as stream:
        qpy.dump(compiled,stream)
    with (output/'logical.qpy').open('wb') as stream:
        qpy.dump(logical,stream)
    receipt = dict(stage='selector',plan=plan,plan_relative_path=str(path.relative_to(root)),
                   plan_sha256=sha(path),circuits_sha256=sha(output/'circuits.qpy'),records=records,
                   shots=plan['selector_shots'],backend=backend.name,prepared_utc=now(),
                   serial_estimated_qpu_seconds=estimate,monthly_remaining_before=usage['usage_remaining_seconds'],
                   code_sha256={p:sha(root/p) for p in ['wildfire_lab/selector_hardware.py',
                      'wildfire_lab/dicke_selector.py','scripts/run_selector_hardware.py']})
    write(output/'prepared.json',receipt)
    return dict(backend=backend.name,pubs=len(compiled),estimate_seconds=estimate,
                monthly_remaining_seconds=usage['usage_remaining_seconds'],
                selector_resources=[{k:r[k] for k in ['label','depth','operations']} for r in records[:6]])


def submit(root, output):
    receipt = json.loads((output/'prepared.json').read_text())
    plan = receipt['plan']
    assert sha(root/receipt['plan_relative_path'])==receipt['plan_sha256']
    assert sha(output/'circuits.qpy')==receipt['circuits_sha256']
    for path, expected in receipt['code_sha256'].items():
        assert sha(root/path)==expected
    svc = service()
    backend = svc.backend(plan['backend'])
    usage = svc.usage()
    assert usage['usage_remaining_seconds']>=2*plan['max_execution_time_per_job_seconds']
    with (output/'circuits.qpy').open('rb') as stream:
        circuits = qpy.load(stream)
    accepted = []
    for arm in ['raw','dd_twirl']:
        intent = output/f'{arm}_intent.json'
        if intent.exists():
            raise FileExistsError('Existing submission intent: collect only')
        enabled = arm=='dd_twirl'
        options = dict(max_execution_time=plan['max_execution_time_per_job_seconds'],
            dynamical_decoupling=dict(enable=enabled,sequence_type='XpXm',skip_reset_qubits=True),
            twirling=dict(enable_gates=enabled,enable_measure=enabled,
                          num_randomizations=4 if enabled else 1,
                          shots_per_randomization=receipt['shots']//4 if enabled else receipt['shots']))
        sampler = Sampler(mode=backend,options=options)
        write(intent,dict(created_utc=now(),arm=arm,options=options,pubs=len(circuits),shots=receipt['shots']))
        start = time.perf_counter()
        job = sampler.run([(qc,None,receipt['shots']) for qc in circuits])
        write(output/f'{arm}_submitted.json',dict(job_id=job.job_id(),accepted_utc=now(),
                    submission_roundtrip_seconds=time.perf_counter()-start))
        accepted.append(arm)
    return dict(accepted_arms=accepted,per_job_cap_seconds=plan['max_execution_time_per_job_seconds'])


def collect(output):
    receipt = json.loads((output/'prepared.json').read_text())
    svc = service()
    status = {}
    for arm in ['raw','dd_twirl']:
        saved = output/f'{arm}_submitted.json'
        if not saved.exists():
            status[arm]='NOT_SUBMITTED'
            continue
        job = svc.job(json.loads(saved.read_text())['job_id'])
        state = str(job.status()).upper()
        status[arm]=state
        write(output/f'{arm}_status.json',dict(status=state,observed_utc=now()))
        if state in {'DONE','ERROR','CANCELLED'}:
            write(output/f'{arm}_metrics.json',job.metrics())
            write(output/f'{arm}_usage.json',job.usage())
        if state=='DONE' and not (output/f'{arm}_counts.json').exists():
            counts = [r.data.meas.get_counts() for r in job.result()]
            assert len(counts)==len(receipt['records'])
            assert all(sum(c.values())==receipt['shots'] for c in counts)
            write(output/f'{arm}_counts.json',dict(counts=counts,collected_utc=now()))
    return status

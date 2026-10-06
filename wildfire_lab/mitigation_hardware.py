"""Budgeted IBM acquisition; private intents survive errors and never retry."""
from datetime import datetime, timezone
import hashlib
import json
import logging
import os
from pathlib import Path
import time
from zipfile import ZipFile
import numpy as np
from qiskit import QuantumCircuit, qpy
from qiskit.transpiler import generate_preset_pass_manager
from qiskit_ibm_runtime import QiskitRuntimeService
from qiskit_ibm_runtime.executor_sampler import Sampler

def now():
    return datetime.now(timezone.utc).isoformat()

def write(path,value):
    path.write_text(json.dumps(value,indent=2,default=str)+'\n')

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def service(token_env='IBM_QUANTUM_API_TOKEN', instance_env='IBM_QUANTUM_INSTANCE'):
    logging.getLogger('qiskit_ibm_runtime').setLevel(logging.ERROR)
    token = os.environ.get(token_env)
    if not token:
        raise ValueError('Requested IBM credential is absent')
    return QiskitRuntimeService(channel='ibm_quantum_platform',token=token,
                                instance=os.environ.get(instance_env) or 'auto')

def connected_path(backend,n):
    graph = {}
    for a,b in backend.coupling_map.get_edges():
        graph.setdefault(a,set()).add(b)
        graph.setdefault(b,set()).add(a)
    def search(path):
        if len(path)==n:
            return path
        for nxt in sorted(graph[path[-1]]):
            if nxt not in path:
                found=search(path+[nxt])
                if found:
                    return found
        return None
    for start in sorted(graph):
        found=search([start])
        if found:
            return found
    raise ValueError('No connected path of requested width')

def measured_wires(qc):
    mapping={}
    for item in qc.data:
        if item.operation.name=='measure':
            mapping[qc.find_bit(item.clbits[0]).index]=qc.find_bit(item.qubits[0]).index
    return [mapping[i] for i in range(len(mapping))]

def prepare(root,output,plan_path=None):
    plan_path=(plan_path or root/'experiments/annual_mitigation_ibm.json').resolve()
    plan=json.loads(plan_path.read_text())
    output.mkdir(parents=True,exist_ok=False)
    bundle=root/plan['parent']
    public=json.loads((root/'docs/results/pipeline-mitigation.json').read_text())
    if sha(bundle)!=public['bundle_sha256']:
        raise ValueError('Parent bundle changed')
    with ZipFile(bundle) as archive:
        evidence=archive.read('evidence.json')
        if hashlib.sha256(evidence).hexdigest()!=plan['parent_evidence_sha256']:
            raise ValueError('Parent evidence differs')
        (output/'parent.json').write_bytes(evidence)
        for name in ['kernel_base.qpy','selector_base.qpy']:
            (output/name).write_bytes(archive.read(name))
    backend=service(plan.get('credential_env','IBM_QUANTUM_API_TOKEN'),
                    plan.get('instance_env','IBM_QUANTUM_INSTANCE')).backend(plan['backend'])
    path=connected_path(backend,10)
    with (output/'kernel_base.qpy').open('rb') as stream:
        logical=qpy.load(stream)
    kernels=[]
    pm=generate_preset_pass_manager(backend=backend,initial_layout=path[:4],
                                   optimization_level=1,seed_transpiler=7)
    for qc in logical:
        qc.measure_all()
        kernels.append(pm.run(qc))
    wires=measured_wires(kernels[0])
    if any(measured_wires(qc)!=wires for qc in kernels):
        raise ValueError('Overlap circuits changed measured physical mapping')
    with (output/'selector_base.qpy').open('rb') as stream:
        selector=qpy.load(stream)[0]
    selector.measure_all()
    selector=generate_preset_pass_manager(backend=backend,initial_layout=path,
                 optimization_level=1,seed_transpiler=7).run(selector)
    calibration=[]
    for width,physical in [(4,wires),(10,measured_wires(selector))]:
        for bit in [0,1]:
            qc=QuantumCircuit(width)
            if bit:
                qc.x(range(width))
            qc.measure_all()
            calibration.append(generate_preset_pass_manager(backend=backend,
                initial_layout=physical,optimization_level=1,seed_transpiler=7).run(qc))
    circuits=kernels+[selector]+calibration
    with (output/'circuits.qpy').open('wb') as stream:
        qpy.dump(circuits,stream)
    # Conservative sum of instruction durations, rather than parallel critical paths.
    lengths=[]
    for qc in circuits:
        total=0.
        for item in qc.data:
            name=item.operation.name
            if name in {'barrier','delay'}:
                continue
            qubits=tuple(qc.find_bit(q).index for q in item.qubits)
            total+=backend.target[name][qubits].duration or 0.
        lengths.append(total)
    shots=[plan['kernel_shots']]*len(kernels)+[plan['selector_shots']]+[plan['calibration_shots']]*4
    estimate=2+sum((length+backend.default_rep_delay)*s for length,s in zip(lengths,shots))
    if estimate*2>50:
        raise ValueError('Conservative timing estimate exceeds budget margin')
    if estimate>plan['max_execution_time_per_job_seconds']:
        raise ValueError('Baseline estimate exceeds per-job cap')
    receipt=dict(plan=plan,plan_sha256=sha(plan_path),
                 plan_relative_path=str(plan_path.relative_to(root)),
                 code_sha256={p:sha(root/p) for p in ['wildfire_lab/mitigation_hardware.py',
                                                     'scripts/run_mitigation_hardware.py']},
                 parent_sha256=plan['parent_evidence_sha256'],circuits_sha256=sha(output/'circuits.qpy'),
                 backend=backend.name,kernel_pairs=len(kernels),shots_per_pub=shots,
                 qsvr_physical_qubits=wires,selector_physical_qubits=measured_wires(selector),
                 baseline_estimated_qpu_seconds_per_job=estimate,
                 conservative_combined_allowance_seconds=estimate*2,
                 num_qubits=backend.num_qubits,native_basis=sorted(backend.operation_names),
                 compiled_resources=[dict(depth=qc.depth(),operations=dict(qc.count_ops()),
                     serial_duration_seconds=length) for qc,length in zip(circuits,lengths)],
                 pending_backend_jobs=backend.status().pending_jobs,prepared_utc=now())
    write(output/'prepared.json',receipt)
    return {k:receipt[k] for k in ['backend','kernel_pairs','baseline_estimated_qpu_seconds_per_job','pending_backend_jobs']}

def submit(root,output):
    receipt=json.loads((output/'prepared.json').read_text())
    plan=receipt['plan']
    plan_path=root/receipt.get('plan_relative_path','experiments/annual_mitigation_ibm.json')
    if sha(plan_path)!=receipt['plan_sha256']:
        raise ValueError('Hardware plan changed')
    for path,expected in receipt['code_sha256'].items():
        if sha(root/path)!=expected:
            raise ValueError('Prepared hardware acquisition code changed')
    if sha(output/'circuits.qpy')!=receipt['circuits_sha256']:
        raise ValueError('Prepared hardware circuits changed')
    backend=service(plan.get('credential_env','IBM_QUANTUM_API_TOKEN'),
                    plan.get('instance_env','IBM_QUANTUM_INSTANCE')).backend(plan['backend'])
    with (output/'circuits.qpy').open('rb') as stream:
        circuits=qpy.load(stream)
    accepted=[]
    for arm in plan['arms']:
        intent=output/f'{arm}_intent.json'
        if intent.exists():
            raise FileExistsError('Existing hardware intent; collect, never retry')
        enabled=arm=='dd_twirl'
        options=dict(max_execution_time=plan['max_execution_time_per_job_seconds'],
                     dynamical_decoupling=dict(enable=enabled,sequence_type='XpXm',skip_reset_qubits=True),
                     twirling=dict(enable_gates=enabled,enable_measure=enabled,
                                   num_randomizations=plan['randomizations'] if enabled else 1,
                                   shots_per_randomization=plan['shots_per_randomization'] if enabled else plan['kernel_shots']))
        # Client-side Sampler uses one shot count per program; all PUBs intentionally match.
        pubs=[(qc,None,shots) for qc,shots in zip(circuits,receipt['shots_per_pub'],strict=True)]
        sampler=Sampler(mode=backend,options=options)
        write(intent,dict(arm=arm,created_utc=now(),options=options,shots=receipt['shots_per_pub']))
        tick=time.perf_counter()
        job=sampler.run(pubs)
        write(output/f'{arm}_submitted.json',dict(job_id=job.job_id(),accepted_utc=now(),
                                                submission_roundtrip_seconds=time.perf_counter()-tick))
        accepted.append(arm)
    return dict(accepted_arms=accepted,max_total_configured_qpu_seconds=plan['max_total_configured_qpu_seconds'])

def collect(output):
    statuses={}
    receipt=json.loads((output/'prepared.json').read_text())
    plan=receipt['plan']
    svc=service(plan.get('credential_env','IBM_QUANTUM_API_TOKEN'),
                plan.get('instance_env','IBM_QUANTUM_INSTANCE'))
    for arm in ['raw','dd_twirl']:
        submitted=output/f'{arm}_submitted.json'
        if not submitted.exists():
            statuses[arm]='not_submitted'
            continue
        record=json.loads(submitted.read_text())
        job=svc.job(record['job_id'])
        status=str(job.status()).upper()
        statuses[arm]=status
        write(output/f'{arm}_status.json',dict(status=status,observed_utc=now()))
        if status in {'DONE','ERROR','CANCELLED'}:
            write(output/f'{arm}_metrics.json',job.metrics())
            write(output/f'{arm}_usage.json',job.usage())
        if status=='DONE' and not (output/f'{arm}_counts.json').exists():
            results=job.result()
            counts=[item.data.meas.get_counts() for item in results]
            receipt=json.loads((output/'prepared.json').read_text())
            if len(counts)!=len(receipt['shots_per_pub']):
                raise ValueError('Unexpected number of hardware outputs')
            for row,shots in zip(counts,receipt['shots_per_pub'],strict=True):
                if sum(row.values())!=shots:
                    raise ValueError('Hardware shot count differs from fixed PUB budget')
            write(output/f'{arm}_counts.json',dict(counts=counts,collected_utc=now()))
            write(output/f'{arm}_metrics.json',job.metrics())
    return statuses

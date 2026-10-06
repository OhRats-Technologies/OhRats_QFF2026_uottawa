"""Measured overlaps for hardware-selected four-input QSVRs, with frozen budgets."""
import json
from pathlib import Path
import numpy as np
from qiskit import QuantumCircuit, qpy
from qiskit.circuit.library import zz_feature_map
from qiskit.transpiler import generate_preset_pass_manager
from wildfire_lab.mitigation_hardware import service, connected_path, measured_wires, sha, write, now
from wildfire_lab.selector_hardware import submit, collect


def prepare(root, output):
    path = root/'experiments/selector_kernel_hardware.json'
    plan = json.loads(path.read_text())
    source_path = root/'docs/results/selector-hardware.json'
    assert sha(source_path)==plan['selector_result_sha256']
    source = json.loads(source_path.read_text())
    output.mkdir(parents=True,exist_ok=False)
    write(output/'intent.json',dict(plan_sha256=sha(path),created_utc=now()))
    svc = service()
    backend = svc.backend(plan['backend'])
    usage = svc.usage()
    write(output/'account_usage_before.json',usage)
    assert usage['usage_remaining_seconds']>=2*plan['max_execution_time_per_job_seconds']
    feature = zz_feature_map(4,reps=1,entanglement='linear')
    physical = connected_path(backend,4)
    pm = generate_preset_pass_manager(backend=backend,initial_layout=physical,
                                      optimization_level=1,seed_transpiler=137)
    circuits, records, models = [], [], {}
    serial = 0.
    for key in plan['model_keys']:
        record = source['models'][key]
        train = np.pi/32*np.tanh(np.array(record['scaled_train'])/2)
        valid = np.pi/32*np.tanh(np.array(record['scaled_cross'])/2)
        bound = [feature.assign_parameters(row) for row in train]
        cross = [feature.assign_parameters(row) for row in valid]
        tasks = [(i,j,bound[i].compose(bound[j].inverse()),'train')
                 for i in range(len(train)) for j in range(i,len(train))]
        tasks += [(i,j,a.compose(b.inverse()),'cross')
                  for i,a in enumerate(cross) for j,b in enumerate(bound)]
        models[key]=record
        for i,j,qc,kind in tasks:
            qc.measure_all()
            qc = pm.run(qc)
            assert measured_wires(qc)==physical
            circuits.append(qc)
            duration = 0.
            for instruction in qc.data:
                if instruction.operation.name in {'barrier','delay'}:
                    continue
                qubits = tuple(qc.find_bit(q).index for q in instruction.qubits)
                duration += backend.target[instruction.operation.name][qubits].duration or 0.
            serial += duration
            records.append(dict(model_key=key,kind=kind,i=i,j=j,depth=qc.depth(),
                                operations=dict(qc.count_ops())))
    for bit in [0,1]:
        qc = QuantumCircuit(4)
        if bit:
            qc.x(range(4))
        qc.measure_all()
        circuits.append(pm.run(qc))
        records.append(dict(kind='calibration',prepared_bit=bit))
    estimate = 2+serial*plan['kernel_shots']+len(circuits)*backend.default_rep_delay*plan['kernel_shots']
    assert estimate<plan['max_execution_time_per_job_seconds']
    with (output/'circuits.qpy').open('wb') as stream:
        qpy.dump(circuits,stream)
    write(output/'models.json',models)
    receipt = dict(stage='kernel',plan=plan,plan_relative_path=str(path.relative_to(root)),
                   plan_sha256=sha(path),circuits_sha256=sha(output/'circuits.qpy'),
                   models_sha256=sha(output/'models.json'),records=records,shots=plan['kernel_shots'],
                   backend=backend.name,physical_qubits=physical,
                   serial_estimated_qpu_seconds=estimate,monthly_remaining_before=usage['usage_remaining_seconds'],
                   prepared_utc=now(),code_sha256={p:sha(root/p) for p in
                      ['wildfire_lab/selector_kernel_hardware.py','wildfire_lab/selector_hardware.py',
                       'scripts/run_selector_kernel_hardware.py']})
    write(output/'prepared.json',receipt)
    return dict(backend=backend.name,pubs=len(circuits),model_subsets=len(models),
                estimate_seconds=estimate,monthly_remaining_seconds=usage['usage_remaining_seconds'])

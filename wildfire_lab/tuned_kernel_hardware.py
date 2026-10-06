"""Freeze training-tuned four-input kernels before independent IBM acquisition."""
import argparse
import json
from pathlib import Path
import subprocess
import time
import numpy as np
import pandas as pd
from qiskit import QuantumCircuit, qpy
from qiskit.transpiler import generate_preset_pass_manager
from wildfire_lab.nested_search import tune, prepared, evaluate
from wildfire_lab.search_kernels import feature_map, angles
from wildfire_lab.search_acquisition import submit, collect
from wildfire_lab.mitigation_hardware import service, connected_path, measured_wires, sha, write, now


def prepare(root, output, path):
    plan = json.loads(path.read_text())
    for name in [str(path.relative_to(root)), *plan['code_paths']]:
        assert subprocess.check_output(['git', 'show', 'HEAD:'+name], cwd=root) == (root/name).read_bytes()
    source_path = root/plan['search_plan']
    assert sha(source_path) == plan['search_plan_sha256']
    search = json.loads(source_path.read_text())
    for name, expected in search['input_sha256'].items():
        assert sha(root/name) == expected
    parent = root/plan['exploration_output']
    assert sha(parent/'choices.json') == plan['choices_sha256']
    choices = json.loads((parent/'choices.json').read_text())['choices']
    exploration = json.loads((parent/'analysis.json').read_text())
    chosen = next(c for c in choices if c['pool_size'] == 20)
    cohort = next(c for c in exploration['cohorts'] if c['pool_size'] == 20)
    columns = [cohort['features'][index] for index in chosen['selected_indices']]
    search['panels'] = dict(hardware_fixed4=columns, mi4=[])
    table = pd.read_csv(root/search['dataset'])
    assert table.year.tolist() == list(range(1988, 2019))
    first, last, vfirst, vlast = plan['fold']
    train, valid = table[table.year.between(first, last)], table[table.year.between(vfirst, vlast)]
    output.mkdir(parents=True, exist_ok=False)
    write(output/'preparation_intent.json', dict(plan_sha256=sha(path), created_utc=now()))
    models, fits, started = {}, 0, time.perf_counter()
    for panel in search['panels']:
        tuning = tune(train, panel, search)
        data = prepared(train, valid, panel, search)
        models[panel] = dict(tuning=tuning, preprocessing=data['preprocessing'],
            scaled_targets=data['y'].tolist(), actual_ha=data['actual'].tolist(),
            train_years=data['train_years'], validation_years=data['validation_years'],
            rows=[evaluate(data, tuning['chosen'][kind], search) for kind in ['ridge', 'rbf', 'qsvr']])
        fits += tuning['predictor_fits']+3
    write(output/'models.json', models)
    svc = service()
    usage = svc.usage()
    assert usage['usage_remaining_seconds'] >= plan['remaining_reserve_seconds']
    backend = svc.backend(plan['backend'])
    physical = connected_path(backend, 4)
    pm = generate_preset_pass_manager(backend=backend, initial_layout=physical,
                                     optimization_level=1, seed_transpiler=137)
    circuits, records = [], []
    for panel, model in models.items():
        row = model['rows'][2]
        specification = row['specification']['circuit']
        feature = feature_map(4, specification)
        bound = [feature.assign_parameters(values) for values in
                 angles(np.asarray(row['scaled_train']), specification, search['quantum'])]
        validation = [feature.assign_parameters(values) for values in
                      angles(np.asarray(row['scaled_cross']), specification, search['quantum'])]
        tasks = [(i, j, bound[i].compose(bound[j].inverse()), 'train')
                 for i in range(len(bound)) for j in range(i, len(bound))]
        tasks += [(i, j, a.compose(b.inverse()), 'cross')
                  for i, a in enumerate(validation) for j, b in enumerate(bound)]
        for i, j, qc, kind in tasks:
            qc.measure_all()
            qc = pm.run(qc)
            assert measured_wires(qc) == physical
            circuits.append(qc)
            records.append(dict(model=panel, kind=kind, i=i, j=j, depth=qc.depth(),
                                operations=dict(qc.count_ops())))
    for bit in [0, 1]:
        qc = QuantumCircuit(4)
        if bit:
            qc.x(range(4))
        qc.measure_all()
        circuits.append(pm.run(qc))
        records.append(dict(kind='calibration', prepared_bit=bit))
    serial = 0.
    for qc in circuits:
        for item in qc.data:
            if item.operation.name in {'barrier', 'delay'}:
                continue
            qubits = tuple(qc.find_bit(q).index for q in item.qubits)
            serial += backend.target[item.operation.name][qubits].duration or 0.
    estimate = 2+plan['shots']*(serial+len(circuits)*backend.default_rep_delay)
    assert len(circuits) < 1000 and estimate <= plan['cap_seconds']
    jobs = []
    for arm in ['raw', 'dd_twirl']:
        child = output/arm
        child.mkdir()
        with (child/'circuits.qpy').open('wb') as stream:
            qpy.dump(circuits, stream)
        jobs.append(dict(label=arm, arm=arm, shots=plan['shots'], cap_seconds=plan['cap_seconds'],
                         records=records, circuits_sha256=sha(child/'circuits.qpy')))
    write(output/'account_usage_before.json', usage)
    write(output/'prepared.json', dict(plan=plan, plan_path=str(path.relative_to(root)),
        plan_sha256=sha(path), models_sha256=sha(output/'models.json'), jobs=jobs,
        physical_qubits=physical, serial_estimate_seconds=estimate, predictor_fits=fits,
        preparation_seconds=time.perf_counter()-started, search_plan=search,
        code_sha256={name: sha(root/name) for name in plan['code_paths']}))
    return dict(jobs=2, pubs_per_job=len(circuits), shots=plan['shots'],
                predictor_fits=fits, estimate_seconds=estimate,
                monthly_remaining_seconds=usage['usage_remaining_seconds'])


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('stage', choices=['prepare', 'submit', 'collect'])
    parser.add_argument('--plan', type=Path)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    try:
        result = prepare(root, args.output, args.plan.resolve()) if args.stage == 'prepare' else (
            submit(root, args.output) if args.stage == 'submit' else collect(args.output))
        print(json.dumps(result))
    except Exception as error:
        args.output.mkdir(parents=True, exist_ok=True)
        write(args.output/'last_error.json', dict(type=type(error).__name__, detail=str(error)))
        print(json.dumps(dict(status='failed', error_type=type(error).__name__)))
        raise SystemExit(1)

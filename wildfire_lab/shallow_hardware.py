"""Compile the declared basis-start grid before allocating real QPU time."""
from itertools import product
import json
from pathlib import Path
import subprocess
from qiskit import QuantumCircuit, qpy
from qiskit.transpiler import generate_preset_pass_manager
import numpy as np
from wildfire_lab.shallow_selector import circuit, probability
from wildfire_lab.selector_sector import Sector
from wildfire_lab.shallow_study import parent
from wildfire_lab.dicke_selector import circuit as dicke_circuit
from wildfire_lab.mitigation_hardware import service, connected_path, measured_wires, now, sha, write


def compile_family(backend, logical, records, shots):
    n = logical[0].num_qubits
    layout = connected_path(backend, n)
    pm = generate_preset_pass_manager(backend=backend, initial_layout=layout,
                                      optimization_level=1, seed_transpiler=137)
    compiled, metadata = [], []
    for qc, label in zip(logical, records, strict=True):
        qc = qc.copy()
        qc.measure_all()
        physical = pm.run(qc)
        serial = 0.
        for item in physical.data:
            if item.operation.name in {'barrier', 'delay'}:
                continue
            qubits = tuple(physical.find_bit(q).index for q in item.qubits)
            serial += backend.target[item.operation.name][qubits].duration or 0.
        compiled.append(physical)
        metadata.append(dict(label, operations=dict(physical.count_ops()),
                             depth=physical.depth(), measured_wires=measured_wires(physical),
                             serial_duration_seconds=serial))
    # Different final permutations get their own physical readout calibration.
    mappings = list(dict.fromkeys(tuple(record['measured_wires']) for record in metadata))
    for wires in mappings:
        for bit in [0, 1]:
            qc = QuantumCircuit(n)
            if bit:
                qc.x(range(n))
            qc.measure_all()
            physical = generate_preset_pass_manager(backend=backend, initial_layout=list(wires),
                         optimization_level=1, seed_transpiler=137).run(qc)
            compiled.append(physical)
            metadata.append(dict(kind='calibration', prepared_bit=bit, measured_wires=list(wires),
                                 operations=dict(physical.count_ops()), depth=physical.depth(),
                                 serial_duration_seconds=n*.000002))
    estimate = 2+shots*sum(r['serial_duration_seconds']+backend.default_rep_delay for r in metadata)
    return compiled, metadata, estimate


def prepare(root, output):
    path = root/'experiments/shallow_hardware_search.json'
    plan = json.loads(path.read_text())
    for name in [str(path.relative_to(root)), *plan['code_paths']]:
        assert subprocess.check_output(['git', 'show', 'HEAD:'+name], cwd=root) == (root/name).read_bytes()
    source = parent(root, plan)
    local_path = root/plan['local_study']
    assert sha(local_path) == plan['local_evidence_sha256']
    local = json.loads(local_path.read_text())
    svc = service()
    backend = svc.backend(plan['backend'])
    usage = svc.usage()
    assert usage['usage_remaining_seconds'] >= plan['personal_total_reserve_seconds']
    output.mkdir(parents=True, exist_ok=False)
    write(output/'preparation_intent.json', dict(plan_sha256=sha(path), created_utc=now()))
    write(output/'account_usage_before.json', usage)
    jobs, cases = [], []
    for old in source['cohorts']:
        if old['fold'] != plan['fold']:
            continue
        n = len(old['features'])
        own = next(c for c in local['cohorts'] if c['fold'] == old['fold'] and len(c['features']) == n)
        obj = {key: np.asarray(value) if isinstance(value, list) else value
               for key, value in old['objective'].items()}
        sector = Sector(obj)
        initial = own['initial']['random']
        logical, labels = [], []
        for beta0, gamma, beta1 in product(plan['beta0'], plan['normalized_gamma'], plan['beta1']):
            parameters = [beta0, gamma/sector.scale, beta1]
            logical.append(circuit(obj, initial, parameters))
            labels.append(dict(kind='candidate', source='grid', initial=initial,
                               parameters=parameters, normalized_gamma=gamma))
        for name in ['random-p2', 'mi-p2']:
            record = own['runs'][name]
            logical.append(circuit(obj, record['initial_indices'], record['parameters']))
            labels.append(dict(kind='candidate', source=name, initial=record['initial_indices'],
                               parameters=record['parameters']))
        for name in ['random', 'mi']:
            qc = QuantumCircuit(n)
            qc.x(own['initial'][name])
            logical.append(qc)
            labels.append(dict(kind='control', source=name, initial=own['initial'][name], parameters=[]))
        compiled, records, estimate = compile_family(backend, logical, labels, plan['shots'])
        assert estimate <= plan['exploration_job_cap_seconds']
        child = output/f'pool-{n}'
        child.mkdir()
        with (child/'circuits.qpy').open('wb') as stream:
            qpy.dump(compiled, stream)
        # Compilation comparison is not a new Dicke acquisition.
        old_qc = dicke_circuit(obj, old['policies']['optimized2']['parameters'])
        old_qc.measure_all()
        old_compiled = generate_preset_pass_manager(backend=backend, optimization_level=3,
                          seed_transpiler=137).run(old_qc)
        job = dict(label=child.name, arm='raw', cap_seconds=plan['exploration_job_cap_seconds'],
                   shots=plan['shots'], records=records, circuits_sha256=sha(child/'circuits.qpy'),
                   serial_estimate_seconds=estimate)
        jobs.append(job)
        ideal = []
        for label in labels:
            if label['parameters']:
                p = probability(sector, label['initial'], label['parameters'])
            else:
                p = (sector.states == sum(1 << i for i in label['initial'])).astype(float)
            ideal.append(dict(expected_objective=float(p @ sector.cost),
                              optimum_probability=float(p[np.isclose(sector.cost, sector.shift,
                                                                      atol=1e-9, rtol=0)].sum()),
                              support=int((p > 1e-12).sum()), probability=p.tolist()))
        cases.append(dict(pool_size=n, objective=old['objective'], features=old['features'],
                          random_initial=initial, sector_states=sector.states.tolist(),
                          sector_objectives=sector.cost.tolist(), ideal=ideal,
                          dicke_reference=dict(logical_qubits=old_qc.num_qubits,
                                               depth=old_compiled.depth(), operations=dict(old_compiled.count_ops()))))
    assert len(jobs) == 3
    receipt = dict(plan=plan, plan_path=str(path.relative_to(root)), plan_sha256=sha(path),
                   prepared_utc=now(), jobs=jobs, cases=cases,
                   code_sha256={name: sha(root/name) for name in plan['code_paths']})
    write(output/'prepared.json', receipt)
    return dict(jobs=len(jobs), reserve_seconds=sum(j['cap_seconds'] for j in jobs),
                monthly_remaining_seconds=usage['usage_remaining_seconds'],
                pubs=[len(j['records']) for j in jobs],
                serial_estimates_seconds=[j['serial_estimate_seconds'] for j in jobs])


if __name__ == '__main__':
    import argparse
    from wildfire_lab.search_acquisition import submit, collect
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('stage', choices=['prepare', 'submit', 'collect'])
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    try:
        result = collect(args.output) if args.stage == 'collect' else globals()[args.stage](root, args.output)
        print(json.dumps(result))
    except Exception as error:
        # SDK exceptions can embed account or job identifiers. Keep them private.
        args.output.mkdir(parents=True, exist_ok=True)
        write(args.output/'last_error.json', dict(type=type(error).__name__, detail=str(error), stage=args.stage))
        print(json.dumps(dict(status='failed', error_type=type(error).__name__, stage=args.stage)))
        raise SystemExit(1)

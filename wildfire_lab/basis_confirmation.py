"""Independent raw/DD confirmation of parameters frozen from hardware training."""
import argparse
import json
from pathlib import Path
import subprocess
import numpy as np
from qiskit import QuantumCircuit, qpy
from wildfire_lab.shallow_selector import circuit
from wildfire_lab.shallow_hardware import compile_family
from wildfire_lab.search_acquisition import submit, collect
from wildfire_lab.mitigation_hardware import service, sha, write, now


def prepare(root, output, path):
    plan = json.loads(path.read_text())
    for name in [str(path.relative_to(root)), *plan['code_paths']]:
        assert subprocess.check_output(['git', 'show', 'HEAD:'+name], cwd=root) == (root/name).read_bytes()
    parent = root/plan['exploration_output']
    choices_path = parent/'choices.json'
    assert sha(choices_path) == plan['choices_sha256']
    frozen = json.loads(choices_path.read_text())
    assert sha(parent/'analysis.json') == frozen['analysis_sha256']
    source = json.loads((parent/'prepared.json').read_text())
    svc = service(plan['credential_env'], plan['instance_env'])
    backend = svc.backend(plan['backend'])
    usage = svc.usage()
    assert usage['usage_remaining_seconds'] >= plan['remaining_reserve_seconds']
    output.mkdir(parents=True, exist_ok=False)
    write(output/'preparation_intent.json', dict(plan_sha256=sha(path), created_utc=now()))
    write(output/'account_usage_before.json', usage)
    compiled, records, cases, estimate = [], [], [], 2.
    for chosen in frozen['choices']:
        n = chosen['pool_size']
        case = next(c for c in source['cases'] if c['pool_size'] == n)
        obj = {key: np.asarray(value) if isinstance(value, list) else value
               for key, value in case['objective'].items()}
        logical = [circuit(obj, chosen['initial'], chosen['parameters'])]
        labels = [dict(kind='confirmation', source='hardware_chosen', pool_size=n,
                       initial=chosen['initial'], parameters=chosen['parameters'])]
        original = next(j for j in source['jobs'] if j['label'] == f'pool-{n}')
        for label in [r for r in original['records'] if r['kind'] == 'control']:
            qc = QuantumCircuit(n)
            qc.x(label['initial'])
            logical.append(qc)
            labels.append(dict(kind='control', pool_size=n, source=label['source'],
                               initial=label['initial'], parameters=[]))
        native, metadata, duration = compile_family(backend, logical, labels, plan['shots'])
        # This helper's stand-alone two-second overhead is counted once for a
        # combined job; actual runtime charges remain authoritative.
        estimate += duration-2
        compiled.extend(native)
        records.extend(dict(record, pool_size=n) for record in metadata)
        cases.append(dict(pool_size=n, objective=case['objective'], features=case['features'],
                          chosen=chosen))
    assert compiled and estimate <= plan['cap_seconds']
    jobs = []
    for arm in ['raw', 'dd_twirl']:
        child = output/arm
        child.mkdir()
        with (child/'circuits.qpy').open('wb') as stream:
            qpy.dump(compiled, stream)
        jobs.append(dict(label=arm, arm=arm, cap_seconds=plan['cap_seconds'], shots=plan['shots'],
                         records=records, circuits_sha256=sha(child/'circuits.qpy'),
                         serial_estimate_seconds=estimate))
    receipt = dict(plan=plan, plan_path=str(path.relative_to(root)), plan_sha256=sha(path),
                   prepared_utc=now(), jobs=jobs, cases=cases,
                   code_sha256={name: sha(root/name) for name in plan['code_paths']})
    write(output/'prepared.json', receipt)
    return dict(jobs=2, pubs_per_job=len(compiled), serial_estimate_seconds=estimate,
                monthly_remaining_seconds=usage['usage_remaining_seconds'], backend=backend.name)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('stage', choices=['prepare', 'submit', 'collect'])
    parser.add_argument('--plan', type=Path)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    try:
        if args.stage == 'prepare':
            assert args.plan is not None
            result = prepare(root, args.output, args.plan.resolve())
        else:
            result = collect(args.output) if args.stage == 'collect' else submit(root, args.output)
        print(json.dumps(result))
    except Exception as error:
        args.output.mkdir(parents=True, exist_ok=True)
        write(args.output/'last_error.json', dict(type=type(error).__name__, detail=str(error), stage=args.stage))
        print(json.dumps(dict(status='failed', error_type=type(error).__name__, stage=args.stage)))
        raise SystemExit(1)

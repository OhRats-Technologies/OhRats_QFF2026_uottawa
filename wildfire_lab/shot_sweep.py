"""Reuse frozen device-native circuits for a bounded measurement-count comparison."""
import argparse
import json
from pathlib import Path
import shutil
import subprocess
from wildfire_lab.mitigation_hardware import service, sha, write, now
from wildfire_lab.search_acquisition import submit, collect


def prepare(root, output, path):
    plan = json.loads(path.read_text())
    for name in [str(path.relative_to(root)), *plan['code_paths']]:
        assert subprocess.check_output(['git', 'show', 'HEAD:'+name], cwd=root) == (root/name).read_bytes()
    parent = root/plan['parent_namespace']
    assert sha(parent/'prepared.json') == plan['parent_prepared_sha256']
    frozen = json.loads((parent/'prepared.json').read_text())
    assert frozen['plan']['backend'] == plan['backend']
    svc = service(plan['credential_env'], plan['instance_env'])
    usage = svc.usage()
    reserve = sum(plan['caps_seconds'][str(shots)] for shots in plan['shot_order'])*2
    assert reserve == plan['remaining_reserve_seconds']
    assert usage['usage_remaining_seconds'] >= reserve
    svc.backend(plan['backend'])
    sources = {job['arm']: job for job in frozen['jobs']}
    for job in sources.values():
        assert sha(parent/job['label']/'circuits.qpy') == job['circuits_sha256']
    output.mkdir(parents=True, exist_ok=False)
    write(output/'preparation_intent.json', dict(plan_sha256=sha(path), created_utc=now()))
    write(output/'account_usage_before.json', usage)
    jobs = []
    for index, shots in enumerate(plan['shot_order']):
        arms = ['raw', 'dd_twirl'] if index % 2 == 0 else ['dd_twirl', 'raw']
        for arm in arms:
            original = sources[arm]
            label = f'{arm}-{shots}'
            child = output/label
            child.mkdir()
            shutil.copyfile(parent/original['label']/'circuits.qpy', child/'circuits.qpy')
            estimate = 2+(original['serial_estimate_seconds']-2)*shots/frozen['plan']['shots']
            assert estimate <= plan['caps_seconds'][str(shots)]
            jobs.append(dict(label=label, arm=arm, shots=shots, records=original['records'],
                cap_seconds=plan['caps_seconds'][str(shots)],
                circuits_sha256=sha(child/'circuits.qpy'), serial_estimate_seconds=estimate))
    write(output/'prepared.json', dict(plan=plan, plan_path=str(path.relative_to(root)),
        plan_sha256=sha(path), prepared_utc=now(), cases=frozen['cases'], jobs=jobs,
        code_sha256={name: sha(root/name) for name in plan['code_paths']}))
    return dict(backend=plan['backend'], jobs=len(jobs), configured_reserve_seconds=reserve,
                pubs_per_job=len(jobs[0]['records']),
                monthly_remaining_seconds=usage['usage_remaining_seconds'],
                estimated_seconds=[round(job['serial_estimate_seconds'], 2) for job in jobs])


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
        print(json.dumps(dict(status='failed', stage=args.stage, error_type=type(error).__name__)))
        raise SystemExit(1)

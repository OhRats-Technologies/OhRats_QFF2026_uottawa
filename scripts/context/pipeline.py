"""Prepare bounded forest context in ignored replica paths; never run a predictor."""
import argparse
import json
import subprocess
import sys
from pathlib import Path

from manifest import build_manifest

ROOT = Path(__file__).resolve().parents[2]


def commands(cache, output, include_wms, include_change=False):
    boundary = cache / 'ontario-2021.geojson'
    steps = [
        ('bootstrap.py', ['--cache', cache]),
        ('../download_ontario_boundary.py', ['--output', boundary]),
        ('overview.py', ['--cache', cache, '--output', output / 'overviews.json']),
        ('layouts.py', ['--cache', cache, '--acquisition', output / 'overviews.json',
                        '--output', output / 'layouts.json']),
        ('extract.py', ['--cache', cache, '--layouts', output / 'layouts.json',
                        '--boundary', boundary, '--output', output / 'arrays',
                        '--receipt', output / 'height-context.json']),
        ('render_height.py', ['--input', output / 'arrays', '--boundary', boundary,
                              '--output', output / 'maps']),
    ]
    if include_wms:
        steps.append(('wms.py', ['--cache', cache / 'wms', '--boundary', boundary,
                                 '--output', output / 'maps']))
    if include_change:
        steps.append(('change.py', ['--prepared', output, '--boundary', boundary,
                                    '--output', output / 'change', '--map']))
    return [[str(ROOT / 'scripts/context' / name), *map(str, arguments)]
            for name, arguments in steps]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=['plan', 'prepare'])
    parser.add_argument('--cache', type=Path, default=ROOT / '.cache/context/source-replica')
    parser.add_argument('--output', type=Path, default=ROOT / '.cache/context/prepared-replica')
    parser.add_argument('--include-wms', action='store_true', help='Also fetch five dated display images/legends')
    parser.add_argument('--include-change', action='store_true', help='Derive pinned 1985–2015 height differences; no added requests')
    args = parser.parse_args()
    cache, output = args.cache.resolve(), args.output.resolve()
    for path in [cache, output]:
        if not path.is_relative_to(ROOT / '.cache'):
            parser.error('Replica paths must be under this repository’s ignored .cache/')
    steps = commands(cache, output, args.include_wms, args.include_change)
    plan = {'steps': steps, 'soft_cache_limit_bytes': 200_000_000,
            'scope': 'Seven 1985–2015 height overviews; native headers only; fixed Ontario boundary',
            'max_overview_bytes_each': 20_000_000, 'max_native_header_bytes_each': 4_000_000,
            'optional_wms_response_cap_bytes_each': 8_000_000,
            'hardware_jobs': 0, 'predictor_fits': 0,
            'published_receipts_modified': False,
            'budget_enforcement': 'Per-request byte bounds; total cache size checked after each completed stage.',
            'limitation': 'Fresh source bytes may drift; this reacquires context, not final scientific evidence.'}
    if args.action == 'plan':
        print(json.dumps(plan, indent=2))
        return
    output.mkdir(parents=True, exist_ok=True)
    (output / 'pipeline-plan.json').write_text(json.dumps(plan, indent=2) + '\n')
    for step in steps:
        print(f'Context stage: {Path(step[0]).name}', flush=True)
        subprocess.run([sys.executable, *step], cwd=ROOT, check=True)
        downloaded = sum(p.stat().st_size for p in cache.rglob('*') if p.is_file())
        if downloaded > plan['soft_cache_limit_bytes']:
            raise ValueError('Context replica exceeds total cache budget; retained for review')
    receipt = {'status': 'prepared', 'cache_bytes': downloaded,
               'stages_completed': len(steps), 'include_change': args.include_change,
               'predictor_fits': 0, 'hardware_jobs': 0}
    manifest = build_manifest(output)
    (output / 'asset-manifest.json').write_text(json.dumps(manifest, indent=2) + '\n')
    (output / 'pipeline-receipt.json').write_text(json.dumps(receipt, indent=2) + '\n')
    print(json.dumps(receipt, indent=2))


if __name__ == '__main__':
    main()

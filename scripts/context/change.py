"""Describe signed endpoint differences in pinned retrospective height samples."""
import argparse
import csv
import hashlib
import json
import time
from datetime import datetime, timezone
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[2]


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def describe(prepared, plan):
    for name, expected in plan['parent_hashes'].items():
        if digest(ROOT / name) != expected:
            raise ValueError(f'Published parent changed: {name}')
    context = json.loads((ROOT / 'docs/data/scanfi_height_context.json').read_text())
    series = json.loads((ROOT / 'web/demo/assets/context/height-series-v2.json').read_text())
    assert [r['year'] for r in series['records']] == plan['epochs']
    endpoints, hashes = {}, {}
    inside, common = None, None
    for record in series['records']:
        year = record['year']
        path = prepared / 'arrays' / f'{year}.npz'
        hashes[str(year)] = digest(path)
        if hashes[str(year)] != record['source_sha256']:
            raise ValueError(f'Numeric source changed: {path.name}')
        with np.load(path) as saved:
            height = saved['height']
            assert height.dtype == np.uint8 and list(height.shape) == context['shape']
            assert saved['transform'].tolist() == context['transform']
            assert str(saved['crs']) == context['crs']
            if inside is None:
                inside = saved['inside'].copy()
                common = inside.copy()
            assert np.array_equal(inside, saved['inside'])
            common &= height != 255
            if year in plan['endpoints']:
                endpoints[year] = height.copy()
    first, last = [endpoints[y] for y in plan['endpoints']]
    delta = last.astype(np.int16) - first.astype(np.int16)
    values = delta[common]
    count = len(values)
    original = json.loads((ROOT / 'docs/data/height_distribution.json').read_text())
    assert count == original['common_samples']
    histogram = np.bincount(values + 254, minlength=509)
    assert len(histogram) == 509 and histogram.sum() == count
    net = float(values.mean())
    absolute = float(np.abs(values).mean())
    positive = float(np.maximum(values, 0).mean())
    negative = float(np.maximum(-values, 0).mean())
    expected = original['endpoint_mean_change_decomposition_m']['1985_to_2015_mean_change']
    assert abs(net - expected) < 1e-12
    assert abs(net - positive + negative) < 1e-12
    assert abs(absolute - positive - negative) < 1e-12
    assert abs(net - histogram @ np.arange(-254, 255) / count) < 1e-12
    signs = {name: int(mask.sum()) for name, mask in
             [('lower', values < 0), ('same', values == 0), ('higher', values > 0)]}
    assert sum(signs.values()) == count
    assert signs['same'] == histogram[254]
    result = {
        'checked_utc': datetime.now(timezone.utc).isoformat(),
        'plan_sha256': digest(ROOT / 'experiments/height_spatial_change.json'),
        'code_sha256': digest(Path(__file__)), 'source_array_hashes': hashes,
        'endpoints': plan['endpoints'], 'difference': '2015 minus 1985, estimated metres',
        'common_samples': count, 'sample_resolution_m': 480,
        'mean_signed_m': net, 'mean_absolute_m': absolute,
        'root_mean_square_m': float(np.sqrt(np.mean(values.astype(np.float64) ** 2))),
        'min_max_m': [int(values.min()), int(values.max())],
        'p05_p25_p50_p75_p95_m': np.percentile(values, [5, 25, 50, 75, 95]).tolist(),
        'sign_counts': signs, 'sign_fractions': {k: v / count for k, v in signs.items()},
        'absolute_threshold_counts': {str(t): int((np.abs(values) >= t).sum()) for t in [5, 10]},
        'mean_positive_contribution_m': positive, 'mean_negative_contribution_m': negative,
        'cancellation_fraction': 1 - abs(net) / absolute if absolute else 0,
        'arithmetic_identity': 'net = positive contribution - negative contribution; '
                               'mean absolute = positive contribution + negative contribution',
        'verification': 'Pinned parents, seven array hashes/native grids/masks, signed histogram '
                        'and counts, direct means and previously published endpoint mean agree.',
        'budget': plan['budget'], 'limitations': plan['limitations'],
    }
    delta[~common] = plan['map']['numeric_nodata']
    return result, histogram, delta, common, endpoints, context


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--prepared', type=Path, default=ROOT / '.cache/context/prepared-replica')
    parser.add_argument('--output', type=Path, default=ROOT / '.cache/context/height-spatial-v1')
    parser.add_argument('--boundary', type=Path, default=ROOT / '.cache/context/source-replica/ontario-2021.geojson')
    parser.add_argument('--map', action='store_true')
    parser.add_argument('--figure', action='store_true', help='Also requires the analysis dependency group')
    args = parser.parse_args()
    if not args.output.resolve().is_relative_to(ROOT / '.cache'):
        parser.error('Output must be under the repository’s ignored .cache/')
    plan = json.loads((ROOT / 'experiments/height_spatial_change.json').read_text())
    started = time.perf_counter()
    result, histogram, delta, common, endpoints, context = describe(args.prepared, plan)
    result['calculation_seconds'] = time.perf_counter() - started
    args.output.mkdir(parents=True, exist_ok=True)
    numeric = args.output / 'height-change.npz'
    np.savez_compressed(numeric, difference=delta, common=common,
                        transform=context['transform'], crs=context['crs'])
    result['numeric_sha256'] = digest(numeric)
    with (args.output / 'histogram.csv').open('w', newline='') as handle:
        writer = csv.writer(handle)
        writer.writerow(['difference_m', 'common_samples'])
        writer.writerows(zip(range(-254, 255), histogram.tolist()))
    result['histogram_sha256'] = digest(args.output / 'histogram.csv')
    if args.map or args.figure:
        from render_change import render, figure
        result['map'] = render(delta, common, endpoints, context, args.boundary, args.output, plan)
        if args.figure:
            figure(result, histogram, args.output)
            result['figure_sha256'] = digest(args.output / 'height-change-summary.png')
    (args.output / 'summary.json').write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps({k: result[k] for k in ['common_samples', 'mean_signed_m',
                      'mean_absolute_m', 'sign_fractions', 'cancellation_fraction', 'calculation_seconds']}))


if __name__ == '__main__':
    main()

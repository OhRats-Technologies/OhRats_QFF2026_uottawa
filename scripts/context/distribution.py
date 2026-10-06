"""Describe pinned height arrays without reading outcomes, downloading or fitting."""
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
    series = json.loads((ROOT / 'web/demo/assets/context/height-series.json').read_text())
    arrays, hashes = [], {}
    inside = None
    for record in series['records']:
        path = prepared / 'arrays' / f"{record['year']}.npz"
        hashes[str(record['year'])] = digest(path)
        if hashes[str(record['year'])] != record['source_sha256']:
            raise ValueError(f'Numeric source changed: {path.name}')
        with np.load(path) as saved:
            if inside is None:
                inside = saved['inside'].copy()
            assert np.array_equal(inside, saved['inside'])
            assert saved['height'].dtype == np.uint8
            assert list(saved['height'].shape) == context['shape']
            assert saved['transform'].tolist() == context['transform']
            assert str(saved['crs']) == context['crs']
            arrays.append(saved['height'].copy())
    years = [r['year'] for r in series['records']]
    assert years == plan['epochs'] == context['years']
    common = inside & np.logical_and.reduce([a != 255 for a in arrays])
    count = int(common.sum())
    rows, histograms, values = [], [], []
    for year, array, previous in zip(years, arrays, context['rows']):
        v = array[common]
        histogram = np.bincount(v, minlength=255)
        positive = v[v > 0]
        assert histogram.sum() == count == previous['common_samples']
        assert histogram[0] == previous['zero_height_samples']
        weighted_mean = float(histogram @ np.arange(255) / count)
        assert abs(weighted_mean - previous['common_mean_height_m']) < 1e-12
        assert abs(weighted_mean - v.mean()) < 1e-12
        rows.append({
            'year': year, 'common_samples': count,
            'zero_samples': int(histogram[0]), 'zero_fraction': float(histogram[0] / count),
            'mean_height_m': weighted_mean,
            'positive_mean_height_m': float(positive.mean()),
            'all_p10_p50_p90_m': np.percentile(v, [10, 50, 90]).tolist(),
            'positive_p10_p50_p90_m': np.percentile(positive, [10, 50, 90]).tolist(),
            'above_30m_fraction': float(histogram[31:].sum() / count),
            'above_40m_fraction': float(histogram[41:].sum() / count),
        })
        histograms.append(histogram)
        values.append(v)
    transitions = []
    for index in range(1, len(values)):
        delta = values[index].astype(np.int16) - values[index - 1].astype(np.int16)
        unchanged, decreased, increased = [int(f(delta).sum()) for f in
                                           [lambda d: d == 0, lambda d: d < 0, lambda d: d > 0]]
        assert unchanged + decreased + increased == count
        transitions.append({'from': years[index - 1], 'to': years[index],
                            'unchanged_fraction': unchanged / count,
                            'decreased_fraction': decreased / count,
                            'increased_fraction': increased / count,
                            'mean_absolute_change_m': float(np.abs(delta).mean())})
    for row, histogram in zip(rows, histograms):
        row['histogram_total_variation_from_1985'] = float(
            np.abs(histogram - histograms[0]).sum() / (2 * count))
    first, last = rows[0], rows[-1]
    p0, p1 = 1 - first['zero_fraction'], 1 - last['zero_fraction']
    mu0, mu1 = first['positive_mean_height_m'], last['positive_mean_height_m']
    share_term = (p1 - p0) * (mu1 + mu0) / 2
    height_term = (mu1 - mu0) * (p1 + p0) / 2
    change = last['mean_height_m'] - first['mean_height_m']
    assert abs(change - share_term - height_term) < 1e-12
    result = {'checked_utc': datetime.now(timezone.utc).isoformat(),
              'plan_sha256': digest(ROOT / 'experiments/height_distribution.json'),
              'code_sha256': digest(Path(__file__)), 'source_array_hashes': hashes,
              'sample_resolution_m': 480, 'common_samples': count, 'rows': rows,
              'transitions': transitions,
              'endpoint_mean_change_decomposition_m': {
                  '1985_to_2015_mean_change': change,
                  'positive_share_term': share_term, 'positive_height_term': height_term,
                  'identity': 'mean = positive_fraction * conditional_positive_mean; '
                              'delta(mean) = average(mu)*delta(p) + average(p)*delta(mu)'},
              'verification': 'Pinned source/grid hashes, histogram counts, weighted means and '
                              'zeros agree with the original receipt; direct array means and '
                              'transition partitions checked; decomposition residual <1e-12.',
              'label_reads': 0, 'downloads': 0, 'predictor_fits': 0,
              'quantum_states': 0, 'hardware_jobs': 0, 'limitations': plan['limitations']}
    return result, histograms


def figure(result, histograms, path):
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    from matplotlib.ticker import PercentFormatter

    plt.rcParams.update({'font.family': 'DejaVu Sans', 'font.size': 11,
                         'axes.spines.top': False, 'axes.spines.right': False})
    fig, axes = plt.subplots(1, 2, figsize=(12, 4.8), gridspec_kw={'width_ratios': [1.1, 1]})
    fig.suptitle('Ontario height: the denominator matters',
                 x=.06, ha='left', fontsize=17, fontweight='bold')
    colours = ['#165c60', '#b35e3c']
    for index, colour in zip([0, -1], colours):
        row = result['rows'][index]
        axes[0].step(np.arange(41), histograms[index][:41] / result['common_samples'],
                     where='mid', label=str(row['year']), color=colour, linewidth=1.7)
    axes[0].set(xlim=(-.5, 40.5), ylim=(0, .4), xlabel='Recorded height (m)',
                ylabel='Share of common valid samples', title='Endpoint distributions · zeros retained')
    axes[0].yaxis.set_major_formatter(PercentFormatter(1))
    axes[0].legend(frameon=False)
    years = [r['year'] for r in result['rows']]
    for key, colour, label in [('mean_height_m', colours[0], 'All valid pixels'),
                              ('positive_mean_height_m', colours[1], 'Positive-height pixels')]:
        axes[1].plot(years, [r[key] for r in result['rows']], marker='o', color=colour,
                     label=label, markersize=4)
    axes[1].set(ylim=(0, 20), xticks=[1985, 1995, 2005, 2015],
                xlabel='Source epoch', ylabel='Mean height (m)', title='Two different denominators')
    axes[1].legend(frameon=False, loc='upper left')
    for ax in axes:
        ax.grid(axis='y', alpha=.15)
    a, b = result['rows'][0], result['rows'][-1]
    note = (f"Valid zeros: {a['zero_fraction']:.1%} → {b['zero_fraction']:.1%}. "
            f"Mass above 40 m (not drawn): {a['above_40m_fraction']:.3%} / {b['above_40m_fraction']:.3%}.\n"
            '480 m nearest samples · common Ontario footprint · positive height is not a forest label.')
    fig.text(.06, .035, note, fontsize=10, color='#47555a')
    fig.tight_layout(rect=(.04, .12, 1, .92))
    fig.savefig(path, dpi=180, facecolor='white')
    plt.close(fig)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--prepared', type=Path, default=ROOT / '.cache/context/prepared-replica')
    parser.add_argument('--output', type=Path, default=ROOT / '.cache/context/height-distribution-v1')
    parser.add_argument('--figure', action='store_true', help='Requires the analysis dependency group')
    args = parser.parse_args()
    plan = json.loads((ROOT / 'experiments/height_distribution.json').read_text())
    started = time.perf_counter()
    result, histograms = describe(args.prepared, plan)
    result['calculation_seconds'] = time.perf_counter() - started
    args.output.mkdir(parents=True, exist_ok=True)
    with (args.output / 'histogram.csv').open('w', newline='') as handle:
        writer = csv.writer(handle)
        writer.writerow(['height_m', *plan['epochs']])
        writer.writerows([value, *[int(h[value]) for h in histograms]] for value in range(255))
    result['histogram_sha256'] = digest(args.output / 'histogram.csv')
    if args.figure:
        figure(result, histograms, args.output / 'height-distribution.png')
        result['figure_sha256'] = digest(args.output / 'height-distribution.png')
    (args.output / 'summary.json').write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps({'rows': result['rows'],
                      'decomposition_m': result['endpoint_mean_change_decomposition_m'],
                      'calculation_seconds': result['calculation_seconds']}))


if __name__ == '__main__':
    main()

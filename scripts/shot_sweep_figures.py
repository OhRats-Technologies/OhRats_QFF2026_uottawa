"""Compare measured usable yield and sampled subset quality from public bundles."""
import argparse
import json
from pathlib import Path
from zipfile import ZipFile
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parents[1]
parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--device', choices=['quebec', 'marrakesh', 'both'], default='both')
args = parser.parse_args()
devices = ['marrakesh', 'quebec'] if args.device == 'both' else [args.device]
evidence = {}
for device in devices:
    with ZipFile(ROOT/f'docs/data/shot-sweep-{device}-evidence.zip') as archive:
        evidence[device] = json.loads(archive.read('evidence.json'))['analysis']
plt.rcParams.update({'font.family': 'DejaVu Sans', 'font.size': 10,
    'axes.spines.top': False, 'axes.spines.right': False,
    'figure.facecolor': '#fbfcfa', 'savefig.facecolor': '#fbfcfa'})
style = [('raw', 'Raw', '#c5693e'), ('dd_twirl', 'DD + twirling', '#237b7c')]


def rows(device, pool, arm):
    return sorted([r for r in evidence[device]['rows'] if r['arm'] == arm
        and r['specification']['kind'] == 'confirmation'
        and r['specification']['pool_size'] == pool], key=lambda r: r['shots'])


for metric in ['yield', 'quality']:
    fig, axes = plt.subplots(len(devices), 3, figsize=(12, 4.2*len(devices)), squeeze=False, sharey='col')
    fig.subplots_adjust(top=.90 if len(devices) > 1 else .84, bottom=.13 if len(devices) > 1 else .17, hspace=.50, wspace=.28)
    for row_index, device in enumerate(devices):
        for column, pool in enumerate([10, 16, 20]):
            ax = axes[row_index, column]
            for arm, label, color in style:
                records = rows(device, pool, arm)
                x = np.arange(3)
                if metric == 'yield':
                    values = np.asarray([r['feasible_fraction']*100 for r in records])
                    intervals = np.asarray([r['wilson95'] for r in records]).T*100
                    ax.errorbar(x, values, yerr=[values-intervals[0], intervals[1]-values],
                                color=color, fmt='o-', capsize=3, label=label)
                else:
                    values = [r.get('gap_to_exact', np.nan) for r in records]
                    ax.plot(x, values, 'o-', color=color, label=label)
            if metric == 'quality':
                controls = [evidence[device]['uniform_controls'][r['uniform_controls']['physical']]
                            for r in rows(device, pool, 'raw')]
                means = [c['mean_gap'] for c in controls]
                bounds = np.asarray([np.quantile(c['gaps'], [.25, .75]) for c in controls]).T
                ax.plot(np.arange(3), means, 's--', color='#828e8a', label='Uniform feasible · full budget')
                ax.fill_between(np.arange(3), bounds[0], bounds[1], color='#828e8a', alpha=.12)
            ax.set(xticks=np.arange(3), xticklabels=['512', '1,024', '2,048'], xlabel='Shots per circuit', ylim=(0, None))
            ax.set_title(f'{device.capitalize()} · {pool} candidate features', loc='left', fontweight='bold')
            if column == 0:
                ax.set_ylabel('Valid four-feature selections · %' if metric == 'yield' else 'Best objective gap · lower is better')
            if row_index == 0 and column == 2:
                ax.legend(frameon=False, fontsize=8)
    for column, pool in enumerate([10, 16, 20]):
        maxima = [r['wilson95'][1]*100 if metric == 'yield' else r.get('gap_to_exact', 0.)
                  for device in devices for arm, _, _ in style for r in rows(device, pool, arm)]
        if metric == 'quality':
            maxima.extend(np.quantile(evidence[device]['uniform_controls'][r['uniform_controls']['physical']]['gaps'], .75)
                          for device in devices for r in rows(device, pool, 'raw'))
        axes[0, column].set_ylim(0, max(maxima)*1.1 or .01)
    title = 'More shots collect candidates, not cleaner circuits' if metric == 'yield' else 'More shots do not guarantee a better subset'
    fig.suptitle(title, x=.125, y=.98, ha='left', fontsize=17, fontweight='bold')
    note = ('Bars: Wilson 95% shot intervals; not calibration/drift uncertainty. Fractions are not prediction accuracy.'
            if metric == 'yield' else 'Grey band: 25–75% of 100 classical trials. Separate hardware executions; no quantum advantage claim.')
    fig.text(.125, .035, note, fontsize=10)
    name = f'shot-sweep-{args.device}-{metric}.png'
    fig.savefig(ROOT/'docs/figures'/name, dpi=170, bbox_inches='tight')
    plt.close(fig)
    print(name)

"""Figures from published saved evidence; no models, states or acquisition."""
import json
from pathlib import Path
from zipfile import ZipFile
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT/'docs/figures'
OUT.mkdir(exist_ok=True)
plt.rcParams.update({'font.family': 'DejaVu Sans', 'font.size': 11,
    'axes.spines.top': False, 'axes.spines.right': False, 'axes.titleweight': 'bold',
    'savefig.facecolor': '#fbfcfa', 'figure.facecolor': '#fbfcfa'})


def hardware(name):
    with ZipFile(ROOT/f'docs/data/{name}-evidence.zip') as archive:
        return json.loads(archive.read('evidence.json'))['analysis']


def save(fig, name):
    fig.savefig(OUT/name, dpi=180, bbox_inches='tight')
    plt.close(fig)


original = json.loads((ROOT/'docs/results/expanded-tuning.json').read_text())
distinct = json.loads((ROOT/'docs/results/expanded-tuning-distinct.json').read_text())
panels = ['weather4', 'mi4', 'interleaved8']
labels = ['Weather · 4', 'MI selected · 4', 'Weather + forest · 8']
fig, ax = plt.subplots(figsize=(10, 5.5))
fig.subplots_adjust(bottom=.27)
for offset, source, label, color in [(-.27, original, 'First grid · includes symmetry duplicates', '#719c9b'),
                                  (0, distinct, 'Distinct grid + C=100', '#cf7044')]:
    values = [next(r['mae_ha'] for r in source['aggregates']
                   if r['panel'] == panel and r['model'] == 'qsvr') for panel in panels]
    bars = ax.bar(np.arange(3)+offset, values, .25, color=color, label=label)
    ax.bar_label(bars, fmt='%.1f', padding=3)
fixed = [next(r['mae_ha'] for r in distinct['aggregates']
              if r['panel'] == panel and r['model'] == 'fixed_qsvr') for panel in panels]
bars = ax.bar(np.arange(3)+.27, fixed, .25, color='#183f48', label='Fixed QSVR reference')
ax.bar_label(bars, fmt='%.1f', padding=3)
ax.axhline(92., color='#707a7b', ls='--', lw=1, label='Training mean')
ax.set(xticks=np.arange(3), xticklabels=labels, ylabel='Mean development MAE · ha/fire', ylim=(0, 210))
ax.set_title('More search did not reliably improve prediction', loc='left', pad=18)
ax.legend(loc='upper left', bbox_to_anchor=(0, -.15), frameon=False, ncol=2, fontsize=9)
fig.text(.125, .015, 'Three reused chronological folds · retrospective annual Ontario · lower is better', fontsize=10)
save(fig, 'research-tuning.png')

fig, axes = plt.subplots(1, 2, figsize=(12, 5.5), sharey=True)
fig.subplots_adjust(top=.78, bottom=.20)
for ax, device in zip(axes, ['marrakesh', 'quebec']):
    result = hardware('basis-confirmation-'+device)
    for offset, arm, label, color in [(-.18, 'raw', 'Raw', '#cf7044'),
                                    (.18, 'dd_twirl', 'DD + twirling', '#227b7c')]:
        values = [next(r['feasible_shots']/r['shots']*100 for r in result['rows']
                       if r['arm'] == arm and r['specification']['pool_size'] == n
                       and r['specification']['kind'] == 'confirmation') for n in [10, 16, 20]]
        bars = ax.bar(np.arange(3)+offset, values, .32, color=color, label=label)
        ax.bar_label(bars, fmt='%.1f%%', padding=4)
    controls = [np.mean([r['feasible_shots']/r['shots']*100 for r in result['rows']
                        if r['specification']['pool_size'] == n and r['specification']['kind'] == 'control'])
                for n in [10, 16, 20]]
    ax.plot(np.arange(3), controls, 'o--', color='#9caaa7', lw=1.5, label='Unentangled controls · mean')
    ax.set(xticks=np.arange(3), xticklabels=['10', '16', '20'], ylim=(0, 105), xlabel='Candidate features / selector qubits')
    ax.set_title('IBM '+device.capitalize(), loc='left', pad=15)
    ax.legend(frameon=False, fontsize=9, loc='upper right')
axes[0].set_ylabel('Valid four-feature subsets · % of 512 shots')
fig.suptitle('Frozen circuits still lose feasible yield on hardware', x=.125, y=.98, ha='left', fontweight='bold', fontsize=15)
fig.text(.125, .025, 'One raw/combined pair per device · layout/calibration/account differ · not a device ranking', fontsize=10)
save(fig, 'research-hardware.png')
print('Saved two figures from immutable published evidence')

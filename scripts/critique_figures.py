"""Descriptive sensitivity and repair figures from frozen saved results."""
import json
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parents[1]
result = json.loads((ROOT/'docs/results/critique-diagnostics.json').read_text())
plt.rcParams.update({'font.family': 'DejaVu Sans', 'font.size': 11,
    'axes.spines.top': False, 'axes.spines.right': False,
    'figure.facecolor': '#fbfcfa', 'savefig.facecolor': '#fbfcfa'})
colors = ['#237b7c', '#c5693e']
fig, axes = plt.subplots(1, 3, figsize=(12, 4.1), sharex=True)
fig.subplots_adjust(top=.75, bottom=.27, wspace=.33)
for ax, panel, title in zip(axes, ['weather4', 'mi4', 'interleaved8'], ['Weather · 4 inputs', 'MI selection · 4 inputs', 'Weather/forest · 8 inputs']):
    for y, (study, color) in enumerate(zip(['expanded-tuning', 'expanded-tuning-distinct'], colors)):
        record = next(r for r in result['prediction_sensitivity'][study] if r['panel'] == panel)
        metrics = record['paired_q_minus_rbf']
        low, high = metrics['omitted_fold_range']
        ax.plot([low, high], [y, y], color=color, lw=5, alpha=.45)
        ax.scatter([metrics['mean_ha']], [y], color=color, s=55, zorder=3)
        ax.annotate(f"{metrics['mean_ha']:+.2f}", (metrics['mean_ha'], y),
                    xytext=(0, 12), textcoords='offset points', ha='center', fontsize=10)
    ax.axvline(0, color='#9ba6a0', lw=1)
    ax.set(title=title, yticks=[0, 1], yticklabels=['Initial grid', 'Distinct / wider C'], ylim=(-.5, 1.6))
    if ax is not axes[0]:
        ax.set_yticklabels([])
    ax.set_xlabel('QSVR − RBF MAE · ha/fire')
fig.suptitle('The ranking depends on which years we count.', x=.06, y=.97, ha='left', fontsize=18, fontweight='bold')
fig.text(.06, .065, 'Dots: all 12 development years. Lines: deleting each four-year fold, without retraining.\nSensitivity ranges, not confidence intervals. Negative favours QSVR; positive favours RBF.', fontsize=10)
fig.savefig(ROOT/'docs/figures/critique-stability.png', dpi=170, bbox_inches='tight')
plt.close(fig)

rows = [r for r in result['kernel_repairs'] if r['repair'] == 'rank4']
fig, axes = plt.subplots(1, 2, figsize=(12, 4.5))
fig.subplots_adjust(top=.78, bottom=.28, wspace=.28)
x = np.arange(len(rows))
for key, label, color, marker in [('raw_mae', 'Measured, unrepaired', '#c5693e', 'o'),
                                 ('repaired_mae', 'Measured + rank 4', '#237b7c', 's'),
                                 ('ideal_mae', 'Ideal QSVR reference', '#828e8a', '^')]:
    axes[0].scatter(x, [r[key] for r in rows], label=label, color=color, marker=marker, s=45)
axes[0].set(yscale='log', ylabel='Four-year MAE · ha/fire · log scale',
    xticks=x, xticklabels=['Subset\nraw', 'Subset\nDD/twirl', 'MI4\nraw', 'MI4\nDD/twirl'])
axes[0].legend(frameon=False, fontsize=9, loc='upper left')
axes[1].bar(x, [100*r['relative_gram_change'] for r in rows], color='#237b7c', width=.6)
axes[1].set(ylabel='Rank-4 Gram change · relative Frobenius %', ylim=(0, 12),
    xticks=x, xticklabels=['Subset\nraw', 'Subset\nDD/twirl', 'MI4\nraw', 'MI4\nDD/twirl'])
for i, row in enumerate(rows):
    axes[1].text(i, 100*row['relative_gram_change']+.4, f"{100*row['relative_gram_change']:.2f}%", ha='center', fontsize=10)
fig.suptitle('A small matrix change can accompany a large prediction change.', x=.06, y=.97, ha='left', fontsize=17, fontweight='bold')
fig.text(.06, .065, 'Fixed 2007–2010 diagnostic, not a selected model or advantage claim. Rank is constrained to four.\nRetained positive-spectrum squared norm: 99.34–99.88%. Hardware-derived dominant geometry remains.', fontsize=10)
fig.savefig(ROOT/'docs/figures/critique-repair.png', dpi=170, bbox_inches='tight')
plt.close(fig)
print('Wrote two saved-evidence figures; no fitting, sampling or hardware.')

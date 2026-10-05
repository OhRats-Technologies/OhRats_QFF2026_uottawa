"""Scientific figures from saved annual receipts; no fitting or test access."""

import json

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

TEAL, ORANGE, INK = '#176468', '#bf733d', '#213843'


def style():
    plt.rcParams.update({'font.family': 'DejaVu Sans', 'font.size': 11,
                         'axes.spines.top': False, 'axes.spines.right': False,
                         'axes.labelcolor': INK, 'text.color': INK,
                         'xtick.color': INK, 'ytick.color': INK,
                         'axes.edgecolor': '#bdc9cc', 'figure.facecolor': '#fafcfb',
                         'axes.facecolor': '#fafcfb', 'svg.fonttype': 'none'})


def save(figure, output, name):
    figure.savefig(output / f'{name}.png', dpi=190, bbox_inches='tight')
    figure.savefig(output / f'{name}.svg', bbox_inches='tight')
    plt.close(figure)


def observed(table, matched, output):
    figure, axes = plt.subplots(2, 1, figsize=(11, 7), height_ratios=[2, 1])
    axes[0].plot(table.year, table.mean_reported_size_ha, color=INK, marker='o', ms=3,
                 lw=1.5, label='Observed annual mean')
    for model, label, color in [('matched_rbf_svr', 'RBF-SVR · four inputs', TEAL),
                                ('matched_fidelity_svr', 'QSVR · four qubits', ORANGE)]:
        rows = sorted([r for r in matched if r['model'] == model and len(r['features']) == 4],
                      key=lambda r: r['years'][0])
        years = sum([r['years'] for r in rows], [])
        predictions = sum([r['predicted_ha'] for r in rows], [])
        axes[0].plot(years, predictions, color=color, marker='.', lw=1.7, label=label)
    axes[0].axvline(2006.5, color='#8e9fa4', lw=1, ls='--')
    axes[0].set_ylabel('Reported hectares / fire')
    axes[0].set_title('Ontario annual mean fire size', loc='left', fontsize=19, weight='bold')
    axes[0].legend(frameon=False, loc='upper left', fontsize=10)
    axes[0].grid(axis='y', alpha=.15)
    axes[1].bar(table.year, table.size_observed_incidents, color=TEAL, alpha=.6)
    axes[1].set_ylabel('Size-observed fires')
    axes[1].set_xlabel('Year · chronological development predictions: 2007–2018')
    for axis in axes:
        axis.set_xlim(1987.3, 2018.7)
    figure.tight_layout()
    save(figure, output, 'annual-development')


def matched_errors(matched, output, baseline):
    figure, axis = plt.subplots(figsize=(10, 5))
    labels = ['RBF · 4 inputs', 'QSVR · 4 qubits', 'RBF · 10 inputs', 'QSVR · 10 qubits']
    groups = [(model, width) for width in [4, 10]
              for model in ['matched_rbf_svr', 'matched_fidelity_svr']]
    for index, (model, width) in enumerate(groups):
        values = [r['mae_ha'] for r in matched if r['model'] == model and len(r['features']) == width]
        color = TEAL if model == 'matched_rbf_svr' else ORANGE
        axis.barh(index, np.mean(values), height=.55, color=color, alpha=.75)
        axis.scatter(values, np.array([index] * len(values)) + np.linspace(-.13, .13, len(values)),
                     color=INK, s=27, zorder=3)
        axis.text(np.mean(values) + 2, index, f'{np.mean(values):.2f}', va='center', fontsize=11)
    axis.axvline(baseline, color='#8e9fa4', ls='--', lw=1)
    axis.set_yticks(range(4), labels)
    axis.invert_yaxis()
    axis.set_xlabel('Mean absolute error · hectares per reported fire')
    axis.set_title('Equal-budget kernel comparison', loc='left', fontsize=19, weight='bold')
    axis.set_xlim(0, 157)
    axis.grid(axis='x', alpha=.12)
    figure.text(.13, .01, 'Bars: mean of three folds. Dots: individual chronological folds. Dashed: training-mean control.',
                fontsize=10, color='#526a72')
    figure.tight_layout(rect=(0, .05, 1, 1))
    save(figure, output, 'annual-matched')


def kernels(diagnostics, output):
    figure, axes = plt.subplots(1, 2, figsize=(11, 4.5))
    frame = pd.DataFrame(diagnostics)
    for width, color in [(4, TEAL), (10, ORANGE)]:
        selected = frame[frame.qubits == width]
        for axis, field in [(axes[0], 'cross_mean'), (axes[1], 'off_diagonal_mean')]:
            for index, ((reps, amplitude), rows) in enumerate(selected.groupby(['reps', 'amplitude'])):
                x = index + (-.1 if width == 4 else .1)
                axis.scatter(np.repeat(x, len(rows)), rows[field], color=color, s=35, alpha=.7)
                axis.plot([x - .07, x + .07], [rows[field].mean()] * 2, color=color, lw=2)
        axes[0].scatter([], [], color=color, label=f'{width} qubits')
    labels = ['1 / π/4', '1 / π/2', '2 / π/4', '2 / π/2']
    for axis in axes:
        axis.set_xticks(range(4), labels)
        axis.set_xlabel('Circuit repetitions / angle amplitude')
        axis.set_yscale('log')
        axis.grid(axis='y', alpha=.15)
    axes[0].set_ylabel('Mean state fidelity')
    axes[0].set_title('Validation → training similarity', loc='left', fontsize=13, weight='bold')
    axes[1].set_title('Off-diagonal training similarity', loc='left', fontsize=13, weight='bold')
    axes[0].legend(frameon=False)
    figure.suptitle('Ten-qubit similarities concentrate near zero', x=.07, ha='left', fontsize=18, weight='bold')
    figure.tight_layout()
    save(figure, output, 'annual-kernel-similarity')


def generate(root, output):
    if output.exists():
        raise FileExistsError(output)
    output.mkdir(parents=True)
    style()
    table = pd.read_csv(root / 'docs/data/annual_training.csv')
    matched = json.loads((root / 'docs/results/annual-matched.json').read_text())['results']
    diagnostics = json.loads((root / 'docs/results/annual-evidence-audit.json').read_text())['kernel_diagnostics']
    classical = json.loads((root / 'docs/results/annual-classical.json').read_text())['results']
    baseline = np.mean([r['mae_ha'] for r in classical if r['model'] == 'training_mean'])
    observed(table, matched, output)
    matched_errors(matched, output, baseline)
    kernels(diagnostics, output)
    return dict(figures=3, files=6, fitting=False, quantum_states=0, annual_test_accessed=False)

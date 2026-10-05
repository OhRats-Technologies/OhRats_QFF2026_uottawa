"""Plot saved primary/reference probability reliability and bin occupancy."""
import argparse
import hashlib
import json
import sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


def plot(source, output):
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    import numpy as np
    saved = json.loads(source.read_text())
    assert saved['status'] == 'audited_saved_probability_reporting'
    fig, (curve, counts) = plt.subplots(1, 2, figsize=(9.2, 4), constrained_layout=True)
    styles = [('geography_season', 'Geography / season', '#587a96'),
              ('geography_cover', '+ forest / water', '#157a67')]
    for index, (group, label, color) in enumerate(styles):
        row = next(r for r in saved['rows'] if r['group'] == group and r['predictor'] == 'tree')
        bins = row['pooled']['bins']; occupied = [b for b in bins if b['count']]
        curve.plot([b['mean_probability'] for b in occupied], [b['positive_fraction'] for b in occupied],
            'o-', color=color, label=label, markersize=4, linewidth=1.5)
        centers = np.array([(b['left']+b['right'])/2 for b in bins])
        counts.bar(centers+(index-.5)*.035, [b['count'] for b in bins],
            width=.033, color=color, alpha=.8, label=label)
    curve.plot([0, 1], [0, 1], '--', color='#999999', linewidth=.8)
    curve.set(xlim=(0, 1), ylim=(-.015, 1.025), xlabel='Mean predicted probability',
        ylabel='Observed positive fraction', title='Reliability of saved probabilities')
    counts.set(xlim=(0, 1), yscale='log', xlabel='Predicted probability bin',
        ylabel='Fires (log scale)', title='Bin occupancy')
    curve.legend(frameon=False, fontsize=9, loc='upper left')
    for ax in (curve, counts):
        ax.spines[['top', 'right']].set_visible(False)
        ax.grid(axis='y', alpha=.15); ax.set_axisbelow(True)
    fig.suptitle('Recorded-size classification · 3,820 fires · 2019–2024', fontsize=11)
    output.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output, dpi=180); plt.close(fig)
    sha = lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
    relative = lambda p:str(p.relative_to(ROOT)) if p.is_relative_to(ROOT) else p.name
    receipt = dict(source=relative(source), source_sha256=sha(source),
        plot_recipe_sha256=sha(Path(__file__)), figure_sha256=sha(output),
        model_fits=0, probability_bins=10,
        interpretation='Descriptive pooled fixed-bin curves with counts, not independent confidence intervals or operational calibration.')
    output.with_suffix('.json').write_text(json.dumps(receipt, indent=2)+'\n')
    print(json.dumps(dict(figure=relative(output), figure_sha256=receipt['figure_sha256'])))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', type=Path, default=ROOT / 'docs/data/probability_report.json')
    parser.add_argument('--output', type=Path, default=ROOT / 'docs/figures/probability-report.png')
    args = parser.parse_args(); plot(args.source, args.output)

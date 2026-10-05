"""Plot local classical approximation versus inherited analytic shot noise."""
import argparse
import hashlib
import json
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.ticker import PercentFormatter
import numpy as np


def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()


def plot(source,output):
    evidence=json.loads(source.read_text());assert evidence['status']=='audited_local_kernel_geometry'
    scales=sorted({r['angle_scale'] for r in evidence['conditions']});rows=evidence['conditions']
    fig,axes=plt.subplots(1,2,figsize=(10.5,4),layout='constrained')
    values=np.array([[r['normalized_cross_shape_relative_error'] for r in rows if r['angle_scale']==a] for a in scales])
    axes[0].plot(scales,values.mean(axis=1),'o-',color='#315d86')
    axes[0].fill_between(scales,values.min(axis=1),values.max(axis=1),color='#315d86',alpha=.12)
    axes[0].set(title='Narrow angles approach a classical tangent kernel',ylabel='Normalized cross-matrix shape error')
    for shots,color in [(512,'#b48252'),(4096,'#24664e')]:
        values=np.array([[next(s for s in r['inherited_cross_shot_rms'] if s['shots']==shots)['rms'] for r in rows if r['angle_scale']==a] for a in scales])
        axes[1].plot(scales,values.mean(axis=1),'o-',color=color,label=f'{shots:,} shots / pair')
        axes[1].fill_between(scales,values.min(axis=1),values.max(axis=1),color=color,alpha=.12)
    axes[1].set(title='But relative measurement noise increases',ylabel='Cross-matrix RMS relative shot error')
    axes[1].legend(frameon=False,fontsize=9)
    for ax in axes:
        ax.set(xscale='log',yscale='log',xlabel='Angle scale α')
        ax.set_xticks(scales,[str(a) for a in scales]);ax.yaxis.set_major_formatter(PercentFormatter(1))
        ax.grid(axis='y',alpha=.12);ax.spines[['top','right']].set_visible(False)
    output.parent.mkdir(parents=True,exist_ok=True);fig.savefig(output,dpi=180,bbox_inches='tight');plt.close(fig)
    output.with_suffix('.json').write_text(json.dumps(dict(source_sha256=sha(source),plot_recipe_sha256=sha(Path(__file__)),
        figure_sha256=sha(output),caption='Three inherited 256/256 training-period sampling conditions; lines are means and bands are ranges, not confidence intervals. Left compares each kernel after its own exact training-variance normalization; right uses independent-shot RMS errors relative to the exact centered matrix. These are different matrix diagnostics, not predictive error. No new shots, model fits or hardware calls. The inherited .05 scale is not reselected.'),indent=2)+'\n')


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--summary',type=Path,default=Path('docs/results/local-geometry.json'))
    parser.add_argument('--output',type=Path,default=Path('docs/figures/local-geometry.png'))
    args=parser.parse_args();plot(args.summary,args.output)

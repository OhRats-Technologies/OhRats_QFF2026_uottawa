"""Plot ideal shot-error sensitivity; ranges show sample conditions, not CIs."""
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
    evidence=json.loads(source.read_text());assert evidence['status']=='audited_analytic_shot_feasibility'
    scales=evidence['plan']['angle_scales'];fig,axes=plt.subplots(1,2,figsize=(11,4),layout='constrained')
    for shots,color in [(512,'#b48252'),(4096,'#24664e')]:
        values=np.array([[next(s for s in r['shot_conditions'] if s['shots']==shots)['expected_relative_frobenius_error']['cross']
            for r in evidence['conditions'] if r['angle_scale']==a] for a in scales])
        axes[0].plot(scales,values.mean(axis=1),'o-',color=color,label=f'{shots:,} shots / pair')
        axes[0].fill_between(scales,values.min(axis=1),values.max(axis=1),color=color,alpha=.1)
    axes[0].set(title='Narrow angles amplify relative shot noise',xlabel='Angle scale α',ylabel='Cross-matrix RMS relative error')
    axes[0].yaxis.set_major_formatter(PercentFormatter(1));axes[0].legend(frameon=False,fontsize=9)
    values=np.array([[r['shots_for_relative_error'][0]['minimum_shots']['cross']
        for r in evidence['conditions'] if r['angle_scale']==a] for a in scales])
    axes[1].plot(scales,values.mean(axis=1),'o-',color='#765b8e')
    axes[1].fill_between(scales,values.min(axis=1),values.max(axis=1),color='#765b8e',alpha=.1)
    axes[1].set(title='Dense-matrix budget for 10% RMS error',xlabel='Angle scale α',ylabel='Required shots per pair (analytic)')
    axes[1].set_yscale('log')
    for ax in axes:
        ax.set_xscale('log');ax.set_xticks(scales,[str(a) for a in scales]);ax.grid(axis='y',alpha=.12);ax.set_axisbelow(True)
        ax.axvline(.05,color='#77858e',linestyle=':',lw=.8);ax.spines[['top','right']].set_visible(False)
    output.parent.mkdir(parents=True,exist_ok=True);fig.savefig(output,dpi=180,bbox_inches='tight');plt.close(fig)
    output.with_suffix('.json').write_text(json.dumps(dict(source_sha256=sha(source),plot_recipe_sha256=sha(Path(__file__)),
        figure_sha256=sha(output),caption='Labels-free exact ZZ matrices; 256 training/256 validation fires per fixed sampling cohort. Lines average three conditions; bands span them, not confidence intervals. Dotted line marks the inherited .05 scale, not a newly selected optimum. Independent Bernoulli pair estimates, noisy training means and fixed exact normalization; no PSD repair or device noise. Dense matrix error is not predictive error or a landmark accuracy guarantee.'),indent=2)+'\n')


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--summary',type=Path,default=Path('docs/results/shot-feasibility.json'))
    parser.add_argument('--output',type=Path,default=Path('docs/figures/shot-feasibility.png'))
    args=parser.parse_args();plot(args.summary,args.output)

"""Plot matched ridge kernels and the fixed 16-landmark approximation."""
import argparse
import hashlib
import json
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt


def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()


def plot(summary_path,output):
    evidence=json.loads(summary_path.read_text());assert evidence['status']=='audited_training_only_ridge'
    fig,axes=plt.subplots(1,2,figsize=(9.5,4),layout='constrained',sharey=True)
    names=['linear','product','rbf','ZZ'];colors=['#77858e','#77858e','#77858e','#24664e']
    for ax,group,title in zip(axes,['diagnostic','sampling_check'],['Diagnostic samples','Fresh sampling checks']):
        samples=[{r['predictor']:r['metric']['average_precision'] for r in s['rows']}
                 for s in evidence['seeds'] if s['group']==group]
        for i,(name,color) in enumerate(zip(names,colors)):
            values=np.array([s[f'{name}/dense'] for s in samples]);mean=values.mean()
            ax.errorbar(i,mean,yerr=[[mean-values.min()],[values.max()-mean]],fmt='o',
                color=color,capsize=4,lw=1.4,markersize=7,label='Dense · seed range' if i==0 else None)
            if name in ['rbf','ZZ']:
                approximate=np.mean([s[f'{name}/ideal/16'] for s in samples])
                ax.plot(i+.13,approximate,marker='D',markerfacecolor='white',markeredgecolor=color,
                    markersize=6,ls='none',label='16 landmarks · mean' if name=='rbf' else None)
        ax.set(title=title,xticks=range(4),xticklabels=['Linear','Product','RBF','ZZ'],xlim=(-.5,3.5))
        ax.spines[['top','right']].set_visible(False);ax.grid(axis='y',alpha=.12);ax.set_axisbelow(True)
        ax.legend(frameon=False,fontsize=9,loc='upper left')
    axes[0].set_ylabel('Average precision');axes[0].set_ylim(.24,.64)
    output.parent.mkdir(parents=True,exist_ok=True);fig.savefig(output,dpi=180,bbox_inches='tight');plt.close(fig)
    output.with_suffix('.json').write_text(json.dumps(dict(summary_sha256=sha(summary_path),
        plot_recipe_sha256=sha(Path(__file__)),figure_sha256=sha(output),
        caption='Fixed ridge=1; 256/256 train/validation fires per seed, common inputs and training-only normalization. Dense dots are means and bars are three-seed ranges, not confidence intervals. Open diamonds mark fixed 16-landmark mean AP. Fresh seeds reuse chronological years and have different prevalence; do not interpret between-panel AP as improvement over time. Exact local simulation, no new shots or hardware.'),indent=2)+'\n')


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--summary',type=Path,default=Path('docs/results/kernel-ridge.json'))
    parser.add_argument('--output',type=Path,default=Path('docs/figures/kernel-ridge.png'))
    args=parser.parse_args();plot(args.summary,args.output)

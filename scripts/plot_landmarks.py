"""Plot audited landmark approximation and shot sensitivity; no model fitting."""
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
    evidence=json.loads(summary_path.read_text())
    assert evidence['status']=='audited_training_only_followup'
    rows=[{r['predictor']:r['metric']['average_precision'] for r in s['rows']} for s in evidence['seeds']]
    counts=evidence['plan']['landmark_counts'];colors={'rbf':'#77858e','ZZ':'#24664e'}
    fig,axes=plt.subplots(1,2,figsize=(11,4.4),layout='constrained')
    for name in ['rbf','ZZ']:
        values=np.array([[s[f'{name}/ideal/{m}'] for m in counts] for s in rows])
        mean=values.mean(axis=0)
        axes[0].errorbar(counts,mean,yerr=np.vstack([mean-values.min(axis=0),values.max(axis=0)-mean]),
            fmt='o-',color=colors[name],capsize=3,lw=1.5,label=f'{name.upper()} landmarks')
        axes[0].axhline(np.mean([s[f'{name}/dense'] for s in rows]),color=colors[name],ls='--',lw=1,
            label=f'{name.upper()} dense')
    axes[0].set_xscale('log',base=2)
    axes[0].set(title='Ideal landmarks · mean and seed range',xlabel='Common training landmarks',
        ylabel='Average precision',xticks=counts,xticklabels=counts)
    axes[0].legend(frameon=False,fontsize=9)
    choices=[('ZZ/dense','Dense exact','#24664e','--'),('ZZ/ideal/16','16 landmarks · ideal','#77858e',':'),
        ('ZZ/512/16','16 landmarks · 512 shots','#b48252','-'),
        ('ZZ/4096/16','16 landmarks · 4096 shots','#765b8e','-')]
    for name,label,color,style in choices:
        axes[1].plot(range(len(rows)),[s[name] for s in rows],marker='o',ls=style,color=color,
            markersize=4,lw=1.5,label=label)
    axes[1].set(title='ZZ shot sensitivity · paired samples',xlabel='Sampling seed',ylabel='Average precision',
        xticks=range(len(rows)),xticklabels=[s['seed'] for s in evidence['seeds']])
    axes[1].legend(frameon=False,fontsize=9)
    for ax in axes:
        ax.spines[['top','right']].set_visible(False);ax.grid(alpha=.12);ax.set_axisbelow(True)
    output.parent.mkdir(parents=True,exist_ok=True);fig.savefig(output,dpi=180,bbox_inches='tight');plt.close(fig)
    meta=dict(summary_sha256=sha(summary_path),plot_recipe_sha256=sha(Path(__file__)),figure_sha256=sha(output),
        caption='Training-only, post-final exploratory screen: 256 train / 256 validation fires, common inputs and landmarks. Bars show the range across three sampling seeds, not confidence intervals. 16 landmarks use 8,056 pair circuits per shot condition (12.19x fewer than dense). All sampling is local; no IBM jobs.')
    output.with_suffix('.json').write_text(json.dumps(meta,indent=2)+'\n')


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--summary',type=Path,default=Path('docs/results/quantum-landmarks.json'))
    parser.add_argument('--output',type=Path,default=Path('docs/figures/quantum-landmarks.png'))
    args=parser.parse_args();plot(args.summary,args.output)

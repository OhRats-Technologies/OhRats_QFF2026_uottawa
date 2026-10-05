"""Plot recorded-coordinate recurrence and ordinary validation geometry."""
import argparse
import hashlib
import json
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.ticker import PercentFormatter


def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()


def plot(source,output):
    evidence=json.loads(source.read_text());assert evidence['status']=='audited_training_coordinate_geometry'
    geometry=evidence['geometry'];conditions=geometry['chronological_conditions']
    fig,axes=plt.subplots(1,2,figsize=(11,4),layout='constrained')
    colors=['#24664e','#b48252','#765b8e']
    for row,color in zip(conditions,colors):
        radii=[float(k) for k in row['fraction_with_training_point_within_km']]
        fractions=list(row['fraction_with_training_point_within_km'].values())
        start,end=row['fold'][2:]
        axes[0].plot(radii,fractions,'o-',lw=1.5,markersize=4,color=color,label=f'{start}-{end}')
    axes[0].set_xscale('log');axes[0].set_xticks([.1,1,5,10,50],['0.1','1','5','10','50'])
    axes[0].set(title='Chronological validation stays nearby',xlabel='Radius to nearest training fire (km)',
                ylabel='Validation records within radius',ylim=(0,1.04))
    axes[0].legend(frameon=False,title='Validation years',fontsize=9,title_fontsize=9,loc='lower right')
    years=[int(k) for k in geometry['years']]
    fractions=[row['repeated_coordinate_row_fraction'] for row in geometry['years'].values()]
    axes[1].bar(years,fractions,color='#77858e',width=.8)
    axes[1].set(title='Exact coordinate recurrence within each year',xlabel='Recorded year',
                ylabel='Records at coordinates used at least twice',xlim=(1987,2019))
    axes[1].set_xticks([1988,1993,1998,2003,2008,2013,2018])
    for ax in axes:
        ax.yaxis.set_major_formatter(PercentFormatter(1));ax.set_axisbelow(True);ax.grid(axis='y',alpha=.12)
        ax.spines[['top','right']].set_visible(False)
    output.parent.mkdir(parents=True,exist_ok=True);fig.savefig(output,dpi=180,bbox_inches='tight');plt.close(fig)
    output.with_suffix('.json').write_text(json.dumps(dict(source_sha256=sha(source),plot_recipe_sha256=sha(Path(__file__)),
        figure_sha256=sha(output),
        caption='Same 37,801 training-period recorded fires; no labels or models used. Left: measured threshold fractions on ordinary chronological folds; lines connect thresholds, not confidence intervals. Right: within-year exact-coordinate recurrence, affected by incident counts and spatial concentration. Repeated coordinates do not prove duplicate incidents or accuracy. Distances use approximate reported points in EPSG:3978.'),indent=2)+'\n')


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--summary',type=Path,default=Path('docs/data/coordinate_quality.json'))
    parser.add_argument('--output',type=Path,default=Path('docs/figures/coordinate-quality.png'))
    args=parser.parse_args();plot(args.summary,args.output)

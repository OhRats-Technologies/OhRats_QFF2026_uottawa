"""Draw saved kernel controls; never prepare states or fit predictors."""
import numpy as np


def draw(directory):
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt

    arrays = np.load(directory / 'arrays.npz', allow_pickle=False)
    plt.rcParams.update({'font.family': 'DejaVu Sans', 'font.size': 11})
    fig, axes = plt.subplots(2, 3, figsize=(13, 7.6), layout='constrained')
    fig.suptitle('Same climate inputs. Different circuit connections.', fontsize=21, weight='bold')
    for row, graph in enumerate(['linear', 'full']):
        baseline = arrays[f'{graph}_d4_identity_kernel']
        swapped = arrays[f'{graph}_d4_middle_swap_kernel']
        for column, matrix in enumerate([baseline, swapped, swapped - baseline]):
            axis = axes[row, column]
            signed = column == 2
            image = axis.imshow(matrix, origin='lower', cmap='RdBu_r' if signed else 'viridis',
                                vmin=-1 if signed else 0, vmax=1, interpolation='nearest')
            axis.set_xticks([0, 10, 20, 30], [1988, 1998, 2008, 2018])
            axis.set_yticks([0, 10, 20, 30], [1988, 1998, 2008, 2018])
            axis.set_xlabel('Training year')
            if column == 0:
                axis.set_ylabel(('Chain' if graph == 'linear' else 'Full graph') + '\nTraining year')
            if row == 0:
                axis.set_title(['Original order: 1–2–3–4', 'Middle swap: 1–3–2–4', 'Swap minus original'][column])
            if signed:
                fig.colorbar(image, ax=axis, fraction=.046, pad=.02, label='Similarity change')
            elif column == 1:
                fig.colorbar(image, ax=axes[row, :2], fraction=.025, pad=.02, label='Fidelity kernel')
    fig.supxlabel('Four weather features · 31 training years · one-layer ZZ · angle scale π/4\n'
                  'No outcomes or predictor fits. Full-graph difference is numerical roundoff.', fontsize=11)
    output = directory / 'input-order.png'
    fig.savefig(output, dpi=170, facecolor='white')
    plt.close(fig)
    return output

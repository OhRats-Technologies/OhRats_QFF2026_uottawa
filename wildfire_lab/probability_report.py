"""Descriptive reliability summaries from existing binary probabilities."""
import numpy as np


def summarize(target, probability, bins=10, reference=.1):
    y, p = np.asarray(target), np.asarray(probability, dtype=float)
    if y.ndim != 1 or p.shape != y.shape or not len(y):
        raise ValueError('Expected nonempty matching one-dimensional arrays')
    if not np.isin(y, [0, 1]).all() or not np.isfinite(p).all() or np.any((p < 0) | (p > 1)):
        raise ValueError('Expected binary targets and probabilities in [0,1]')
    if bins < 1 or not 0 <= reference <= 1:
        raise ValueError('Invalid bins or constant reference')
    edges = np.linspace(0, 1, bins+1)
    assignment = np.minimum(np.searchsorted(edges, p, side='right')-1, bins-1)
    rows = []
    for i in range(bins):
        selected = assignment == i
        count = int(selected.sum())
        predicted, observed = (float(p[selected].mean()), float(y[selected].mean())) if count else (None, None)
        rows.append(dict(left=float(edges[i]), right=float(edges[i+1]), count=count,
            positive=int(y[selected].sum()), mean_probability=predicted, positive_fraction=observed,
            observed_minus_predicted=observed-predicted if count else None))
    return dict(rows=len(y), positive=int(y.sum()), positive_fraction=float(y.mean()),
        mean_probability=float(p.mean()), observed_minus_predicted=float(y.mean()-p.mean()),
        brier=float(np.mean((p-y)**2)), constant_probability=reference,
        constant_brier=float(np.mean((reference-y)**2)),
        count_weighted_absolute_bin_gap=sum(r['count']*abs(r['observed_minus_predicted'])
            for r in rows if r['count'])/len(y), bins=rows)

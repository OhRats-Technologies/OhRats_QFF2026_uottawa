"""Optional fourth Fireline season: train 1988-2018, play the reused 2019-2024 years.

Owner-requested teaching season. It reuses the public evaluation table, so it is
adaptive play on reused years, never research evidence. Forest inputs end in 2018;
only weather and lagged fire-memory signals are available for these rows.
"""
import csv
import itertools
from pathlib import Path

import numpy as np
from sklearn.feature_selection import mutual_info_regression
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import StandardScaler

ROOT = Path(__file__).resolve().parents[1]
TRAIN = ROOT / 'docs/data/forest_selector_scaling_training.csv'
REUSED = ROOT / 'docs/data/annual_reused_evaluation.csv'
# Same selection objective as experiments/selector_multistart.json.
K, NEIGHBORS, WEIGHT, PENALTY, SEED = 4, 3, 0.5, 2, 137
LAGS = {'lag_reported_fire_area_ha': 'total_observed_size_ha',
        'lag_recorded_incidents': 'recorded_incidents'}


def costs(train, ids, allowed):
    x = np.array([[float(r[c]) if r[c] else np.nan for c in ids] for r in train])
    x = SimpleImputer(strategy='median', keep_empty_features=True).fit_transform(x)
    x = StandardScaler().fit_transform(x)
    y = np.log1p([float(r['mean_reported_size_ha']) for r in train]).reshape(-1, 1)
    y = StandardScaler().fit_transform(y).ravel()
    relevance = mutual_info_regression(x, y, random_state=SEED, n_neighbors=NEIGHBORS)
    relevance /= max(relevance.max(), 1e-12)
    with np.errstate(invalid='ignore', divide='ignore'):
        redundancy = np.nan_to_num(np.abs(np.corrcoef(x, rowvar=False)), nan=0.)
    np.fill_diagonal(redundancy, 0.)
    linear = -relevance / K + PENALTY * (1 - 2 * K)
    pair = np.triu(WEIGHT * redundancy / (K * (K - 1) / 2) + 2 * PENALTY, 1)
    out = {}
    for subset in itertools.combinations(allowed, K):
        bits = np.zeros(len(ids))
        bits[list(subset)] = 1
        out[str(sum(1 << j for j in subset))] = float(
            bits @ linear + bits @ pair @ bits + PENALTY * K * K)
    ranked = [int(j) for j in np.argsort(-relevance, kind="stable") if j in allowed]
    return out, sorted(ranked[:K])


def final_season(features):
    ids = [f['id'] for f in features]
    train = list(csv.DictReader(TRAIN.open()))
    reused = list(csv.DictReader(REUSED.open()))
    allowed = [j for j, c in enumerate(ids) if c in reused[0] or c in LAGS]
    history = {int(r['year']): r for r in train + reused}
    rows = []
    for r in reused:
        year = int(r['year'])
        x = [float(history[year - 1][LAGS[c]]) if c in LAGS
             else float(r[c]) if c in r and r[c] else None for c in ids]
        rows.append({'year': year, 'y': float(r['mean_reported_size_ha']), 'x': x})
    objective, mi = costs(train, ids, allowed)
    exact = min(objective, key=objective.get)
    return rows, {
        'trainEnd': 2018, 'years': [r['year'] for r in rows],
        'objective': objective, 'available': allowed,
        'selectors': {'mi': mi, 'exact': [j for j in range(len(ids)) if int(exact) >> j & 1]},
        'note': 'Reused 2019-2024 years; weather and fire-memory signals only.',
    }

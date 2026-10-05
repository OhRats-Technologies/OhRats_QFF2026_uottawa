"""Exhaustive, descriptive alignment of a fixed selection proxy and validation AP."""
import numpy as np
from scipy.stats import spearmanr
from sklearn.linear_model import LogisticRegression
from wildfire_lab.constrained_selection import sampled
from wildfire_lab.evaluation import scores
from wildfire_lab.selection import configurations, energies


def inputs(train, valid, parent_plan, parent_record, columns):
    train, valid, hashes = sampled(train, valid, parent_plan, parent_record['seed'])
    assert all(parent_record[k] == v for k, v in hashes.items())
    p = parent_record['preprocessing']
    raw = train[columns].to_numpy(dtype=float)
    median = np.nan_to_num(np.nanmedian(raw, axis=0), nan=0)
    filled = np.where(np.isnan(raw), median, raw)
    mean, scale = filled.mean(axis=0), filled.std(axis=0)
    scale[scale == 0] = 1
    for key, value in [('median', median), ('mean', mean), ('scale', scale)]:
        np.testing.assert_allclose(p[key], value, atol=1e-9, rtol=1e-9)
    v = valid[columns].to_numpy(dtype=float)
    x = (filled - mean) / scale
    v = (np.where(np.isnan(v), median, v) - mean) / scale
    return x, train.target.to_numpy(), v, valid.target.to_numpy(), hashes


def masks(objective):
    bits = configurations(len(objective['linear']))
    states = np.flatnonzero(bits.sum(axis=1) == objective['k'])
    return states, bits[states], energies(objective, bits[states])


def fit_subsets(x, y, v, target, objective, logistic):
    states, bits, cost = masks(objective)
    rows = []
    for state, b, value in zip(states, bits, cost):
        indices = np.flatnonzero(b).tolist()
        model = LogisticRegression(**logistic).fit(x[:, indices], y)
        assert model.n_iter_[0] < logistic['max_iter'], 'Nonconverged fixed predictor'
        prediction = model.decision_function(v[:, indices])
        rows.append(dict(state=int(state), indices=indices, energy=float(value),
            coefficient=model.coef_[0].tolist(), intercept=float(model.intercept_[0]),
            iterations=int(model.n_iter_[0]), predictions=prediction.tolist(),
            metric=scores(target, prediction, False)))
    return rows


def describe(rows, parent_record):
    energy = np.array([r['energy'] for r in rows])
    ap = np.array([r['metric']['average_precision'] for r in rows])
    minimum = energy.min()
    optimum = np.flatnonzero(np.isclose(energy, minimum, atol=1e-10, rtol=0))
    references = {}
    for name in ['exact', 'l1']:
        prior = next(r for r in parent_record['rows'] if r['selector'] == name)
        row = next(r for r in rows if set(r['indices']) == set(prior['indices']))
        references[name] = dict(state=row['state'], energy=row['energy'],
            average_precision=row['metric']['average_precision'],
            ap_midrank_percentile=float(100 * ((ap < row['metric']['average_precision'] - 1e-12).sum()
                + .5 * np.isclose(ap, row['metric']['average_precision'], atol=1e-12, rtol=0).sum()) / len(ap)))
    rho = float(spearmanr(-energy, ap).statistic) if np.ptp(energy) and np.ptp(ap) else None
    return dict(spearman_negative_energy_ap=rho,
        ap_min=float(ap.min()), ap_max=float(ap.max()), ap_mean=float(ap.mean()),
        optimum_states=[rows[i]['state'] for i in optimum],
        optimum_ap_min=float(ap[optimum].min()), optimum_ap_max=float(ap[optimum].max()),
        exact_to_descriptive_max_ap_gap=float(ap.max() - references['exact']['average_precision']),
        references=references)


def validate(rows, x, y, v, target, objective, logistic, parent_record):
    states, bits, cost = masks(objective)
    assert [r['state'] for r in rows] == states.tolist()
    for row, b, value in zip(rows, bits, cost):
        indices = np.flatnonzero(b).tolist()
        assert row['indices'] == indices and 0 < row['iterations'] < logistic['max_iter']
        np.testing.assert_allclose(row['energy'], value, atol=1e-9, rtol=1e-9)
        prediction = v[:, indices] @ row['coefficient'] + row['intercept']
        np.testing.assert_allclose(row['predictions'], prediction, atol=1e-9, rtol=1e-9)
        for key, expected in scores(target, prediction, False).items():
            np.testing.assert_allclose(row['metric'][key], expected, atol=1e-9, rtol=1e-9)
    # Prior selector order can differ, so compare predictions rather than raw coefficients.
    for name in ['exact', 'l1']:
        prior = next(r for r in parent_record['rows'] if r['selector'] == name)
        current = next(r for r in rows if set(r['indices']) == set(prior['indices']))
        np.testing.assert_allclose(current['predictions'], prior['predictions'], atol=1e-9, rtol=1e-9)
        np.testing.assert_allclose(current['metric']['average_precision'],
            prior['metric']['average_precision'], atol=1e-9, rtol=1e-9)
    return describe(rows, parent_record)

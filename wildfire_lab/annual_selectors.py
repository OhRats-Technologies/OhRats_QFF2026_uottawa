"""Matched classical/quantum selectors for a continuous annual regression target."""

import numpy as np
from qiskit.quantum_info import Statevector
from sklearn.feature_selection import mutual_info_regression
from sklearn.linear_model import Lasso, Ridge

from wildfire_lab.annual_classical import errors, inverse, scale
from wildfire_lab.qaoa import circuit, select
from wildfire_lab.selection import configurations, energies, exact_subset
from wildfire_lab.sqd_selection import sampled_subspace


def objective(x, y, plan, seed):
    relevance = mutual_info_regression(x, y, random_state=seed,
                                      n_neighbors=plan['relevance_neighbors'])
    relevance /= max(float(relevance.max()), 1e-12)
    with np.errstate(invalid='ignore', divide='ignore'):
        redundancy = np.nan_to_num(np.abs(np.corrcoef(x, rowvar=False)), nan=0.)
    np.fill_diagonal(redundancy, 0.)
    k, penalty = plan['selected_count'], plan['cardinality_penalty']
    pair_count = k * (k - 1) / 2
    return dict(relevance=relevance, redundancy=redundancy,
                linear=-relevance / k + penalty * (1 - 2 * k),
                pair=np.triu(plan['redundancy_weight'] * redundancy / pair_count + 2 * penalty, 1),
                constant=penalty * k * k, k=k, penalty=penalty)


def selectors(x, y, features, parent, plan, seed):
    obj = objective(x, y, plan, seed)
    exact, best_cost = exact_subset(obj)
    quantum, diagnostic = select(obj, seed=seed, **plan['qaoa'])
    bits = configurations(len(features))
    costs = energies(obj, bits)
    uniform_draws = np.random.default_rng(seed).integers(len(bits), size=plan['qaoa']['shots'])
    eligible = uniform_draws[bits[uniform_draws].sum(axis=1) == obj['k']]
    uniform = np.flatnonzero(bits[eligible[np.argmin(costs[eligible])]]).tolist() if len(eligible) else None
    lasso = Lasso(alpha=plan['lasso_alpha'], max_iter=10000).fit(x, y)
    choices = dict(
        physical_four=[features.index(name) for name in parent['four_feature_subset']],
        all_ten=list(range(len(features))),
        lasso_ranking=np.argsort(-np.abs(lasso.coef_), kind='stable')[:obj['k']].tolist(),
        mutual_information=np.argsort(-obj['relevance'], kind='stable')[:obj['k']].tolist(),
        exact_same_qubo=exact, qaoa_same_qubo=quantum,
        uniform_bitstring_budget=uniform,
        random_four=np.sort(np.random.default_rng(seed).choice(len(features), obj['k'], replace=False)).tolist(),
    )
    sqd = [dict(source='uniform', **sampled_subspace(obj, uniform_draws))]
    if quantum is not None:
        probability = Statevector.from_instruction(circuit(obj, diagnostic['parameters'])).probabilities()
        rng = np.random.default_rng(seed)
        rng.uniform(0, .5, 2 * plan['qaoa']['depth'])
        draws = rng.choice(len(bits), size=plan['qaoa']['shots'], p=probability)
        sqd.append(dict(source='qaoa', **sampled_subspace(obj, draws)))
        if sqd[-1]['selected_subset'] != quantum:
            raise ValueError('SQD reconstruction does not match QAOA sampled selection')
    metadata = dict(relevance=obj['relevance'].tolist(), redundancy=obj['redundancy'].tolist(),
                    exact_objective=best_cost, qaoa=diagnostic, sqd=sqd,
                    extra_sampling_state_evaluations=int(quantum is not None),
                    lasso_iterations=int(lasso.n_iter_), feasible_subsets=210)
    return choices, obj, metadata


def screen(table, parent, plan):
    results, records = [], []
    features = parent['features']
    for fold in plan['folds']:
        first, last, valid_first, valid_last = fold
        train = table[table.year.between(first, last)]
        validation = table[table.year.between(valid_first, valid_last)]
        x, cross, y, y_scaler = scale(train[features].to_numpy(), validation[features].to_numpy(),
                                      train.mean_reported_size_ha.to_numpy())
        actual = validation.mean_reported_size_ha.to_numpy()
        for seed in plan['seeds']:
            choices, obj, metadata = selectors(x, y, features, parent, plan, seed)
            records.append(dict(fold=fold, seed=seed, **metadata))
            for name, indices in choices.items():
                if indices is None:
                    results.append(dict(selector=name, fold=fold, seed=seed, status='no_feasible_draw'))
                    continue
                model = Ridge(alpha=1.).fit(x[:, indices], y)
                prediction = inverse(model.predict(cross[:, indices]), y_scaler)
                bitstring = np.zeros((1, len(features)))
                bitstring[0, indices] = 1
                results.append(dict(selector=name, fold=fold, seed=seed, status='complete',
                                    feature_indices=indices, features=[features[i] for i in indices],
                                    objective=float(energies(obj, bitstring)[0]),
                                    objective_gap=float(energies(obj, bitstring)[0] - metadata['exact_objective']),
                                    years=validation.year.tolist(), actual_ha=actual.tolist(),
                                    predicted_ha=prediction.tolist(), **errors(actual, prediction)))
    return results, records

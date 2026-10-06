"""Chronological inner tuning with fold-local input and target preparation."""
from itertools import product
import time
import numpy as np
from sklearn.feature_selection import mutual_info_regression
from sklearn.linear_model import Ridge
from sklearn.model_selection import TimeSeriesSplit
from sklearn.svm import SVR
from qiskit_machine_learning.algorithms import QSVR
from wildfire_lab.annual_classical import errors, inverse, gamma
from wildfire_lab.forest_models import prepare, rbf
from wildfire_lab.search_kernels import candidates, matrices


def prepared(train, valid, panel, plan):
    columns = plan['panels'][panel]
    selection = None
    if panel == 'mi4':
        pool = plan['candidate_features']
        x, _, y, _, prep = prepare(train[pool].to_numpy(), valid[pool].to_numpy(),
                                  train.mean_reported_size_ha.to_numpy())
        relevance = mutual_info_regression(x, y, n_neighbors=3, random_state=137)
        indices = np.sort(np.argsort(-relevance, kind='stable')[:4])
        columns = [pool[index] for index in indices]
        selection = dict(relevance=relevance.tolist(), indices=indices.tolist(),
                         preprocessing=prep, labelled_years=train.year.tolist())
    x, cross, y, scaler, prep = prepare(
        train[columns].to_numpy(), valid[columns].to_numpy(),
        train.mean_reported_size_ha.to_numpy())
    return dict(x=x, cross=cross, y=y, scaler=scaler,
                actual=valid.mean_reported_size_ha.to_numpy(), columns=columns,
                preprocessing=prep, selection=selection,
                train_years=train.year.tolist(), validation_years=valid.year.tolist())


def grid(plan):
    svr = [dict(C=c, epsilon=epsilon) for c, epsilon in product(
        plan['svr']['C'], plan['svr']['epsilon'])]
    quantum = [dict(model='qsvr', circuit=specification, **parameters)
               for specification, parameters in product(candidates(plan['quantum']), svr)]
    classical = [dict(model='rbf', multiplier=value, **parameters)
                 for value, parameters in product(plan['rbf_multipliers'], svr)]
    ridge = [dict(model='ridge', alpha=value) for value in plan['ridge_alpha']]
    return quantum + classical + ridge


def kernel_inputs(data, specification, plan, cache):
    if specification['model'] == 'ridge':
        return data['x'], data['cross'], dict(state_evaluations=0, seconds=0)
    if specification['model'] == 'rbf':
        key = ('rbf', specification['multiplier'])
        if key not in cache:
            bandwidth = gamma(data['x'])*specification['multiplier']
            cache[key] = (rbf(data['x'], data['x'], bandwidth),
                          rbf(data['x'], data['cross'], bandwidth),
                          dict(state_evaluations=0, seconds=0, gamma=bandwidth))
    else:
        circuit = specification['circuit']
        key = ('quantum', tuple(circuit.items()))
        if key not in cache:
            cache[key] = matrices(data['x'], data['cross'], circuit, plan['quantum'])
    return cache[key]


def model(specification):
    if specification['model'] == 'ridge':
        return Ridge(alpha=specification['alpha'])
    kwargs = dict(C=specification['C'], epsilon=specification['epsilon'])
    if specification['model'] == 'qsvr':
        return QSVR(quantum_kernel='precomputed', **kwargs)
    return SVR(kernel='precomputed', **kwargs)


def tune(train, panel, plan):
    started = time.perf_counter()
    splits = []
    for indices, validation in TimeSeriesSplit(n_splits=3).split(train):
        data = prepared(train.iloc[indices], train.iloc[validation], panel, plan)
        splits.append((data, {}))
    records = []
    for specification in grid(plan):
        actual, prediction, fold_scores = [], [], []
        for data, cache in splits:
            gram, cross, _ = kernel_inputs(data, specification, plan, cache)
            fitted = model(specification).fit(gram, data['y'])
            predicted = inverse(fitted.predict(cross), data['scaler'])
            actual.extend(data['actual'])
            prediction.extend(predicted)
            fold_scores.append(errors(data['actual'], predicted))
        records.append(dict(specification=specification, inner_scores=fold_scores,
                            predicted_ha=prediction, **errors(np.array(actual), np.array(prediction))))
    chosen = {kind: min((row for row in records if row['specification']['model'] == kind),
                       key=lambda row: row['mae_ha'])['specification']
              for kind in ['ridge', 'rbf', 'qsvr']}
    # The inner fold selections are data objects, not one selection made using
    # the full outer training set. Thus held-out inner labels cannot enter MI.
    split_records = []
    for data, cache in splits:
        split_records.append(dict(
            train_years=data['train_years'], validation_years=data['validation_years'],
            columns=data['columns'], selection=data['selection'],
            preprocessing=data['preprocessing'], actual_ha=data['actual'].tolist(),
            state_evaluations=sum(value[2]['state_evaluations'] for value in cache.values()),
            quantum_kernel_pairs=sum(len(data['x'])*(len(data['x'])-1)//2+
                                     len(data['x'])*len(data['cross'])
                                     for key in cache if key[0] == 'quantum'),
            kernel_seconds=sum(value[2]['seconds'] for value in cache.values())))
    return dict(chosen=chosen, candidates=records, inner_splits=split_records,
                predictor_fits=len(records)*3, seconds=time.perf_counter()-started)


def evaluate(data, specification, plan):
    gram, cross, resource = kernel_inputs(data, specification, plan, {})
    fitted = model(specification).fit(gram, data['y'])
    scaled_prediction = fitted.predict(cross)
    prediction = inverse(scaled_prediction, data['scaler'])
    parameters = dict(intercept=float(np.asarray(fitted.intercept_).ravel()[0]))
    if specification['model'] == 'ridge':
        parameters['coef'] = fitted.coef_.tolist()
    else:
        parameters.update(support=fitted.support_.tolist(),
                          dual_coef=fitted.dual_coef_.ravel().tolist())
    return dict(specification=specification, columns=data['columns'],
                preprocessing=data['preprocessing'], selection=data['selection'],
                scaled_train=data['x'].tolist(), scaled_cross=data['cross'].tolist(),
                scaled_targets=data['y'].tolist(), parameters=parameters,
                train_matrix=gram.tolist(), cross_matrix=cross.tolist(),
                predicted_scaled=scaled_prediction.tolist(), predicted_ha=prediction.tolist(),
                actual_ha=data['actual'].tolist(), resource=resource,
                **errors(data['actual'], prediction))

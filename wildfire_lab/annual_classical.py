"""Chronological annual regression controls with fold-local preprocessing."""

import numpy as np
from sklearn.impute import SimpleImputer
from sklearn.linear_model import Ridge
from sklearn.metrics import mean_absolute_error, mean_squared_error
from sklearn.model_selection import TimeSeriesSplit
from sklearn.preprocessing import StandardScaler
from sklearn.svm import SVR


def errors(actual, prediction):
    return dict(mae_ha=float(mean_absolute_error(actual, prediction)),
                rmse_ha=float(mean_squared_error(actual, prediction) ** .5),
                bias_ha=float(np.mean(prediction - actual)))


def scale(train_x, validation_x, train_y):
    imputer = SimpleImputer(strategy='median', keep_empty_features=True)
    scaler = StandardScaler()
    x = scaler.fit_transform(imputer.fit_transform(train_x))
    cross = scaler.transform(imputer.transform(validation_x))
    y_scaler = StandardScaler()
    y = y_scaler.fit_transform(np.log1p(train_y).reshape(-1, 1)).ravel()
    return x, cross, y, y_scaler


def inverse(values, scaler):
    log_values = scaler.inverse_transform(np.asarray(values).reshape(-1, 1)).ravel()
    return np.maximum(0, np.expm1(log_values))


def gamma(x):
    distances = np.sum((x[:, None] - x[None, :]) ** 2, axis=-1)
    positive = distances[distances > 0]
    return 1 / np.median(positive) if positive.size else 1.0


def fit_predict(kind, train_x, validation_x, train_y, params):
    x, cross, y, y_scaler = scale(train_x, validation_x, train_y)
    if kind == 'ridge':
        model = Ridge(alpha=params['alpha'])
    else:
        model = SVR(kernel=kind, C=params['C'], epsilon=params['epsilon'],
                    gamma=gamma(x) if kind == 'rbf' else 'scale')
    model.fit(x, y)
    return inverse(model.predict(cross), y_scaler)


def grid(kind, plan):
    if kind == 'ridge':
        return [dict(alpha=alpha) for alpha in plan['ridge_alpha']]
    return [dict(C=c, epsilon=e) for c in plan['svr_grid']['C']
            for e in plan['svr_grid']['epsilon']]


def tune(kind, x, y, plan):
    scores = []
    for params in grid(kind, plan):
        actual, predictions = [], []
        for train, validation in TimeSeriesSplit(n_splits=3).split(x):
            predictions.extend(fit_predict(kind, x[train], x[validation], y[train], params))
            actual.extend(y[validation])
        scores.append(dict(params=params, **errors(np.array(actual), np.array(predictions))))
    chosen = min(scores, key=lambda r: r['mae_ha'])
    return chosen['params'], scores


def screen(table, plan):
    output = []
    for first, last, valid_first, valid_last in plan['development_folds']:
        train = table[table.year.between(first, last)]
        validation = table[table.year.between(valid_first, valid_last)]
        y = train.mean_reported_size_ha.to_numpy()
        actual = validation.mean_reported_size_ha.to_numpy()
        for label, prediction in [
            ('training_mean', np.repeat(np.mean(y), len(actual))),
            ('training_median', np.repeat(np.median(y), len(actual))),
            ('linear_year_trend', np.maximum(0, np.polyval(
                np.polyfit(train.year, y, 1), validation.year))),
        ]:
            output.append(dict(model=label, features=[], fold=[first, last, valid_first, valid_last],
                               years=validation.year.tolist(), actual_ha=actual.tolist(),
                               predicted_ha=prediction.tolist(), **errors(actual, prediction)))
        for features in [plan['four_feature_subset'], plan['features']]:
            x, cross = train[features].to_numpy(), validation[features].to_numpy()
            for kind in ['ridge', 'linear', 'rbf']:
                chosen, tuning = tune(kind, x, y, plan)
                prediction = fit_predict(kind, x, cross, y, chosen)
                output.append(dict(model=kind, features=features, chosen=chosen,
                                   inner_tuning=tuning, fold=[first, last, valid_first, valid_last],
                                   years=validation.year.tolist(), actual_ha=actual.tolist(),
                                   predicted_ha=prediction.tolist(), **errors(actual, prediction)))
    return output

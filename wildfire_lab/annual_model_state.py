"""JSON model/scaler states permit frozen annual predictions without refitting."""

import numpy as np
from sklearn.impute import SimpleImputer
from sklearn.linear_model import Ridge
from sklearn.preprocessing import StandardScaler
from sklearn.svm import SVR
from qiskit_machine_learning.algorithms import QSVR


def fit_scaling(values, target):
    imputer = SimpleImputer(strategy='median', keep_empty_features=True)
    scaler = StandardScaler()
    x = scaler.fit_transform(imputer.fit_transform(values))
    target_scaler = StandardScaler()
    y = target_scaler.fit_transform(np.log1p(target).reshape(-1, 1)).ravel()
    state = dict(medians=imputer.statistics_.tolist(), means=scaler.mean_.tolist(),
                 scales=scaler.scale_.tolist(), target_mean=float(target_scaler.mean_[0]),
                 target_scale=float(target_scaler.scale_[0]))
    return x, y, state


def transform(values, scaling):
    values = np.asarray(values, dtype=float)
    return (np.where(np.isnan(values), scaling['medians'], values) - scaling['means']) / scaling['scales']


def inverse(values, scaling):
    return np.maximum(0, np.expm1(scaling['target_mean'] + scaling['target_scale'] * np.asarray(values)))


def fit_state(kind, x, y, params):
    if kind == 'ridge':
        model = Ridge(alpha=params['alpha'])
    elif kind == 'linear':
        model = SVR(kernel='linear', **params)
    elif kind == 'quantum':
        model = QSVR(quantum_kernel='precomputed', **params)
    elif kind == 'rbf':
        model = SVR(kernel='precomputed', **params)
    else:
        raise ValueError(f'Unknown annual model: {kind}')
    model.fit(x, y)
    state = dict(kind=kind, intercept=float(model.intercept_[0] if kind != 'ridge' else model.intercept_))
    if kind in ['ridge', 'linear']:
        state['coefficients'] = np.asarray(model.coef_).ravel().tolist()
    else:
        state.update(support=model.support_.tolist(), dual=model.dual_coef_[0].tolist())
    if kind != 'ridge':
        state.update(fit_status=int(model.fit_status_), support_count=int(len(model.support_)))
        if model.fit_status_ != 0:
            raise ValueError('Annual SVR did not converge')
    np.testing.assert_allclose(predict_scaled(state, x), model.predict(x), rtol=1e-9, atol=1e-9)
    return state


def predict_scaled(state, values):
    values = np.asarray(values)
    if state['kind'] in ['ridge', 'linear']:
        return values @ state['coefficients'] + state['intercept']
    return values[:, state['support']] @ state['dual'] + state['intercept']

"""Verify stored train-only preprocessing and regression equations without fitting."""
import numpy as np
from wildfire_lab.forest_collect import check_preprocessing
from wildfire_lab.forest_models import rbf
from wildfire_lab.annual_classical import errors, gamma


def check(train, valid, record, plan):
    columns = record['rows'][0]['features']
    targets = train.mean_reported_size_ha.to_numpy()
    actual = valid.mean_reported_size_ha.to_numpy()
    x, v, y = check_preprocessing(train[columns].to_numpy(), valid[columns].to_numpy(),
                                  targets, record)
    np.testing.assert_allclose(gamma(x), record['rbf_gamma'], atol=1e-10)
    gram, cross = np.array(record['quantum_gram']), np.array(record['quantum_cross'])
    assert gram.shape == (len(x),len(x)) and cross.shape == (len(v),len(x))
    np.testing.assert_allclose(gram,gram.T,atol=1e-10)
    np.testing.assert_allclose(np.diag(gram),1.,atol=1e-10)
    assert np.linalg.eigvalsh(gram).min() >= -1e-7
    assert min(gram.min(), cross.min()) >= -1e-10 and max(gram.max(), cross.max()) <= 1+1e-10
    for row in record['rows']:
        assert row['features'] == columns
        parameters = row['parameters']
        if row['model'] == 'ridge':
            coef = np.array(parameters['coef'])
            prediction = v@coef+parameters['intercept']
            residual = x@coef+parameters['intercept']-y
            np.testing.assert_allclose(x.T@residual+plan['models']['ridge']['alpha']*coef,0,atol=1e-8)
            np.testing.assert_allclose(residual.mean(),0,atol=1e-9)
        else:
            matrix = cross if row['model']=='qsvr' else rbf(x,v,record['rbf_gamma'])
            prediction = matrix[:,parameters['support']]@np.array(parameters['dual_coef'])+parameters['intercept']
        p = record['preprocessing']
        hectares = np.maximum(0,np.expm1(prediction*p['y_scale']+p['y_mean']))
        np.testing.assert_allclose(prediction,row['predicted_scaled'],atol=1e-9)
        np.testing.assert_allclose(hectares,row['predicted_ha'],atol=1e-7)
        np.testing.assert_allclose(actual,row['actual_ha'],atol=1e-9)
        for metric,value in errors(actual,hectares).items():
            np.testing.assert_allclose(value,row[metric],atol=1e-7)
    return len(record['rows']), record['resource']['pair_circuits']

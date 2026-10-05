"""Frozen learned coefficients and scaler state must retain predictor behavior."""

import json
import unittest
import numpy as np
from sklearn.metrics.pairwise import rbf_kernel
from sklearn.svm import SVR
from wildfire_lab.annual_model_state import fit_scaling, fit_state, predict_scaled, transform, inverse


class ModelStateTests(unittest.TestCase):
    def test_serialized_state_preserves_missing_value_scaling(self):
        values = np.array([[1., np.nan], [2., 3.], [3., 5.]])
        x, y, state = fit_scaling(values, np.array([0., 10., 30.]))
        parsed = json.loads(json.dumps(state))
        np.testing.assert_allclose(transform(values, parsed), x)
        np.testing.assert_allclose(inverse(y, parsed), [0., 10., 30.], atol=1e-12)
        future = transform([[100., np.nan]], parsed)
        self.assertGreater(future[0, 0], 100)
        self.assertEqual(future[0, 1], 0.)

    def test_cached_dual_state_matches_svr_and_qsvr_predictions(self):
        x = np.array([[0.], [.3], [1.], [2.]])
        y = np.array([-1., -.8, .3, 1.])
        cross_x = np.array([[.5], [3.]])
        gram, cross = rbf_kernel(x, gamma=.7), rbf_kernel(cross_x, x, gamma=.7)
        parameters = dict(C=1., epsilon=.1)
        reference = SVR(kernel='precomputed', **parameters).fit(gram, y).predict(cross)
        for kind in ['rbf', 'quantum']:
            state = json.loads(json.dumps(fit_state(kind, gram, y, parameters)))
            np.testing.assert_allclose(predict_scaled(state, cross), reference, atol=1e-10)


if __name__ == '__main__':
    unittest.main()

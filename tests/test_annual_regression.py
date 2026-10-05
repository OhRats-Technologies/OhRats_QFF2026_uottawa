"""Leakage and actual quantum-kernel equivalence checks for annual regression."""

import tempfile
import unittest
from pathlib import Path

import numpy as np
from qiskit.circuit.library import zz_feature_map
from qiskit.quantum_info import Statevector
from wildfire_lab.annual_classical import scale, inverse
from wildfire_lab.annual_quantum import kernel_fold, predict_cached
from sklearn.svm import SVR


class AnnualRegressionTests(unittest.TestCase):
    def test_validation_values_do_not_set_scaling(self):
        train = np.array([[1., 2.], [3., 4.]])
        x, cross, y, scaler = scale(train, np.array([[1000., 1000.]]), np.array([5., 50.]))
        np.testing.assert_allclose(x.mean(axis=0), 0, atol=1e-12)
        self.assertGreater(cross.min(), 900)
        np.testing.assert_allclose(inverse(y, scaler), [5., 50.])

    def test_qsvr_precomputed_uses_the_same_regression_problem(self):
        x = np.array([[1., 0.], [.5, .5], [0., 1.]])
        gram, cross = x @ x.T, np.array([[.2, .8]]) @ x.T
        _, _, y, scaler = scale(x, x, np.array([5., 15., 50.]))
        params = dict(C=1., epsilon=.2)
        expected = inverse(SVR(kernel='precomputed', **params).fit(gram, y).predict(cross), scaler)
        np.testing.assert_allclose(predict_cached(gram, cross, y, scaler, params), expected)

    def test_actual_fidelity_api_matches_state_overlaps(self):
        x = np.array([[0., 1., 2., 3.], [1., 2., 0., 2.], [2., 0., 1., 0.]])
        cross = np.array([[1., .5, 2., 1.]])
        with tempfile.TemporaryDirectory() as temporary:
            gram, measured, _, _, receipt = kernel_fold(
                x, cross, np.array([1., 5., 20.]), Path(temporary) / 'kernel', 1, .7853981634)
            saved = np.load(Path(temporary) / 'kernel/matrices.npz')
            circuit = zz_feature_map(4, reps=1, entanglement='linear')
            states = [Statevector(circuit.assign_parameters(row)).data for row in saved['train_angles']]
            validation = Statevector(circuit.assign_parameters(saved['cross_angles'][0])).data
            expected = np.abs(np.array(states).conj() @ np.array(states).T) ** 2
            np.testing.assert_allclose(gram, expected, atol=1e-9)
            np.testing.assert_allclose(measured[0], np.abs(np.array(states).conj() @ validation) ** 2,
                                       atol=1e-9)
            self.assertEqual(receipt['hardware_jobs_submitted'], 0)


if __name__ == '__main__':
    unittest.main()

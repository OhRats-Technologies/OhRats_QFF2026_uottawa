"""Offline replay must reject changed predictions and cannot call producers."""
from pathlib import Path
import unittest
from unittest.mock import patch
import numpy as np
from wildfire_lab.saved_search import collect, prediction

ROOT = Path(__file__).resolve().parents[1]


class SavedTests(unittest.TestCase):
    def test_both_public_bundles_without_producers(self):
        with patch('socket.socket', side_effect=AssertionError('Network forbidden')), \
             patch('numpy.random.default_rng', side_effect=AssertionError('Sampling forbidden')):
            for study in ['selector-multistart', 'expanded-tuning', 'expanded-tuning-distinct',
                          'expanded-proxy-controls', 'shallow-preparation', 'objective-alignment']:
                result = collect(ROOT, study)
                self.assertEqual(result['status'], 'passed')
                self.assertEqual(result['predictor_fits'], 0)
                self.assertEqual(result['new_quantum_states'], 0)

    def test_changed_saved_prediction_is_rejected(self):
        row = dict(parameters=dict(coef=[1.], intercept=0.), predicted_scaled=[0.],
                   predicted_ha=[0.], actual_ha=[0.], mae_ha=0., rmse_ha=0., bias_ha=0.)
        with self.assertRaises(AssertionError):
            prediction(row, dict(y_scale=1., y_mean=0.), [[2.]])


if __name__ == '__main__':
    unittest.main()

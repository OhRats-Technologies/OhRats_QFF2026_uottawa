"""Frozen final states, exclusive opening and label-independent predictions."""

import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import numpy as np
import pandas as pd

from wildfire_lab.annual_data import digest
from wildfire_lab.annual_final_kernel import TrainingKernels, evaluate_cross
from wildfire_lab.annual_final_protocol import evaluate
from wildfire_lab.annual_final_evaluate import predict_models


class FinalProtocolTests(unittest.TestCase):
    def test_recipe_change_stops_before_test_preparation(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            plan = root / 'plan.json'
            plan.write_text('{}')
            training = root / 'training.json'
            training.write_text('{}')
            (root / 'training_receipt.json').write_text(json.dumps(dict(
                training_sha256=digest(training), plan_sha256=digest(plan), code_sha256={'recipe': 'old'})))
            with patch('wildfire_lab.annual_final_protocol.inputs', return_value=({}, [])), \
                    patch('wildfire_lab.annual_final_protocol.current_code', return_value={'recipe': 'new'}), \
                    patch('wildfire_lab.annual_final_protocol.prepare') as preparation:
                with self.assertRaisesRegex(ValueError, 'recipe changed'):
                    evaluate(root, plan, root)
                preparation.assert_not_called()
                self.assertFalse((root / 'evaluation').exists())

    def test_existing_evaluation_intent_never_restarts(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / 'data/raw/nfdb-audit').mkdir(parents=True)
            source = root / 'data/raw/nfdb-audit/source.zip'
            source.write_bytes(b'fixture')
            weather = root / 'weather.csv'
            weather.write_text('fixture')
            plan_path = root / 'plan.json'
            plan_path.write_text('{}')
            (root / 'training.json').write_text(json.dumps(dict(dependencies={'fixture': '1'})))
            (root / 'training_receipt.json').write_text(json.dumps(dict(
                training_sha256=digest(root / 'training.json'), plan_sha256=digest(plan_path), code_sha256={})))
            (root / 'evaluation').mkdir()
            intent = root / 'evaluation/intent.json'
            intent.write_text('{"preserve":true}')
            plan = dict(weather_path='weather.csv', nfdb_sha256=digest(source), weather_sha256=digest(weather))
            with patch('wildfire_lab.annual_final_protocol.inputs', return_value=(plan, [])), \
                    patch('wildfire_lab.annual_final_protocol.current_code', return_value={}), \
                    patch('wildfire_lab.annual_final_protocol.dependencies', return_value={'fixture': '1'}), \
                    patch('wildfire_lab.annual_final_protocol.prepare') as preparation:
                with self.assertRaises(FileExistsError):
                    evaluate(root, plan_path, root)
                preparation.assert_not_called()
            self.assertEqual(intent.read_text(), '{"preserve":true}')

    def test_predictions_do_not_change_with_test_labels(self):
        scaling = dict(medians=[0.], means=[0.], scales=[1.], target_mean=0., target_scale=1.)
        model = dict(id='fixture', kind='ridge', features=['temp'], scaling=scaling,
                     state=dict(kind='ridge', coefficients=[.2], intercept=.1))
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            table = pd.DataFrame(dict(year=[2019, 2020], temp=[1., 2.], mean_reported_size_ha=[10., 20.]))
            first, _ = predict_models([model], table, [], root, root, {})
            table['mean_reported_size_ha'] = [1000., 0.]
            second, _ = predict_models([model], table, [], root, root, {})
            self.assertEqual(first[0]['predicted_ha'], second[0]['predicted_ha'])
            self.assertNotEqual(first[0]['mae_ha'], second[0]['mae_ha'])

    def test_actual_kernel_cache_reuses_training_and_separates_cross(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            table = pd.DataFrame(dict(temp=[1., 2., 3.], precip=[3., 1., 2.],
                                      mean_reported_size_ha=[0., 10., 30.]))
            cache = TrainingKernels(root / 'kernels')
            params = dict(reps=1, amplitude=.5)
            gram, entry = cache.get(table, ['temp', 'precip'], 'quantum', params)
            repeated, same = cache.get(table, ['temp', 'precip'], 'quantum', params)
            self.assertEqual(entry['id'], same['id'])
            self.assertEqual(len(cache.entries), 1)
            np.testing.assert_array_equal(gram, repeated)
            path = root / 'kernels' / entry['id'] / 'matrix.npz'
            saved = np.load(path)
            cross, receipt = evaluate_cross(entry, saved, np.zeros((2, 2)), root / 'cross')
            self.assertEqual(cross.shape, (2, 3))
            self.assertEqual(receipt['pair_circuits'], 6)


if __name__ == '__main__':
    unittest.main()

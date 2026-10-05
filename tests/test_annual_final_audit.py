import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import numpy as np
import pandas as pd

from wildfire_lab.annual_data import digest
from wildfire_lab.annual_final_audit import collect, gram_diagnostic


class FinalCollectionTests(unittest.TestCase):
    def fixture(self, root):
        run = root / 'run'
        (run / 'evaluation/data').mkdir(parents=True)
        train = root / 'training.csv'
        pd.DataFrame(dict(year=range(1988, 2019))).to_csv(train, index=False)
        test = run / 'evaluation/data/annual.csv'
        pd.DataFrame(dict(year=range(2019, 2025), mean_reported_size_ha=range(1, 7))).to_csv(test, index=False)
        plan = root / 'plan.json'
        plan.write_text(json.dumps(dict(training_dataset='training.csv', training_sha256=digest(train),
                                       budget=dict(maximum_training_quantum_matrices=50))))
        model = dict(id='training_mean', kind='constant', prediction_ha=3.)
        training = run / 'training.json'
        training.write_text(json.dumps(dict(main_models=[model], crossed_models=[], kernels=[],
                                            training_quantum_matrices=0)))
        receipt = dict(plan_sha256=digest(plan), training_sha256=digest(training), code_sha256={})
        (run / 'training_receipt.json').write_text(json.dumps(receipt))
        actual, prediction = np.arange(1., 7.), np.repeat(3., 6)
        row = dict(id=model['id'], actual_ha=actual.tolist(), predicted_ha=prediction.tolist(),
                   absolute_errors_ha=np.abs(prediction-actual).tolist(), mae_ha=1.5,
                   rmse_ha=float(np.sqrt(((prediction-actual)**2).mean())), bias_ha=-.5)
        outcome = dict(training_receipt=receipt, predictor_fits=0,
                       dataset_manifest=dict(table_sha256=digest(test)),
                       main_results=[row], crossed_results=[], cross_resources=[])
        (run / 'evaluation/outcome.json').write_text(json.dumps(outcome))
        return run, plan

    @patch('wildfire_lab.annual_final_audit.current_code', return_value={})
    def test_saved_prediction_reconstructs_without_predictor_fits(self, _):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            run, plan = self.fixture(root)
            receipt = collect(root, run, plan)
            self.assertEqual(receipt['prediction_records_checked'], 1)
            self.assertEqual(receipt['collection_predictor_fits'], 0)

    @patch('wildfire_lab.annual_final_audit.current_code', return_value={})
    def test_changed_saved_score_is_detected(self, _):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            run, plan = self.fixture(root)
            path = run / 'evaluation/outcome.json'
            outcome = json.loads(path.read_text())
            outcome['main_results'][0]['mae_ha'] = 0.
            path.write_text(json.dumps(outcome))
            with self.assertRaises(AssertionError):
                collect(root, run, plan)

    def test_flat_exact_gram_has_identity_spectrum(self):
        entry = dict(id='kernel', kind='quantum', features=['x']*10, params={})
        receipt = gram_diagnostic(entry, np.eye(31), np.zeros((6, 31)))
        self.assertAlmostEqual(receipt['effective_rank'], 31.)
        self.assertAlmostEqual(receipt['condition_number'], 1.)
        self.assertEqual(receipt['cross_mean'], 0.)


if __name__ == '__main__':
    unittest.main()

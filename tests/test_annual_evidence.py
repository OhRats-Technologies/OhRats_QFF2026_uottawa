"""Scientific reporting must reject altered saved metrics."""

import unittest
from wildfire_lab.annual_evidence import validate_metrics


class EvidenceTests(unittest.TestCase):
    def test_saved_metric_change_is_detected(self):
        row = dict(actual_ha=[0., 2.], predicted_ha=[0., 0.], mae_ha=1., rmse_ha=2 ** .5, bias_ha=-1.)
        self.assertEqual(validate_metrics([row]), 1)
        row['mae_ha'] = .1
        with self.assertRaises(AssertionError):
            validate_metrics([row])


if __name__ == '__main__':
    unittest.main()

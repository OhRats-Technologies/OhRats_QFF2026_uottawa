import unittest
import numpy as np
from wildfire_lab.probability_report import summarize


class ProbabilityReportTests(unittest.TestCase):
    def test_boundaries_empty_bins_and_weighted_totals(self):
        result = summarize([0, 1, 0, 1], [0, .1, .9, 1], bins=10, reference=.25)
        self.assertEqual([r['count'] for r in result['bins']], [1, 1, 0, 0, 0, 0, 0, 0, 0, 2])
        self.assertIsNone(result['bins'][2]['mean_probability'])
        self.assertEqual(sum(r['count'] for r in result['bins']), 4)
        self.assertEqual(sum(r['positive'] for r in result['bins']), 2)
        self.assertAlmostEqual(result['brier'], .405)
        self.assertAlmostEqual(result['constant_brier'], .3125)
        self.assertAlmostEqual(result['count_weighted_absolute_bin_gap'], .45)

    def test_perfect_bin_calibration_does_not_mean_zero_brier(self):
        result = summarize([0, 0, 1, 1], [.5]*4)
        self.assertEqual(result['count_weighted_absolute_bin_gap'], 0)
        self.assertEqual(result['observed_minus_predicted'], 0)
        self.assertEqual(result['brier'], .25)

    def test_invalid_probabilities_and_targets_rejected(self):
        for y,p in [([], []), ([0], [np.nan]), ([0], [-.1]), ([0], [1.1]),
                    ([2], [.5]), ([0,1], [.5]), ([[0]], [[.5]])]:
            with self.assertRaises(ValueError):
                summarize(y, p)


if __name__ == '__main__':
    unittest.main()

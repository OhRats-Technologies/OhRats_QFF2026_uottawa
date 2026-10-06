"""Measured kernel assembly/repairs and immutable count accounting."""
import unittest
from pathlib import Path
from unittest.mock import patch
import numpy as np
from wildfire_lab.tuned_kernel_analysis import variants
from wildfire_lab.saved_hardware_search import measured, collect


class MeasuredTests(unittest.TestCase):
    def test_all_published_counts_and_equations_replay_offline(self):
        root = Path(__file__).resolve().parents[1]
        with patch('socket.socket', side_effect=AssertionError('Network forbidden')), \
             patch('numpy.random.default_rng', side_effect=AssertionError('Sampling forbidden')):
            for study in ['shallow-hardware-search', 'basis-confirmation-marrakesh',
                          'basis-confirmation-quebec', 'tuned-kernel-hardware']:
                result = collect(root, study)
                self.assertEqual(result['status'], 'passed')
                self.assertEqual(result['hardware_jobs_submitted'], 0)

    def test_perfect_readout_retains_all_declared_kernel_arms(self):
        counts = [{'0000': 128}, {'0000': 32, '0001': 96}, {'0000': 128},
                  {'0000': 64, '0001': 64}, {'0000': 16, '0010': 112}]
        arms, diagnostic = variants(counts, np.repeat(np.eye(2)[None], 4, axis=0), 2, 1)
        self.assertEqual(len(arms), 6)
        for gram, cross in arms.values():
            np.testing.assert_allclose(gram, [[1., .25], [.25, 1.]])
            np.testing.assert_allclose(cross, [[.5, .125]])
        self.assertEqual(len(diagnostic), 5)

    def test_changed_hardware_feasible_accounting_is_rejected(self):
        row = dict(measured_counts={'01': 10, '00': 90}, shots=100, feasible_shots=11)
        objective = dict(linear=[-2., -2.], pair=[[0., 4.], [0., 0.]], constant=2., k=1)
        with self.assertRaises(AssertionError):
            measured(row, objective)


if __name__ == '__main__':
    unittest.main()

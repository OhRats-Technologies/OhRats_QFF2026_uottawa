"""Shot-count intervals and exact accounting of saved classical control draws."""
import base64
import unittest
from pathlib import Path
from unittest.mock import patch
from wildfire_lab.saved_hardware_search import collect
import zlib
import numpy as np
from wildfire_lab.shot_sweep_analysis import wilson, uniform_control
from wildfire_lab.selector_sector import Sector
from wildfire_lab.saved_shot_sweep import verify_uniform


class ShotSweepTests(unittest.TestCase):
    def test_published_shot_sweep_replays_without_network_or_sampling(self):
        root = Path(__file__).resolve().parents[1]
        with patch('socket.socket', side_effect=AssertionError('Network forbidden')), \
             patch('numpy.random.default_rng', side_effect=AssertionError('Sampling forbidden')):
            for device in ['quebec', 'marrakesh']:
                if (root/f'docs/results/shot-sweep-{device}.json').exists():
                    result = collect(root, f'shot-sweep-{device}')
                    self.assertEqual(result['status'], 'passed')
                    self.assertEqual(result['hardware_jobs_submitted'], 0)

    def test_interval_shrinks_without_changing_rate(self):
        low = wilson(64, 512)
        high = wilson(256, 2048)
        self.assertLess(high[1]-high[0], low[1]-low[0])
        self.assertTrue(low[0] < .125 < low[1])
        self.assertTrue(high[0] < .125 < high[1])

    def test_zero_success_is_not_zero_upper_probability(self):
        lower, upper = wilson(0, 512)
        self.assertAlmostEqual(lower, 0.)
        self.assertGreater(upper, 0.)

    def test_saved_uniform_indices_recover_observed_minima(self):
        sector = Sector(dict(linear=np.array([-1., -2., -3., -4.]),
            pair=np.zeros((4, 4)), constant=0., k=2))
        result = uniform_control(sector, 20, 10, 2701)
        indices = np.frombuffer(zlib.decompress(base64.b64decode(result['encoded_indices'])),
                                dtype='<u2').reshape(10, 20)
        minima = sector.cost[indices].min(axis=1)
        np.testing.assert_allclose(minima, result['minima'])
        expected = 1-(1-1/6)**20
        self.assertAlmostEqual(result['exact_uniform_optimum_probability'], expected)
        self.assertEqual(verify_uniform(result, sector.states, sector.cost), 200)
        result['minima'][0] += 1
        with self.assertRaises(AssertionError):
            verify_uniform(result, sector.states, sector.cost)

    def test_zero_accepted_shots_have_no_fake_sample(self):
        self.assertEqual(uniform_control(None, 0, 100, 7)['status'], 'no_accepted_draws')


if __name__ == '__main__':
    unittest.main()

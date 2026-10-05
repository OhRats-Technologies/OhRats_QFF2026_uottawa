"""The annual QUBO must use continuous relevance and enforce exact cardinality."""

import unittest
import numpy as np
from wildfire_lab.annual_selectors import objective
from wildfire_lab.selection import configurations, energies, exact_subset
from wildfire_lab.sqd_selection import sampled_subspace


class AnnualSelectorTests(unittest.TestCase):
    def test_continuous_objective_and_diagonal_sampled_subspace(self):
        rng = np.random.default_rng(9)
        x = rng.normal(size=(30, 4))
        y = 2 * x[:, 0] + .1 * rng.normal(size=30)
        plan = dict(relevance_neighbors=3, selected_count=2,
                    cardinality_penalty=2., redundancy_weight=.5)
        obj = objective(x, y, plan, 7)
        selected, exact = exact_subset(obj)
        self.assertEqual(len(selected), 2)
        self.assertIn(0, selected)
        bits = configurations(4)
        optimum = np.argmin(energies(obj, bits))
        self.assertEqual(bits[optimum].sum(), 2)
        result = sampled_subspace(obj, np.arange(16))
        self.assertAlmostEqual(result['sqd_energy'], exact)
        self.assertAlmostEqual(result['sqd_energy'], result['sampled_minimum'])


if __name__ == '__main__':
    unittest.main()

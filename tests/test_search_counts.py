"""Invalid cardinality shots remain in the noisy training objective."""
import unittest
import numpy as np
from wildfire_lab.search_counts import score


class CountTests(unittest.TestCase):
    def test_unconditional_objective_does_not_drop_invalid_counts(self):
        obj = dict(linear=np.array([-2., -2.]), pair=np.array([[0., 4.], [0., 0.]]),
                   constant=2., k=1, penalty=2.)
        result = score({'01': 10, '00': 90}, obj)
        self.assertEqual(result['feasible_shots'], 10)
        self.assertEqual(result['conditional_expected_objective'], 0.)
        self.assertEqual(result['unconditional_expected_objective'], 1.8)
        self.assertEqual(result['selected_indices'], [0])

    def test_empty_feasible_support_is_retained(self):
        obj = dict(linear=np.zeros(2), pair=np.zeros((2, 2)), constant=0., k=1)
        result = score({'00': 128}, obj)
        self.assertEqual(result['feasible_shots'], 0)
        self.assertIsNone(result['conditional_expected_objective'])
        self.assertNotIn('selected_indices', result)


if __name__ == '__main__':
    unittest.main()

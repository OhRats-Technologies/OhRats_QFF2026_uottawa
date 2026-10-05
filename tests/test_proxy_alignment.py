"""Subset coverage, reused-reference checks and refit-free collection primitives."""
import copy
import unittest
from unittest.mock import patch
import numpy as np
from wildfire_lab.proxy_alignment import fit_subsets, masks, describe, validate


class ProxyAlignmentTests(unittest.TestCase):
    def setUp(self):
        rng = np.random.default_rng(11)
        self.x = rng.normal(size=(40, 4)); self.v = rng.normal(size=(24, 4))
        self.y = (self.x[:, 0] > 0).astype(int)
        self.target = (self.v[:, 0] > 0).astype(int)
        self.objective = dict(n=4, k=2, linear=[-1, -.5, 0, .2],
            pair=np.zeros((4, 4)).tolist(), constant=0)
        self.logistic = dict(C=1., max_iter=1000)

    def fixture(self):
        rows = fit_subsets(self.x, self.y, self.v, self.target, self.objective, self.logistic)
        exact = copy.deepcopy(min(rows, key=lambda r:r['energy'])); exact['selector'] = 'exact'
        l1 = copy.deepcopy(rows[-1]); l1['selector'] = 'l1'
        return rows, dict(rows=[exact, l1])

    def test_complete_cardinality_and_integer_order(self):
        objective = dict(n=8, k=4, linear=np.zeros(8), pair=np.zeros((8, 8)), constant=0)
        states, bits, cost = masks(objective)
        self.assertEqual(len(states), 70)
        self.assertTrue(np.all(np.diff(states) > 0))
        np.testing.assert_array_equal(bits.sum(axis=1), np.full(70, 4))
        np.testing.assert_array_equal(cost, np.zeros(70))

    def test_no_refit_and_prediction_tamper(self):
        rows, parent = self.fixture()
        with patch('sklearn.linear_model.LogisticRegression.fit', side_effect=AssertionError('refit')):
            review = validate(rows, self.x, self.y, self.v, self.target,
                self.objective, self.logistic, parent)
        self.assertEqual(review, describe(rows, parent))
        broken = copy.deepcopy(rows); broken[0]['predictions'][0] += .1
        with self.assertRaises(AssertionError):
            validate(broken, self.x, self.y, self.v, self.target,
                self.objective, self.logistic, parent)
        with self.assertRaises(AssertionError):
            validate(rows[:-1], self.x, self.y, self.v, self.target,
                self.objective, self.logistic, parent)

    def test_percentile_ties_and_reference_tamper(self):
        rows, parent = self.fixture()
        for row in rows:
            row['metric']['average_precision'] = .5
        self.assertEqual(describe(rows, parent)['references']['exact']['ap_midrank_percentile'], 50)
        self.assertIsNone(describe(rows, parent)['spearman_negative_energy_ap'])
        rows, parent = self.fixture(); parent['rows'][0]['predictions'][0] += .1
        with self.assertRaises(AssertionError):
            validate(rows, self.x, self.y, self.v, self.target,
                self.objective, self.logistic, parent)


if __name__ == '__main__':
    unittest.main()

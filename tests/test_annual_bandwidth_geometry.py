import unittest
import numpy as np
from wildfire_lab.annual_bandwidth_geometry import summary


class GeometryTests(unittest.TestCase):
    def test_identity_has_full_rank_without_neighbor_similarity(self):
        row = summary(np.eye(31))
        self.assertAlmostEqual(row['effective_rank'], 31)
        self.assertEqual(row['off_diagonal_mean'], 0)
        self.assertEqual(row['relative_distance_from_identity'], 0)

    def test_constant_kernel_is_rank_one_not_well_conditioned(self):
        row = summary(np.ones((31,31)))
        self.assertAlmostEqual(row['effective_rank'], 1)
        self.assertEqual(row['off_diagonal_mean'], 1)
        self.assertIsNone(row['condition_number'])

    def test_indefinite_matrix_is_rejected(self):
        with self.assertRaises(ValueError):
            summary(np.array([[1.,2.],[2.,1.]]))

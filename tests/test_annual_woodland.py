"""Equal-area province geometry and resolution acceptance checks."""

import unittest
from wildfire_lab.annual_woodland import grid, resolution_gate


class CoverTests(unittest.TestCase):
    def test_center_mask_excludes_rectangle_outside_polygon(self):
        geometry = dict(type='Polygon', coordinates=[[[0, 0], [2000, 0], [0, 2000], [0, 0]]])
        transform, mask = grid(geometry, 1000)
        self.assertEqual(mask.shape, (2, 2))
        self.assertLess(mask.sum(), 4)
        self.assertEqual(abs(transform.a * transform.e), 1e6)

    def test_resolution_and_uncovered_gates_are_both_required(self):
        policy = dict(max_probe_fraction_difference=.01, max_uncovered_fraction=.005)
        coarse = dict(treed_fraction=.7, water_fraction=.1, uncovered_fraction=0.)
        fine = dict(treed_fraction=.699, water_fraction=.101, uncovered_fraction=0.)
        self.assertTrue(resolution_gate(coarse, fine, policy)['accepted'])
        fine['uncovered_fraction'] = .02
        self.assertFalse(resolution_gate(coarse, fine, policy)['accepted'])


if __name__ == '__main__':
    unittest.main()

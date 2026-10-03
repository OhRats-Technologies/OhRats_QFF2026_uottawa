import unittest
from fractions import Fraction as F
import numpy as np
from flybrain.channel_robustness import transition_box, power_bound, verify
from flybrain.isospectral_controls import multiply, identity


class ChannelRobustness(unittest.TestCase):
    def test_normalization_extreme_corners_are_enclosed(self):
        W = np.array([[1, 3], [4, 2]])
        scale = 100000
        L, U = transition_box(W, "1/10", "3/5", scale)
        for bits in range(16):
            noisy = [
                [
                    F(int(W[i, j]))
                    * (F(11, 10) if bits & (1 << (i * 2 + j)) else F(9, 10))
                    for j in range(2)
                ]
                for i in range(2)
            ]
            for i, row in enumerate(noisy):
                for j, x in enumerate(row):
                    value = (F(3, 5) if i == j else 0) + F(2, 5) * x / sum(row)
                    self.assertLessEqual(F(L[i][j], scale), value)
                    self.assertGreaterEqual(F(U[i][j], scale), value)

    def test_outward_rounding_of_powers(self):
        M = [[F(1, 3), F(2, 3)], [F(3, 7), F(4, 7)]]
        D = 1000
        L = [[int(x * D) for x in row] for row in M]
        U = [[int(x * D) + (x * D != int(x * D)) for x in row] for row in M]
        exact = identity(2)
        for r in range(1, 9):
            exact = multiply(exact, M)
            lo = power_bound(L, r, D)
            hi = power_bound(U, r, D, True)
            for i in range(2):
                for j in range(2):
                    self.assertLessEqual(F(lo[i][j], D), exact[i][j])
                    self.assertGreaterEqual(F(hi[i][j], D), exact[i][j])

    def test_uniform_reset_certificate_and_invalid_boxes(self):
        item = verify(np.ones((4, 4), int), "0", [1] * 4, r=4)
        self.assertEqual(item["exact_eb_index_for_entire_box"], 4)
        for e in ["-1/10", "1"]:
            with self.assertRaises(ValueError):
                transition_box(np.ones((2, 2)), e)
        with self.assertRaises(ValueError):
            transition_box(np.array([[0, 0], [1, 1]]), "0")
        with self.assertRaises(ValueError):
            power_bound([[1, -1], [1, 1]], 2)


if __name__ == "__main__":
    unittest.main()

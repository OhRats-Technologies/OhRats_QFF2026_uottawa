import unittest
from fractions import Fraction as F
import numpy as np
from flybrain.channel_parameter_boxes import joint_box, verify_joint
from flybrain.channel_robustness import transition_box, verify


class ParameterBoxes(unittest.TestCase):
    def test_gamma_endpoints_and_count_corners_enclosed(self):
        W = np.array([[1, 3], [4, 2]])
        D = 100000
        L, U = joint_box(W, "1/10", "1/2", "7/10", D)
        for gamma in [F(1, 2), F(3, 5), F(7, 10)]:
            for bits in range(16):
                weights = [
                    [
                        F(int(W[i, j]))
                        * (F(11, 10) if bits & (1 << (i * 2 + j)) else F(9, 10))
                        for j in range(2)
                    ]
                    for i in range(2)
                ]
                for i, row in enumerate(weights):
                    for j, x in enumerate(row):
                        value = (gamma if i == j else 0) + (1 - gamma) * x / sum(row)
                        self.assertLessEqual(F(L[i][j], D), value)
                        self.assertGreaterEqual(F(U[i][j], D), value)

    def test_fixed_gamma_reduces_to_count_certificate(self):
        W = np.ones((4, 4), int)
        self.assertEqual(joint_box(W, "0", "3/5", "3/5"), transition_box(W, "0"))
        fixed = verify(W, "0", [1] * 4, r=4)
        joint = verify_joint(W, "0", "3/5", "3/5", [1] * 4, r=4)
        for key in [
            "exact_eb_index_for_entire_box",
            "minimum_residual_lower_rational",
            "powered_lower_integer",
            "population_dobrushin_uniform_lower_rational",
        ]:
            self.assertEqual(fixed[key], joint[key])

    def test_invalid_gamma_intervals(self):
        for lo, hi in [("0", ".6"), (".7", ".6"), (".6", "1")]:
            with self.assertRaises(ValueError):
                joint_box(np.ones((2, 2)), 0, lo, hi)
        with self.assertRaises(ValueError):
            verify_joint(np.ones((2, 2)), 0, ".5", ".6", [0, 1])


if __name__ == "__main__":
    unittest.main()

import unittest
from fractions import Fraction as F
import numpy as np
from flybrain.isospectral_controls import (
    reflection,
    identity,
    multiply,
    transpose,
    seed_chain,
    integer_weights,
    run,
)


class IsospectralControls(unittest.TestCase):
    def test_exact_similarity_and_stochasticity(self):
        P, eigenvalues = seed_chain(4)
        O = reflection([1, -1, 2, -2])
        self.assertEqual(multiply(transpose(O), O), identity(4))
        self.assertTrue(all(sum(row) == 1 for row in O))
        Q = multiply(multiply(O, P), transpose(O))
        self.assertEqual(Q, transpose(Q))
        np.testing.assert_allclose(
            np.linalg.eigvalsh(np.array(Q, float)),
            sorted(map(float, eigenvalues)),
            atol=1e-13,
        )

    def test_integer_weights_reproduce_rational_rows(self):
        P, _ = seed_chain(8)
        W = integer_weights(P)
        for row, weights in zip(P, W):
            self.assertEqual(row, [F(int(x), int(weights.sum())) for x in weights])
        with self.assertRaises(ValueError):
            integer_weights([[F(1), F(-1)], [F(0), F(1)]])

    def test_invalid_vectors_and_sample_count(self):
        for v in [[0, 0], [1, 2]]:
            with self.assertRaises(ValueError):
                reflection(v)
        with self.assertRaises(ValueError):
            run(0)


if __name__ == "__main__":
    unittest.main()

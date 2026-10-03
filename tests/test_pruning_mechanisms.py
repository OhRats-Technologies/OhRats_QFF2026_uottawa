import unittest
from fractions import Fraction

import numpy as np

from flybrain.channel_certificates import exact_certificate
from flybrain.data import load_graph
from flybrain.pruning_mechanisms import certify, interventions, simulate


class PruningMechanismTests(unittest.TestCase):
    def test_interventions_exhaustive_and_mass_control(self):
        nodes, W, _ = load_graph()
        cases = list(interventions(W, nodes))
        self.assertEqual(len(cases), 42)
        self.assertEqual(len({name for name, _, _ in cases}), 42)
        single = [
            x
            for x in cases
            if x[2].get("kind") == "row_restoration" and len(x[2]["rows"]) == 1
        ]
        double = [
            x
            for x in cases
            if x[2].get("kind") == "row_restoration" and len(x[2]["rows"]) == 2
        ]
        self.assertEqual(len(single), 8)
        self.assertEqual(len(double), 28)
        held = cases[2][1]
        np.testing.assert_array_equal(held.sum(1), W.sum(1))
        for _, weights, intervention in single + double:
            rows = intervention["rows"]
            np.testing.assert_array_equal(weights[rows], W[rows])
            other = [i for i in range(8) if i not in rows]
            np.testing.assert_array_equal(weights[other], cases[1][1][other])
        np.testing.assert_array_equal(W, load_graph()[1])

    def test_empty_rows_rejected(self):
        with self.assertRaises(ValueError):
            list(interventions(np.eye(8), list(map(str, range(8)))))

    def test_exact_classical_rescue_does_not_rescue_eb(self):
        nodes, W, _ = load_graph()
        selected = {name: weights for name, weights, _ in interventions(W, nodes)}
        results = {
            name: certify(selected[name], nodes)
            for name in ["intact", "pruned", "rows:T4a_R", "rows:Y3_R+T4a_R"]
        }
        self.assertEqual([results[x]["exact_eb_index"] for x in results], [7, 8, 8, 7])
        self.assertLess(
            abs(
                results["rows:T4a_R"]["subdominant_modulus"]
                - results["intact"]["subdominant_modulus"]
            ),
            0.0002,
        )
        for result in results.values():
            cert = result["certificate"]
            self.assertGreaterEqual(Fraction(cert["minimum_residual_rational"]), 0)
            self.assertLess(
                Fraction(
                    cert["previous_step_npt_witness"]["unscaled_pt_block_determinant"]
                ),
                0,
            )
            reloaded = exact_certificate(
                np.array(cert["adjacency_integer"]),
                cert["gamma_rational"],
                cert["r"],
                cert["v_rational"],
            )
            self.assertEqual(reloaded, cert)

    def test_qiskit_kraus_register_order(self):
        _nodes, W, _ = load_graph()
        P = W / W.sum(1, keepdims=True)
        result = simulate(P, 1)
        self.assertLess(result["max_choi_error"], 1e-12)
        self.assertAlmostEqual(result["trace_real"], 1)
        self.assertLess(result["partial_transpose_minimum"], 0)


if __name__ == "__main__":
    unittest.main()

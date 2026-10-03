import unittest
import numpy as np
from qiskit.quantum_info import Choi
from flybrain.quantum_channel import ConnectomeQuantumChannel, partial_transpose_b
from flybrain.channel_certificates import (
    analytic_choi,
    ppt_min_eigenvalue,
    product_certificate,
    reconstruct,
    profile,
    phase_certificate,
    exact_certificate,
)


class Certificates(unittest.TestCase):
    def test_true_composition_and_blocks(self):
        rng = np.random.default_rng(531)
        for n in [2, 4, 8]:
            P = rng.random((n, n))
            P /= P.sum(1, keepdims=True)
            for gamma in [0, 0.3, 0.6, 1]:
                channel = ConnectomeQuantumChannel(P, gamma=gamma)
                for r in [1, 2, 7]:
                    J, B, c = analytic_choi(P, gamma, r)
                    np.testing.assert_allclose(
                        J, Choi(channel.power_superop(r)).data / n, atol=1e-12
                    )
                    self.assertAlmostEqual(
                        ppt_min_eigenvalue(B, c),
                        np.linalg.eigvalsh(partial_transpose_b(J, n, n)).min(),
                        places=11,
                    )

    def test_product_mixture_reconstructs(self):
        P = np.full((8, 8), 1 / 8)
        J, B, c = analytic_choi(P, 0.6, 8)
        cert = product_certificate(B, c)
        self.assertIsNotNone(cert)
        self.assertGreaterEqual(cert["residual"].min(), 0)
        np.testing.assert_allclose(reconstruct(cert), J, atol=1e-12)
        self.assertAlmostEqual(np.trace(reconstruct(cert)).real, 1)
        for a, b, w in cert["terms"]:
            self.assertGreater(w, 0)

    def test_phase_twirl_and_uniform_reset_threshold(self):
        # Uniform reset is isotropic: first PPT/EB has gamma^r < 1/(n+1).
        for n in [2, 4, 8]:
            P = np.full((n, n), 1 / n)
            gamma = 0.6
            r = next(r for r in range(1, 20) if gamma**r < 1 / (n + 1))
            J, B, c = analytic_choi(P, gamma, r)
            cert = phase_certificate(B, c)
            self.assertIsNotNone(cert)
            np.testing.assert_allclose(reconstruct(cert), J, atol=1e-12)
            _, Bprev, cprev = analytic_choi(P, gamma, r - 1)
            self.assertLess(ppt_min_eigenvalue(Bprev, cprev), 0)
            self.assertIsNone(phase_certificate(Bprev, cprev))

    def test_directional_phase_certificate(self):
        rng = np.random.default_rng(778)
        for n in [2, 4]:
            P = rng.random((n, n))
            P /= P.sum(1, keepdims=True)
            J, B, c = analytic_choi(P, 0.6, 12)
            cert = phase_certificate(B, c)
            self.assertIsNotNone(cert)
            np.testing.assert_allclose(reconstruct(cert), J, atol=1e-12)

    def test_exact_certificate_and_reject_invalid_residue(self):
        proof = exact_certificate(np.ones((4, 4), int), "0.6", 4, [1] * 4)
        self.assertEqual(proof["exact_eb_index"], 4)
        self.assertIsNotNone(proof["previous_step_npt_witness"])
        with self.assertRaises(ValueError):
            exact_certificate(np.ones((4, 4), int), "0.6", 3, [1] * 4)
        with self.assertRaises(ValueError):
            exact_certificate(np.ones((4, 4), int), "0.6", 4, [100, 1, 1, 1])
        with self.assertRaises(ValueError):
            exact_certificate(np.full((4, 4), 0.5), "0.6", 4, [1] * 4)

    def test_limits(self):
        P = np.eye(4)
        self.assertIsNone(profile(P, 0.6, 20)["constructive_eb_upper_bound"])
        self.assertEqual(profile(P, 0, 2)["constructive_eb_upper_bound"], 1)
        self.assertEqual(
            profile(np.full((4, 4), 0.25), 1, 8)["npt_based_eb_lower_bound"], 9
        )

    def test_invalid_transition(self):
        with self.assertRaises(ValueError):
            analytic_choi(np.array([[1, -0.1], [0, 1]]), 0.6, 1)
        with self.assertRaises(ValueError):
            analytic_choi(np.eye(2), 0.6, 0)


if __name__ == "__main__":
    unittest.main()

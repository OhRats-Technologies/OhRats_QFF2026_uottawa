import itertools
import json
import unittest
from pathlib import Path

import numpy as np
from qiskit.quantum_info import Statevector

from scripts.q_sigreg_audit import (
    density_features,
    feature_map,
    quantum_kernel,
    rbf,
    states,
)


class QSigregAuditTests(unittest.TestCase):
    def test_feature_states_fidelity_and_cancelled_terminal_gate(self):
        x = np.random.default_rng(7).normal(size=(8, 4))
        psi = states(x)
        exact = np.array(
            [
                Statevector.from_instruction(feature_map(np.pi / 2 * np.tanh(row))).data
                for row in x
            ]
        )
        np.testing.assert_allclose(psi, exact, atol=1e-13)
        K = quantum_kernel(x, x)
        self.assertGreater(np.linalg.eigvalsh(K).min(), -1e-12)
        np.testing.assert_allclose(np.diag(K), 1, atol=1e-13)
        plain = states(x, final_cz=False)
        np.testing.assert_allclose(K, np.abs(plain @ plain.conj().T) ** 2, atol=1e-13)
        pair = feature_map(np.pi / 2 * np.tanh(x[0])).compose(
            feature_map(np.pi / 2 * np.tanh(x[1])).inverse()
        )
        self.assertAlmostEqual(
            K[0, 1], abs(Statevector.from_instruction(pair).data[0]) ** 2
        )

    def test_density_mean_identity(self):
        x = np.random.default_rng(8).normal(size=(9, 4))
        y = np.random.default_rng(9).normal(size=(11, 4))
        a, b = states(x), states(y)
        rho_a = a.T @ a.conj() / len(a)
        rho_b = b.T @ b.conj() / len(b)
        expected = np.square(np.abs(rho_a - rho_b)).sum()
        observed = (
            quantum_kernel(x, x).mean()
            + quantum_kernel(y, y).mean()
            - 2 * quantum_kernel(x, y).mean()
        )
        self.assertAlmostEqual(expected, observed)
        self.assertEqual(density_features(a).shape, (9, 256))

    def test_paired_estimator_expectation(self):
        x = np.array([[0.0, 0.0, 0.0, 0.0], [1.0, -1.0, 0.2, 0.5]])
        y = np.array([[0.2, 0.0, 0.1, 0.0], [-0.4, 0.5, 0.2, -0.1]])
        a, b, c = quantum_kernel(x, x), quantum_kernel(y, y), quantum_kernel(x, y)
        terms = [
            a[i, j] + b[g, h] - c[i, h] - c[j, g]
            for i, j, g, h in itertools.product(range(2), repeat=4)
        ]
        self.assertAlmostEqual(np.mean(terms), a.mean() + b.mean() - 2 * c.mean())

    def test_saved_collision_has_nonnegative_weights_and_same_features(self):
        path = Path("artifacts/q-sigreg-audit-20261003/results.json")
        data = json.loads(path.read_text())["finite_feature_collision"]
        x = np.array(data["points"])
        original, other = (
            np.array(data["baseline_weights"]),
            np.array(data["alternative_weights"]),
        )
        self.assertGreaterEqual(other.min(), 0)
        self.assertAlmostEqual(other.sum(), 1)
        delta = other - original
        self.assertGreater(np.abs(delta).sum() / 2, 0.5)
        np.testing.assert_allclose(delta @ density_features(states(x)), 0, atol=1e-10)
        np.testing.assert_allclose(delta @ x, 0, atol=1e-10)
        np.testing.assert_allclose(np.einsum("n,ni,nj->ij", delta, x, x), 0, atol=1e-10)
        self.assertGreater(delta @ rbf(x, x) @ delta, 1e-6)


if __name__ == "__main__":
    unittest.main()

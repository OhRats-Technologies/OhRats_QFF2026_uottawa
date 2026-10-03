import unittest

import numpy as np
import torch
from qiskit.quantum_info import Statevector

from q_sigreg.kernel import (
    bounded_angles,
    build_sampler_qnn,
    exact_states,
    feature_map_circuit,
    pair_kernel,
)
from q_sigreg.mmd import (
    energy_distance,
    full_mmd2,
    linear_mmd2_from_kernel,
    moment_penalty,
    quantum_kernel_fn,
    rbf_kernel_fn,
)
from qiskit.circuit import ParameterVector


class KernelTests(unittest.TestCase):
    def setUp(self):
        torch.manual_seed(0)

    def test_matches_qiskit_statevector_overlap(self):
        theta = torch.rand(5, 4, dtype=torch.float64) * 3 - 1.5
        states = exact_states(theta)
        params = ParameterVector("t", 4)
        for i in range(5):
            qc = feature_map_circuit(params).assign_parameters(dict(zip(params, theta[i].tolist())))
            ref = Statevector(qc).data.reshape(2, 2, 2, 2).transpose(3, 2, 1, 0).reshape(16)
            overlap = abs(np.vdot(ref, states[i].numpy()))
            self.assertAlmostEqual(overlap, 1.0, places=10)

    def test_kernel_properties(self):
        a = exact_states(torch.rand(6, 4, dtype=torch.float64) * 3 - 1.5)
        b = exact_states(torch.rand(6, 4, dtype=torch.float64) * 3 - 1.5)
        k = pair_kernel(a, b)
        self.assertTrue(torch.all(k >= 0) and torch.all(k <= 1 + 1e-12))
        torch.testing.assert_close(k, pair_kernel(b, a))
        torch.testing.assert_close(pair_kernel(a, a), torch.ones(6, dtype=torch.float64))

    def test_sampler_qnn_value_and_input_gradient(self):
        from qiskit_machine_learning.connectors import TorchConnector

        qnn = TorchConnector(build_sampler_qnn(shots=2**16))
        xy = (torch.rand(2, 8, dtype=torch.float64) * 3 - 1.5).requires_grad_(True)
        k_qnn = qnn(xy)[:, 0].double()
        k_ref_in = xy.detach().clone().requires_grad_(True)
        k_ref = pair_kernel(exact_states(k_ref_in[:, :4]), exact_states(k_ref_in[:, 4:]))
        torch.testing.assert_close(k_qnn, k_ref, atol=1e-2, rtol=0)
        k_qnn.sum().backward()
        k_ref.sum().backward()
        torch.testing.assert_close(xy.grad.double(), k_ref_in.grad, atol=1e-2, rtol=0)


class MMDTests(unittest.TestCase):
    def setUp(self):
        torch.manual_seed(1)

    def test_full_and_linear_estimators_unbiased_under_null(self):
        fn = quantum_kernel_fn()
        full, lin = [], []
        for _ in range(60):
            z = torch.randn(8, 4, dtype=torch.float64)
            g = torch.randn(8, 4, dtype=torch.float64)
            full.append(full_mmd2(fn, z, g).item())
            lin.append(linear_mmd2_from_kernel(fn, z, g).item())
        for values in (full, lin):
            sem = np.std(values) / np.sqrt(len(values))
            self.assertLess(abs(np.mean(values)), 4 * sem + 1e-3)

    def test_detects_scale_and_shift(self):
        fn = quantum_kernel_fn()
        g = torch.randn(256, 4, dtype=torch.float64)
        same = full_mmd2(fn, torch.randn(256, 4, dtype=torch.float64), g).item()
        collapsed = full_mmd2(fn, 0.05 * torch.randn(256, 4, dtype=torch.float64), g).item()
        shifted = full_mmd2(fn, torch.randn(256, 4, dtype=torch.float64) + 2.0, g).item()
        self.assertGreater(collapsed, same + 1e-3)
        self.assertGreater(shifted, same + 1e-3)

    def test_linear_matches_bruteforce_pairs(self):
        fn = rbf_kernel_fn(1.5)
        z = torch.randn(8, 4, dtype=torch.float64)
        g = torch.randn(8, 4, dtype=torch.float64)
        manual = np.mean(
            [
                fn(z[2 * i : 2 * i + 1], z[2 * i + 1 : 2 * i + 2]).item()
                + fn(g[2 * i : 2 * i + 1], g[2 * i + 1 : 2 * i + 2]).item()
                - fn(z[2 * i : 2 * i + 1], g[2 * i + 1 : 2 * i + 2]).item()
                - fn(z[2 * i + 1 : 2 * i + 2], g[2 * i : 2 * i + 1]).item()
                for i in range(4)
            ]
        )
        self.assertAlmostEqual(linear_mmd2_from_kernel(fn, z, g).item(), manual, places=12)

    def test_odd_batch_rejected(self):
        with self.assertRaises(ValueError):
            linear_mmd2_from_kernel(rbf_kernel_fn(1.0), torch.zeros(3, 4), torch.zeros(3, 4))

    def test_moment_penalty_and_energy(self):
        z = torch.randn(20000, 4, dtype=torch.float64)
        self.assertLess(moment_penalty(z).item(), 0.05)
        self.assertGreater(moment_penalty(z * 2 + 1).item(), 5.0)
        self.assertLess(energy_distance(z[:500], torch.randn(500, 4, dtype=torch.float64)).item(), 0.1)

    def test_gradient_reaches_embeddings(self):
        z = torch.randn(8, 4, dtype=torch.float64, requires_grad=True)
        g = torch.randn(8, 4, dtype=torch.float64)
        loss = linear_mmd2_from_kernel(quantum_kernel_fn(), z, g)
        loss.backward()
        self.assertTrue(torch.isfinite(z.grad).all() and z.grad.abs().sum() > 0)


if __name__ == "__main__":
    unittest.main()

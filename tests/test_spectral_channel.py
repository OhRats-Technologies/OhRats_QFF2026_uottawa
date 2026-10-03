"""Unit tests for connectome spectral dynamics and quantum channel formulation."""

import unittest
import numpy as np
from flybrain.spectral import (
    SynapseFlowChain,
    dobrushin_coefficient,
    certified_mixing_bounds,
    pruning_sweep,
    signed_influence_map,
    uncertainty_lemma1,
    uncertainty_lemma2,
    uncertainty_lemma3_knapsack,
)
from flybrain.quantum_channel import (
    ConnectomeQuantumChannel,
    choi_density_matrix,
    compute_ppt_negativity,
    construct_entanglement_witness,
    run_witness_aer,
    compare_classical_and_quantum_mixing,
    bipartite_conjugate_witness,
)


class ConnectomeSpectralAndChannelTests(unittest.TestCase):
    def setUp(self):
        # 4-node directed test graph with one weakly-connected boundary node (Node 3)
        self.adj_4node = np.array([
            [50.0, 50.0, 50.0, 100.0],
            [50.0, 50.0, 50.0, 100.0],
            [50.0, 50.0, 50.0, 100.0],
            [10.0, 5.0, 5.0, 80.0],
        ])
        self.names_4node = ["N0", "N1", "N2", "N3_boundary"]

        # Simple 2-node symmetric graph for exact analytic verification
        self.adj_2node = np.array([
            [10.0, 90.0],
            [90.0, 10.0],
        ])

    def test_row_stochastic_and_stationary_distribution(self):
        chain = SynapseFlowChain(self.adj_4node, node_names=self.names_4node)
        # Check row sums equal 1
        np.testing.assert_allclose(chain.P.sum(axis=1), np.ones(4), atol=1e-12)
        # Check stationary equation pi * P = pi
        np.testing.assert_allclose(chain.pi @ chain.P, chain.pi, atol=1e-10)
        self.assertAlmostEqual(float(chain.pi.sum()), 1.0, places=10)
        # Spectral gap must be positive for a strongly connected aperiodic chain
        self.assertGreater(chain.spectral_gap, 0.0)
        self.assertLessEqual(float(np.abs(chain.lambda2)), 1.0)

    def test_dobrushin_analytic_two_node(self):
        chain = SynapseFlowChain(self.adj_2node)
        # For 2-node chain with P = [[0.1, 0.9], [0.9, 0.1]]:
        # P[0] - P[1] = [-0.8, 0.8], TV = 0.5 * (0.8 + 0.8) = 0.8
        tau1 = dobrushin_coefficient(chain.P, r=1)
        self.assertAlmostEqual(tau1, 0.8, places=8)
        # At r steps, (P[0] - P[1]) P^r scales as (lambda2)^r = (-0.8)^r
        tau2 = dobrushin_coefficient(chain.P, r=2)
        self.assertAlmostEqual(tau2, 0.8**2, places=8)

    def test_certified_mixing_bounds_sandwich(self):
        chain = SynapseFlowChain(self.adj_4node)
        steps = [1, 2, 3, 4]
        bounds = certified_mixing_bounds(chain.P, steps, slack_scale=1e-9)

        for i, r in enumerate(steps):
            lower = bounds["lower_bound"][i]
            upper = bounds["upper_bound"][i]
            exact = bounds["exact"][i]
            # Certified lower bound <= exact <= certified upper bound
            self.assertLessEqual(lower, exact + 1e-8)
            self.assertGreaterEqual(upper, exact - 1e-8)

    def test_pruning_boundary_trap(self):
        # Pruning weak connections (>= 8) removes Node 3's outward links to N1, N2 while retaining N0
        thresholds = [0.0, 8.0]
        results = pruning_sweep(self.adj_4node, thresholds, self.names_4node)

        res_unpruned = results[0]
        res_pruned = results[1]

        # Pruning should increase |lambda_2| (slower mixing) and lower escape probability
        self.assertGreaterEqual(res_pruned["lambda2_modulus"], res_unpruned["lambda2_modulus"])
        self.assertLessEqual(res_pruned["escape_probability"], res_unpruned["escape_probability"])

    def test_signed_influence_map_median_floor(self):
        # 4-node graph where N3 receives very few inputs
        signs = [+1, -1, +1, -1]
        evals_raw, _, pr_raw = signed_influence_map(self.adj_4node, signs, floor=None)
        evals_floor, _, pr_floor = signed_influence_map(self.adj_4node, signs, floor=50.0)

        # Leading participation ratio should be higher or spectral radius regularized
        self.assertGreater(pr_floor[0], 0.0)
        self.assertGreater(pr_raw[0], 0.0)

    def test_uncertainty_lemmas(self):
        # High confidence weights w_hi <= w
        w = self.adj_4node
        w_hi = w * 0.9  # 10% below confidence
        eps = uncertainty_lemma1(w, w_hi)
        np.testing.assert_allclose(eps, np.full(4, 0.1), atol=1e-8)

        # Lemma 2 accumulated slack
        P = w / w.sum(axis=1)[:, np.newaxis]
        slack = uncertainty_lemma2(P, a=0, b=1, r=2, eps=eps)
        self.assertGreater(slack, 0.0)

        # Lemma 3 knapsack bound
        eps_star = uncertainty_lemma3_knapsack(w[0], w_hi[0])
        self.assertLessEqual(eps_star, eps[0] + 1e-6)

    def test_channel_cptp_and_trace_preservation(self):
        chain = SynapseFlowChain(self.adj_4node)
        channel = ConnectomeQuantumChannel(chain.P, gamma=0.5)

        # Kraus operators must satisfy sum_k E_k^dagger E_k = I
        identity = sum(E.conj().T @ E for E in channel.kraus_operators)
        np.testing.assert_allclose(identity, np.eye(4), atol=1e-6)

        # Trace preservation on random density matrix
        psi = np.random.randn(4) + 1j * np.random.randn(4)
        psi /= np.linalg.norm(psi)
        rho = np.outer(psi, psi.conj())
        rho_out = channel.apply_density_matrix(rho)
        self.assertAlmostEqual(float(np.real(np.trace(rho_out))), 1.0, places=8)

    def test_choi_ppt_negativity_and_entanglement_breaking(self):
        chain = SynapseFlowChain(self.adj_4node)
        # With gamma = 0, channel dephases completely -> n_EB = 1
        ch_dephase = ConnectomeQuantumChannel(chain.P, gamma=0.0)
        choi_dephase = choi_density_matrix(ch_dephase)
        neg_dephase, _, min_eig = compute_ppt_negativity(choi_dephase, 4)
        self.assertAlmostEqual(neg_dephase, 0.0, places=6)
        self.assertGreaterEqual(min_eig, -1e-8)

        # With gamma > 0, initial Choi state is entangled
        ch_coherent = ConnectomeQuantumChannel(chain.P, gamma=0.8)
        choi_coh = choi_density_matrix(ch_coherent)
        neg_coh, log_neg, min_eig_coh = compute_ppt_negativity(choi_coh, 4)
        self.assertGreater(neg_coh, 0.0)
        self.assertLess(min_eig_coh, -1e-6)

    def test_entanglement_witness_aer(self):
        chain = SynapseFlowChain(self.adj_4node)
        channel = ConnectomeQuantumChannel(chain.P, gamma=0.8)
        choi = choi_density_matrix(channel)
        witness, min_val = construct_entanglement_witness(choi, 4)

        # Tr(W * J) must match min eigenvalue < 0
        res = run_witness_aer(choi, witness, num_qubits=2, shots=4096)
        self.assertLess(res["exact_witness_expectation"], 0.0)
        self.assertAlmostEqual(res["exact_witness_expectation"], min_val, places=6)
        self.assertTrue(res["is_entangled"])

    def test_dual_comparison_profile(self):
        chain = SynapseFlowChain(self.adj_4node)
        profile = compare_classical_and_quantum_mixing(chain.P, gamma=0.5, max_steps=6)
        self.assertEqual(len(profile.steps), 6)
        self.assertEqual(len(profile.classical_dobrushin), 6)
        self.assertEqual(len(profile.choi_negativity), 6)
        # Negativity should decrease with steps
        self.assertGreaterEqual(profile.choi_negativity[0], profile.choi_negativity[-1])

    def test_true_composition_counterexample(self):
        from qiskit.quantum_info import DensityMatrix
        # Two-node counterexample from audit: P = [[0.1, 0.9], [0.9, 0.1]], gamma = 0.6
        P = np.array([[0.1, 0.9], [0.9, 0.1]])
        ch = ConnectomeQuantumChannel(P, gamma=0.6)
        rho0 = DensityMatrix([[1.0, 0], [0, 0]])

        # True composition at r=2 gives [0.5392, 0.4608]
        sop2 = ch.power_superop(2)
        rho2 = rho0.evolve(sop2).data
        np.testing.assert_allclose(np.diag(rho2).real, [0.5392, 0.4608], atol=1e-8)

    def test_bipartite_conjugate_witness(self):
        # Simulated counts for an entangled Bell state (measuring in Z and X)
        counts_z = {"00": 512, "11": 512}
        counts_x = {"00": 512, "11": 512}
        res = bipartite_conjugate_witness(counts_z, counts_x, [(0, 1)])
        self.assertEqual(len(res), 1)
        self.assertAlmostEqual(res[0]["witness_sum"], 2.0, places=6)
        self.assertTrue(res[0]["certified_entangled"])


if __name__ == "__main__":
    unittest.main()

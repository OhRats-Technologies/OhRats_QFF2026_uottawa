"""Offline scientific invariants and snapshot/parser regression checks."""

import shutil
import tempfile
import unittest
from pathlib import Path
import numpy as np
from flybrain.data import DEFAULT_DATA, load_graph, parse_connections
from flybrain.walks import laplacian, sampled_walk, trajectories, undirected


class DataTests(unittest.TestCase):
    def test_optional_html_tags_and_exact_counts(self):
        html = (
            "<table id=upstream-table><tr><td>ignore</table>"
            "<table id=downstream-table><tr><th>Partner"
            "<tr><td><a href=Mi1_R.html#s-c>Mi1</a>"
            '<td title="∑ connections: 1,234"><span>1.2</span>'
            "<tr><td><a href=Tm3_R.html#s-c>Tm3</a>"
            '<td title="∑ connections: 7"><span>0.0</span></table>'
        )
        self.assertEqual(
            parse_connections(html),
            [{"target": "Mi1_R", "synapses": 1234}, {"target": "Tm3_R", "synapses": 7}],
        )

    def test_missing_table_and_missing_count_fail(self):
        for html in [
            "<table></table>",
            "<table id=downstream-table><tr><td><a href=Mi1_R.html#s-c>Mi1</a></table>",
        ]:
            with self.assertRaises(ValueError):
                parse_connections(html)

    def test_real_snapshot_and_tamper_detection(self):
        nodes, adjacency, manifest = load_graph()
        self.assertEqual(nodes[0], "Mi1_R")
        self.assertEqual(len(nodes), 8)
        self.assertEqual(adjacency[0, nodes.index("Pm2a_R")], 132532)
        self.assertEqual(manifest["dataset"], "male-cns:v1.0")
        with tempfile.TemporaryDirectory() as temp:
            copied = Path(temp) / "snapshot"
            shutil.copytree(DEFAULT_DATA, copied)
            with (copied / "edges.csv").open("a") as stream:
                stream.write("Mi1_R,Pm2a_R,1\n")
            with self.assertRaisesRegex(ValueError, "checksum"):
                load_graph(copied)


class WalkTests(unittest.TestCase):
    def test_two_node_analytic_solution(self):
        # Independent closed forms: quantum sin²(t), classical (1-exp(-2t))/2.
        generator = laplacian(np.array([[0.0, 1.0], [1.0, 0.0]]))
        times = np.array([0.0, 0.2, np.pi / 2, np.pi])
        classical, quantum = trajectories(generator, 0, times)
        np.testing.assert_allclose(
            classical[:, 1], (1 - np.exp(-2 * times)) / 2, atol=1e-12
        )
        np.testing.assert_allclose(quantum[:, 1], np.sin(times) ** 2, atol=1e-12)

    def test_direction_symmetrization_and_self_loops(self):
        np.testing.assert_array_equal(undirected([[9, 6], [2, 4]]), [[0, 4], [4, 0]])

    def test_disconnected_node_cannot_receive_probability(self):
        weights = np.ones((4, 4)) - np.eye(4)
        original_scale = weights.sum(axis=1).max()
        weights[2, :] = weights[:, 2] = 0
        generator = laplacian(weights, original_scale)
        for probabilities in trajectories(generator, 0, [0.0, 1.0, 3.0]):
            np.testing.assert_allclose(probabilities[:, 2], 0, atol=1e-12)
            np.testing.assert_allclose(probabilities.sum(axis=1), 1, atol=1e-12)
        self.assertAlmostEqual(generator[0, 0], 2 / 3)

    def test_basis_order_and_deterministic_sampling(self):
        generator = laplacian(np.ones((4, 4)) - np.eye(4))
        sampled, _ = sampled_walk(generator, 2, 0.0, shots=128)
        np.testing.assert_array_equal(sampled, [0, 0, 1, 0])

    def test_invalid_graphs_fail(self):
        for adjacency in [[[0, -1], [1, 0]], [[0, np.nan], [1, 0]], [[0, 1, 2]]]:
            with self.assertRaises(ValueError):
                undirected(adjacency)


class MagneticTests(unittest.TestCase):
    def test_zero_charge_and_reversal(self):
        from flybrain.flux import magnetic_laplacian, quantum_probabilities

        adjacency = np.array(
            [[0, 3, 1, 0], [1, 0, 2, 0], [2, 1, 0, 0], [0, 0, 0, 0]], dtype=float
        )
        zero, _ = magnetic_laplacian(adjacency, 0.0)
        np.testing.assert_allclose(zero, laplacian(undirected(adjacency)))
        forward, _ = magnetic_laplacian(adjacency, 1.0)
        reverse, _ = magnetic_laplacian(adjacency.T, 1.0)
        np.testing.assert_allclose(reverse, forward.conj())
        p = quantum_probabilities(forward, [0, 1, 2])
        np.testing.assert_allclose(
            quantum_probabilities(reverse, [0, 1, 2]), p.transpose(0, 2, 1), atol=1e-12
        )

    def test_gauge_invariance_and_two_node_limit(self):
        from flybrain.flux import magnetic_laplacian, quantum_probabilities

        adjacency = np.array([[0, 3], [1, 0]], dtype=float)
        baseline, _ = magnetic_laplacian(adjacency, 0.0)
        phased, _ = magnetic_laplacian(adjacency, 1.0)
        np.testing.assert_allclose(
            quantum_probabilities(baseline, [0, 0.3, 1]),
            quantum_probabilities(phased, [0, 0.3, 1]),
            atol=1e-12,
        )
        triangle = np.array(
            [[0, 1, 0, 0], [0, 0, 1, 0], [1, 0, 0, 0], [0, 0, 0, 0]], dtype=float
        )
        generator, _ = magnetic_laplacian(triangle, 1.0)
        gauge = np.diag(np.exp(1j * np.array([0.3, 1.2, -0.7, 2.0])))
        np.testing.assert_allclose(
            quantum_probabilities(generator, [0.5, 1, 2]),
            quantum_probabilities(gauge @ generator @ gauge.conj().T, [0.5, 1, 2]),
            atol=1e-12,
        )
        p = quantum_probabilities(generator, [1])[0]
        self.assertGreater(abs(p[1, 0] - p[2, 0]), 0.01)


class StrengthControlTests(unittest.TestCase):
    def test_balanced_moves_preserve_weighted_strength_and_generator_diagonal(self):
        from flybrain.strengthnull import four_edge_move, move_span_rank
        from flybrain.walks import laplacian

        weights = np.zeros((4, 4), dtype=float)
        upper = np.triu_indices(4, 1)
        weights[upper] = np.arange(1, 7)
        weights += weights.T
        original = weights.copy()
        strength = weights.sum(axis=1)
        rng = np.random.default_rng(24)
        for _ in range(1000):
            four_edge_move(weights, rng)
        np.testing.assert_allclose(weights.sum(axis=1), strength, atol=1e-10)
        np.testing.assert_allclose(weights, weights.T, atol=1e-12)
        np.testing.assert_allclose(
            np.diag(laplacian(weights, strength.max())),
            np.diag(laplacian(original, strength.max())),
            atol=1e-12,
        )
        self.assertGreater(np.min(weights[upper]), 0)
        self.assertGreater(np.linalg.norm(weights - original), 0.1)
        self.assertEqual(move_span_rank(4), 2)
        self.assertEqual(move_span_rank(8), 20)


if __name__ == "__main__":
    unittest.main()

import unittest
import numpy as np
from qiskit.quantum_info import SparsePauliOp, Statevector
from sqd_lab.sampling import pair_circuit, sample_circuit, valid_mask, uniform_basis
from sqd_lab.subspace import selected_energy
from sqd_lab.chemistry import hydrogen_chain


class SQDTests(unittest.TestCase):
    def test_ansatz_conserves_both_spin_particle_numbers(self):
        for norb in (2, 4):
            probabilities = Statevector.from_instruction(
                pair_circuit(norb)
            ).probabilities_dict()
            rows = np.array(
                [[b == "1" for b in s] for s, p in probabilities.items() if p > 1e-12]
            )
            self.assertTrue(valid_mask(rows, (norb // 2, norb // 2)).all())

    def test_projection_endianness_complex_offdiagonal_and_duplicates(self):
        h = SparsePauliOp.from_list([("ZI", 0.7), ("IY", 0.4), ("XX", 0.2)])
        rows = np.array([[0, 1], [1, 0], [0, 1], [1, 1]], dtype=bool)
        result = selected_energy(rows, h)
        expected = np.linalg.eigvalsh(h.to_matrix()[np.ix_([1, 2, 3], [1, 2, 3])])[0]
        self.assertAlmostEqual(result["energy"], expected, places=10)
        self.assertEqual(result["dimension"], 3)

    def test_no_shots_and_empty_postselection_are_explicit(self):
        with self.assertRaises(ValueError):
            sample_circuit(pair_circuit(2), 0, 1)
        self.assertEqual(
            selected_energy(np.zeros((0, 4), bool), SparsePauliOp("IIII"))["dimension"],
            0,
        )

    def test_molecular_sector_matches_independent_fci(self):
        molecule = hydrogen_chain()
        basis = uniform_basis(2, (1, 1), 4, 3)
        result = selected_energy(basis, molecule.hamiltonian, molecule.offset)
        self.assertAlmostEqual(result["energy"], molecule.exact_energy, places=9)
        hf = np.array([[0, 1, 0, 1]], dtype=bool)
        self.assertAlmostEqual(
            selected_energy(hf, molecule.hamiltonian, molecule.offset)["energy"],
            molecule.hf_energy,
            places=9,
        )

    def test_greedy_classical_control_is_nested_variational_and_physical(self):
        from sqd_lab.classical import greedy_basis

        molecule = hydrogen_chain()
        rows, history = greedy_basis(molecule, 4)
        self.assertTrue(valid_mask(rows, molecule.nelec).all())
        self.assertEqual(len(np.unique(rows, axis=0)), 4)
        self.assertAlmostEqual(history[0]["energy"], molecule.hf_energy, places=9)
        self.assertAlmostEqual(history[-1]["energy"], molecule.exact_energy, places=9)
        self.assertTrue(
            all(
                b["energy"] <= a["energy"] + 1e-10 for a, b in zip(history, history[1:])
            )
        )
        with self.assertRaises(ValueError):
            greedy_basis(molecule, 5)

    def test_nested_counts_are_reproducible(self):
        a = sample_circuit(pair_circuit(2), 100, 7, 0.08)
        b = sample_circuit(pair_circuit(2), 100, 7, 0.08)
        np.testing.assert_array_equal(a, b)


if __name__ == "__main__":
    unittest.main()

import unittest
import numpy as np
from wildfire_lab.kernel import angle_states, fidelity
from wildfire_lab.library_kernel import matrices, project_psd
from wildfire_lab.selection import fit_objective
from wildfire_lab.sqd_selection import sampled_subspace, hamiltonian


class LibraryTests(unittest.TestCase):
    def test_compute_uncompute_matches_independent_cached_states(self):
        rng=np.random.default_rng(18)
        a=rng.uniform(1,2,size=(5,4));b=rng.uniform(1,2,size=(3,4))
        gram,cross,cost=matrices(a,b)
        np.testing.assert_allclose(gram,fidelity(angle_states(a),angle_states(a)),atol=1e-9)
        np.testing.assert_allclose(cross,fidelity(angle_states(b),angle_states(a)),atol=1e-9)
        self.assertEqual(cost['pair_circuits'],25)
        self.assertEqual(cost['hardware_jobs_submitted'],0)

    def test_shot_accounting_and_psd_repair(self):
        a=np.array([[1.,1.2],[2.,2.2],[1.6,1.8]])
        gram,cross,cost=matrices(a,a[:1],shots=128,seed=3)
        self.assertEqual(cost['synthetic_shots'],6*128)
        self.assertTrue(((gram>=0)&(gram<=1)).all())
        matrix=np.array([[1.,2.],[2.,1.]])
        repaired,diagnostic=project_psd(matrix)
        self.assertGreaterEqual(np.linalg.eigvalsh(repaired).min(),-1e-12)
        self.assertEqual(diagnostic['negative_eigenvalues'],1)

    def test_sqd_diagonal_projection_equals_sampled_minimum(self):
        rng=np.random.default_rng(4)
        objective=fit_objective(rng.normal(size=(30,4)),np.arange(30)%2,2)
        h=hamiltonian(objective).to_matrix()
        np.testing.assert_allclose(h,np.diag(np.diag(h)),atol=1e-12)
        row=sampled_subspace(objective,np.array([3,3,5,6,12]))
        self.assertEqual(row['unique_feasible'],4)
        self.assertAlmostEqual(row['sqd_energy'],row['sampled_minimum'],places=9)
        self.assertLess(row['projected_off_diagonal_max'],1e-10)
        self.assertEqual(sampled_subspace(objective,np.array([0,15]))['status'],'no_feasible_sample')

    def test_two_state_subspace_uses_dense_projected_fallback(self):
        rng=np.random.default_rng(3)
        objective=fit_objective(rng.normal(size=(20,4)),np.arange(20)%2,2)
        row=sampled_subspace(objective,np.array([3,5]))
        self.assertEqual(row['eigensolver'],'dense projected matrix')
        self.assertAlmostEqual(row['sqd_energy'],row['sampled_minimum'],places=10)

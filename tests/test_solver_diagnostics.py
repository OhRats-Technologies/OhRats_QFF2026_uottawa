import unittest
import numpy as np
from sklearn.svm import SVC
from wildfire_lab.solver_diagnostics import diagnostics


class SolverDiagnostics(unittest.TestCase):
    def test_primal_dual_and_kkt_of_known_margin_solution(self):
        x=np.array([[-2.],[-1.],[1.],[2.]]);y=np.array([0,0,1,1])
        model=SVC(C=1,kernel='linear',tol=1e-10).fit(x,y)
        d=diagnostics(model,x@x.T,y)
        self.assertAlmostEqual(d['squared_weight_norm'],1,places=8)
        self.assertAlmostEqual(d['primal'],.5,places=8)
        self.assertAlmostEqual(d['dual'],.5,places=8)
        self.assertLess(abs(d['duality_gap']),1e-8)
        self.assertLess(d['kkt_max_violation'],1e-8)
        self.assertEqual(d['fit_status'],0)

    def test_majority_constant_kernel_is_a_valid_degenerate_solution(self):
        gram=np.ones((8,8));y=np.array([0]*7+[1])
        model=SVC(C=1,kernel='precomputed',tol=1e-10).fit(gram,y)
        d=diagnostics(model,gram,y)
        self.assertAlmostEqual(d['squared_weight_norm'],0,places=8)
        self.assertAlmostEqual(d['primal'],2,places=8)
        self.assertAlmostEqual(d['duality_gap'],0,places=8)
        self.assertEqual(d['training_positive_predictions'],0)
        self.assertLess(d['training_decision_std'],1e-10)


if __name__=='__main__':unittest.main()

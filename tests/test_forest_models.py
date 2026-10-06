"""Verify actual Qiskit QSVR fit equations and fold-local preprocessing."""
import unittest
import numpy as np
from wildfire_lab.forest_models import fit,prepare,rbf


class ModelTests(unittest.TestCase):
    def fixture(self):
        rng=np.random.default_rng(17)
        return rng.normal(size=(8,4)),rng.normal(size=(3,4)),np.exp(np.arange(8)/5+2)

    def test_saved_fit_equations(self):
        x,cross,y=self.fixture()
        plan={'quantum':{'angle_amplitude':np.pi/32,'reps':1},
              'models':{'ridge':{'alpha':1.},'svr':{'C':1.,'epsilon':.2}}}
        result=fit(x,cross,y,np.ones(3),['a','b','c','d'],plan)
        sx=np.array(result['scaled_train']);sv=np.array(result['scaled_cross'])
        for row in result['rows']:
            p=row['parameters']
            if row['model']=='ridge':
                prediction=sv@np.array(p['coef'])+p['intercept']
            else:
                matrix=np.array(result['quantum_cross']) if row['model']=='qsvr' else rbf(sx,sv,result['rbf_gamma'])
                prediction=matrix[:,p['support']]@np.array(p['dual_coef'])+p['intercept']
            np.testing.assert_allclose(prediction,row['predicted_scaled'],atol=1e-10)
        self.assertEqual(result['resource']['hardware_jobs_submitted'],0)
        self.assertGreater(result['resource']['pair_circuits'],0)

    def test_cross_rows_do_not_fit_preprocessing(self):
        x,cross,y=self.fixture()
        first=prepare(x,cross,y)
        second=prepare(x,cross+1000,y)
        np.testing.assert_array_equal(first[0],second[0])
        np.testing.assert_array_equal(first[2],second[2])
        self.assertEqual(first[-1],second[-1])


if __name__=='__main__':
    unittest.main()

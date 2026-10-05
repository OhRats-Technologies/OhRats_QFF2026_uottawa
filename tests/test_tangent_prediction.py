import unittest
from unittest.mock import patch
import numpy as np
from wildfire_lab.encoding_screen import normalize_kernel
from wildfire_lab.ridge_kernel import normalized_features
from wildfire_lab.tangent_prediction import run,review
from wildfire_lab.tangent_checks import validate


class TangentPredictionTests(unittest.TestCase):
    def setUp(self):
        rng=np.random.default_rng(21);x=rng.normal(size=(12,2));v=rng.normal(size=(6,2));t=x@np.diag([2.,.5]);w=v@np.diag([2.,.5])
        linear=normalize_kernel(x@x.T,v@x.T);tangent=normalize_kernel(t@t.T,w@t.T)
        kernels=dict(linear=(*linear[:2],normalized_features(x,v),linear[2]),
            tangent=(*tangent[:2],normalized_features(t,w),tangent[2]))
        # Distinct PSD nonlinear perturbation; the prediction bound must still hold.
        g,b,var=normalize_kernel(t@t.T+.03*(t@t.T)**2,w@t.T+.03*(w@t.T)**2)
        kernels['ZZ/0.01']=(g,b,None,var)
        self.sample=({},kernels,np.array([0,1]*6),np.array([0,1]*3),{})
        self.plan=dict(kernel_ridge=1.,angle_scales=[.01],numerical_checks=dict(relative_solve_residual_max=1e-10,
            primal_dual_prediction_difference_max=1e-9,validation_score_std_min=1e-5,reference_metric_tolerance=1e-9),
            narrow_closeness_gate=dict(angle_scale=.01,mean_absolute_ap_difference_max=.02,seed_absolute_ap_difference_max=.03,prediction_spearman_min=.99))

    def test_reconstruction_does_not_solve_and_bound_is_valid(self):
        record=run(self.sample,self.plan)
        with patch('wildfire_lab.ridge_kernel.solve',side_effect=AssertionError('Audit attempted fitting')):
            checks=validate(self.sample,record,self.plan)
        self.assertEqual(checks['predictor_conditions'],3)
        self.assertEqual(checks['primal_reference_solves'],2)
        pair=record['comparisons'][0];self.assertLessEqual(pair['prediction_l2_difference'],pair['prediction_l2_bound'])
        self.assertIn('narrow_closeness_gate',review([record],self.plan))

    def test_changed_coefficient_or_prediction_fails(self):
        import copy
        record=run(self.sample,self.plan)
        for key in ['coefficients','predictions']:
            bad=copy.deepcopy(record);bad['rows'][0][key][0]+=.1
            with self.assertRaises(AssertionError):validate(self.sample,bad,self.plan)

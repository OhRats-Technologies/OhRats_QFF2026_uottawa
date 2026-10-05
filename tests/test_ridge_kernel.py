import unittest
import numpy as np
from wildfire_lab.ridge_kernel import predict,normalized_features
from wildfire_lab.ridge_checks import verify
from wildfire_lab.evaluation import scores


class RidgeKernel(unittest.TestCase):
    def test_dual_matches_explicit_primal_on_rank_deficient_features(self):
        x=np.array([[1.,2.],[1.,2.],[2.,4.],[-1.,-2.],[0.,0.]])
        v=np.array([[.3,.6],[3.,6.]]);x,v=normalized_features(x,v);y=np.array([0,1,1,0,0])
        p,d=predict(x@x.T,v@x.T,y,ridge=1.,features=(x,v))
        target=2*y-1;mean=target.mean()
        explicit=np.linalg.solve(x.T@x+np.eye(2),x.T@(target-mean))
        np.testing.assert_allclose(p,v@explicit+mean,atol=1e-12)
        self.assertLess(d['relative_solve_residual'],1e-12)
        self.assertLess(d['primal_dual_prediction_max_abs_difference'],1e-12)

    def test_validation_cannot_change_training_transform_or_solution(self):
        rng=np.random.default_rng(4);x=rng.normal(size=(15,3));v=rng.normal(size=(4,3));y=np.arange(15)%2
        a,b=normalized_features(x,v);again,more=normalized_features(x,np.vstack([v,[[1e8,2e8,3e8]]]))
        np.testing.assert_array_equal(a,again);np.testing.assert_array_equal(b,more[:4])
        p,d=predict(a@a.T,b@a.T,y)
        p2,d2=predict(a@a.T,more@a.T,y)
        np.testing.assert_allclose(p,p2[:4],atol=1e-12)
        self.assertEqual(d['training_squared_error'],d2['training_squared_error'])

    def test_zero_centered_kernel_returns_training_prevalence_score(self):
        y=np.array([0,0,0,1]);p,d=predict(np.zeros((4,4)),np.zeros((2,4)),y)
        np.testing.assert_array_equal(p,[-.5,-.5]);self.assertEqual(d['squared_feature_weight_norm'],0)
        self.assertEqual(d['relative_solve_residual'],0)
        with self.assertRaises(ValueError):predict(np.eye(4),np.ones((2,4)),y,ridge=0)

    def test_saved_coefficients_are_checked_without_refitting(self):
        rng=np.random.default_rng(31);x=rng.normal(size=(12,3));v=rng.normal(size=(6,3))
        x,v=normalized_features(x,v);y=np.arange(12)%2;target=np.arange(6)%2
        gram,cross=x@x.T,v@x.T;p,d=predict(gram,cross,y,features=(x,v))
        row=dict(**d,predictions=p.tolist(),metric=scores(target,p,False))
        verify(row,gram,cross,(x,v),y,target,1.)
        row['coefficients'][0]+=.1
        with self.assertRaises(AssertionError):verify(row,gram,cross,(x,v),y,target,1.)


if __name__=='__main__':unittest.main()

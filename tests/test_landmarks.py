import unittest
import numpy as np
from sklearn.svm import SVC
from wildfire_lab.landmarks import coordinates,indices,pair_count,assemble
from wildfire_lab.library_kernel import matrices
from wildfire_lab.encoding_screen import normalize_kernel
from wildfire_lab.landmark_review import review


class Landmarks(unittest.TestCase):
    def test_full_psd_basis_matches_centered_kernel(self):
        x=np.array([[1.,0.],[0.,1.],[-1.,0.],[0.,-1.]])
        v=np.array([[.3,.5],[-.2,1.]])
        gram=x@x.T;cross=v@x.T
        ft,fv,diagnostic=coordinates(gram,gram,cross,ridge=0)
        reference,validation,_=normalize_kernel(gram,cross)
        np.testing.assert_allclose(ft@ft.T,reference,atol=1e-12)
        np.testing.assert_allclose(fv@ft.T,validation,atol=1e-12)
        self.assertEqual(diagnostic['retained_rank'],2)
        y=[0,1,0,1]
        linear=SVC(C=1,kernel='linear').fit(ft,y)
        explicit=SVC(C=1,kernel='precomputed').fit(ft@ft.T,y)
        np.testing.assert_allclose(linear.decision_function(fv),
            explicit.decision_function(fv@ft.T),atol=1e-8)

    def test_noisy_basis_is_jointly_psd_and_validation_cannot_fit_it(self):
        w=np.array([[1.,1.3,.1],[1.3,1.,.2],[.1,.2,1.]])
        ct=np.vstack([w,[[.2,.4,.6],[.1,.1,.1]]]);cv=np.array([[.1,.2,.7]])
        ft,fv,diagnostic=coordinates(w,ct,cv)
        again,more,_=coordinates(w,ct,np.vstack([cv,[[1e9,2e9,3e9]]]))
        np.testing.assert_array_equal(ft,again)
        np.testing.assert_array_equal(fv,more[:1])
        features=np.vstack([ft,fv]);joint=features@features.T
        self.assertGreater(np.linalg.eigvalsh(joint).min(),-1e-10)
        self.assertEqual(diagnostic['negative_landmark_eigenvalues'],1)
        self.assertEqual(diagnostic['retained_rank'],2)

    def test_nested_training_landmarks_and_actual_pair_accounting(self):
        small=indices(8,3,81);large=indices(8,5,81)
        self.assertTrue(set(small)<=set(large))
        rng=np.random.default_rng(14);x=rng.uniform(.2,2,(8,2));v=rng.uniform(.2,2,(5,2))
        rest=np.setdiff1d(np.arange(8),small)
        w,cross,cost=matrices(x[small],np.vstack([x[rest],v]),shots=32,reps=1)
        self.assertEqual(cost['pair_circuits'],pair_count(8,5,3))
        self.assertEqual(cost['pair_circuits'],33)
        ct,cv=assemble(w,cross[:5],cross[5:],small,8)
        np.testing.assert_array_equal(ct[small],w)
        np.testing.assert_array_equal(ct[rest],cross[:5])
        np.testing.assert_array_equal(cv,cross[5:])
        self.assertEqual(pair_count(256,256,16),8056)

    def test_quality_gate_does_not_promote_cost_reduction_alone(self):
        plan={'quality_gate':dict(ideal_16_mean_ap_delta_min=-.02,ideal_16_seed_ap_delta_min=-.03,
            ideal_16_seeds_within_min=2,shot_4096_mean_ap_delta_min=-.05,pair_fraction_max=.1)}
        rows=[dict(predictor=name,metric={'average_precision':ap}) for name,ap in
            [('ZZ/dense',.4),('ZZ/ideal/16',.39),('ZZ/4096/16',.36)]]
        seeds=[dict(rows=rows,per_shot_pair_fraction=.082) for _ in range(3)]
        self.assertTrue(review(seeds,plan)['passed'])
        for seed in seeds:seed['rows']=[dict(r) for r in rows]
        seeds[0]['rows'][2]=dict(predictor='ZZ/4096/16',metric={'average_precision':.2})
        self.assertFalse(review(seeds,plan)['passed'])


if __name__=='__main__':unittest.main()

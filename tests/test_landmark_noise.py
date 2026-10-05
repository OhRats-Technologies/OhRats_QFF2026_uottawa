import copy
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
import numpy as np
from wildfire_lab.landmark_noise import draw,kernels,probabilities
from wildfire_lab.geometry_inputs import sha
from wildfire_lab.shot_ridge import fit,audit


class LandmarkNoiseTests(unittest.TestCase):
    def setUp(self):
        rng=np.random.default_rng(8);x=rng.normal(size=(12,2));v=rng.normal(size=(6,2))
        self.g=np.exp(-.3*np.sum((x[:,None]-x[None])**2,axis=2));self.b=np.exp(-.3*np.sum((v[:,None]-x[None])**2,axis=2));self.li=np.array([1,4,8])
        self.plan=dict(landmark_ridge=.001,eigenvalue_cutoff=1e-10,kernel_ridge=1.,relative_solve_residual_max=1e-10,
            primal_dual_difference_max=1e-9,score_std_min=1e-5,shots=[512],noise_seeds=[29],reference_metric_tolerance=1e-9)

    def test_shared_block_known_diagonals_and_pair_budget(self):
        c=draw(self.g,self.b,self.li,512,811,29);k,b,(x,v),d=kernels(c,self.g,self.b,self.li,512,self.plan)
        self.assertTrue(np.array_equal(c['landmark'],c['landmark'].T));self.assertTrue(np.all(c['landmark'].diagonal()==512))
        self.assertEqual(d['binomial_pair_estimates'],48);self.assertEqual(d['modeled_shot_exposure'],48*512)
        np.testing.assert_allclose(k,x@x.T);np.testing.assert_allclose(b,v@x.T);self.assertAlmostEqual(np.mean(np.diag(k)),1)
        for name,a in draw(self.g,self.b,self.li,512,811,29).items():np.testing.assert_array_equal(a,c[name])

    def test_binomial_mean_and_variance(self):
        p=probabilities(self.g,self.b,self.li)['other'][0,0];s=512
        values=np.random.default_rng(11).binomial(s,p,size=30000)/s
        self.assertLess(abs(values.mean()-p),5*np.sqrt(p*(1-p)/(s*len(values))))
        self.assertLess(abs(values.var()/(p*(1-p)/s)-1),.04)

    def test_saved_counts_audit_without_draws_or_solves_and_tamper_rejection(self):
        y=np.array([0,1]*6);target=np.array([0,1]*3);c=draw(self.g,self.b,self.li,512,811,29)
        with tempfile.TemporaryDirectory() as directory:
            cache=Path(directory);path=cache/'counts.npz';np.savez_compressed(path,**c)
            row=fit('ZZ/shot/512/29',kernels(c,self.g,self.b,self.li,512,self.plan),y,target,self.plan,
                    shots=512,noise_seed=29,matrix_file=path.name,matrix_sha256=sha(path))
            sample=({'landmark_indices':self.li.tolist()},self.g,self.b,{},y,target,{})
            record=dict(landmark_indices=self.li.tolist(),rows=[row],reference_metrics_match=True)
            with patch('wildfire_lab.ridge_kernel.solve',side_effect=AssertionError('solve')),patch('wildfire_lab.shot_ridge.draw',side_effect=AssertionError('draw')):
                self.assertEqual(audit(sample,record,self.plan,cache)['predictor_conditions'],1)
            bad=copy.deepcopy(record);bad['rows'][0]['predictions'][0]+=.1
            with self.assertRaises(AssertionError):audit(sample,bad,self.plan,cache)
            c['landmark'][0,1]+=1;np.savez_compressed(path,**c)
            with self.assertRaises(AssertionError):audit(sample,record,self.plan,cache)

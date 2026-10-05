import unittest
import numpy as np
from wildfire_lab.shot_noise import centered,error_coefficients,describe


class ShotNoiseTests(unittest.TestCase):
    def test_centering_covariance_matches_independent_shot_monte_carlo(self):
        gram=np.array([[1.,.7,.2],[.7,1.,.4],[.2,.4,1.]])
        cross=np.array([[.3,.8,.4],[.6,.1,.9]])
        shots=32;rng=np.random.default_rng(71);trials=30000;n=3;m=2
        i,j=np.triu_indices(n,1);error=np.zeros((trials,n,n))
        draws=rng.binomial(shots,gram[i,j],size=(trials,len(i)))/shots-gram[i,j]
        error[:,i,j]=draws;error[:,j,i]=draws
        f=rng.binomial(shots,cross,size=(trials,m,n))/shots-cross
        mean=error.mean(axis=1);grand=mean.mean(axis=1)
        a=error-mean[:,None,:]-mean[:,:,None]+grand[:,None,None]
        b=f-f.mean(axis=2)[:,:,None]-mean[:,None,:]+grand[:,None,None]
        expected=error_coefficients(gram,cross)
        self.assertAlmostEqual(np.mean(np.sum(a*a,axis=(1,2)))*shots,expected['train'],delta=.015)
        self.assertAlmostEqual(np.mean(np.sum(b*b,axis=(1,2)))*shots,expected['cross'],delta=.015)
        self.assertGreater(expected['cross_training_mean_component'],0)

    def test_known_diagonal_fixed_normalization_and_shot_scaling(self):
        gram=np.array([[1.,.6],[.6,1.]]);cross=np.array([[.2,.8]])
        a,b=centered(gram,cross);self.assertTrue(np.allclose(a.sum(axis=0),0));self.assertTrue(np.allclose(b.sum(axis=1),0))
        result=describe(gram,cross,[100,400],[.25])
        first,last=result['shot_conditions']
        self.assertAlmostEqual(first['expected_relative_frobenius_error']['train']/last['expected_relative_frobenius_error']['train'],2.)
        self.assertAlmostEqual(error_coefficients(gram,cross)['cross_training_mean_component'],0.)
        with self.assertRaisesRegex(ValueError,'Degenerate'):describe(np.ones((2,2)),np.ones((1,2)),[100],[.25])
        with self.assertRaisesRegex(ValueError,'unit diagonal'):error_coefficients(np.eye(2)*.9,cross)

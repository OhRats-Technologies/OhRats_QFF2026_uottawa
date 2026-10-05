import unittest
import numpy as np
from wildfire_lab.local_geometry import derivative_points,quantum_metric,describe,tangent_kernel


def product_states(points,phase=False):
    output=[]
    for p in points:
        state=np.array([1],dtype=complex)
        for angle in p:state=np.kron(state,[np.cos(angle/2),np.sin(angle/2)])
        output.append(state*np.exp(1j*(2*p[0]-3*p[1])) if phase else state)
    return np.array(output)


class LocalGeometryTests(unittest.TestCase):
    def test_phase_invariance_and_known_ry_metric(self):
        points=derivative_points([.4,.8],1e-5)
        plain=quantum_metric(product_states(points),1e-5)
        phase=quantum_metric(product_states(points,True),1e-5)
        np.testing.assert_allclose(plain,np.eye(2)/4,atol=1e-9)
        np.testing.assert_allclose(phase,plain,atol=1e-8)
        with self.assertRaises(AssertionError):quantum_metric(product_states(points)*2,1e-5)

    def test_centering_factor_and_cross_training_mean(self):
        x=np.array([[-.9,-.2],[.4,.8],[.2,-.5],[.6,.1]])
        v=np.array([[-.1,.3],[.9,-.7]]);scale=.001;metric=np.eye(2)/4
        a=product_states(np.pi*(.5+scale*x));b=product_states(np.pi*(.5+scale*v))
        gram=np.abs(a.conj()@a.T)**2;cross=np.abs(b.conj()@a.T)**2
        result=describe(gram,cross,x,v,metric,scale)
        self.assertLess(result['raw_centered_train_relative_error'],1e-5)
        self.assertLess(result['raw_centered_cross_relative_error'],1e-5)
        self.assertLess(result['normalized_cross_shape_relative_error'],1e-5)
        tangent,other=tangent_kernel(x,v,metric)
        np.testing.assert_allclose(tangent.sum(axis=0),0,atol=1e-12)
        np.testing.assert_allclose(other.sum(axis=1),0,atol=1e-12)
        self.assertEqual(result['tangent_metric_rank'],2)
        self.assertGreater(result['exact_top_input_dimension_variance_fraction'],.99999)

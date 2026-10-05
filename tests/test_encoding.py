import unittest
import numpy as np
import pandas as pd
from qiskit import QuantumCircuit
from qiskit.quantum_info import Statevector
from wildfire_lab.encoding_screen import preprocess, normalize_kernel
from wildfire_lab.kernel import angle_product_kernel


class EncodingTests(unittest.TestCase):
    def test_transform_fits_only_training(self):
        train=pd.DataFrame({'x':[0.,2.,4.,np.nan]})
        valid=pd.DataFrame({'x':[1.,1e9]})
        for variant in ['standard_tanh','standard_clip','robust_tanh']:
            x,v,bx,bv=preprocess(train,valid,['x'],variant)
            x2,_,bx2,_=preprocess(train,pd.DataFrame({'x':[-1e9]}),['x'],variant)
            np.testing.assert_allclose(x,x2);np.testing.assert_allclose(bx,bx2)
            self.assertTrue(np.isfinite(v).all())
            self.assertTrue((np.abs(bv)<=1).all())

    def test_train_centering_and_cross_reconstruction(self):
        x=np.array([[1.,2.],[3.,0.],[2.,1.]])
        gram=x@x.T
        normalized,cross,variance=normalize_kernel(gram,gram)
        np.testing.assert_allclose(normalized,cross)
        np.testing.assert_allclose(normalized.mean(axis=0),0,atol=1e-14)
        self.assertAlmostEqual(np.trace(normalized)/len(x),1.)
        self.assertGreater(np.linalg.eigvalsh(normalized).min(),-1e-12)
        _,extra,_=normalize_kernel(gram,np.vstack([gram,gram[:1]*10]))
        np.testing.assert_allclose(extra[:3],cross)

    def test_analytic_product_matches_qiskit(self):
        angles=np.array([[.2,.5],[1.1,-.3],[0.,0.]])
        states=[]
        for row in angles:
            circuit=QuantumCircuit(2)
            for j,angle in enumerate(row):circuit.ry(angle,j)
            states.append(Statevector.from_instruction(circuit).data)
        states=np.array(states)
        np.testing.assert_allclose(angle_product_kernel(angles,angles),np.abs(states.conj()@states.T)**2,atol=1e-14)

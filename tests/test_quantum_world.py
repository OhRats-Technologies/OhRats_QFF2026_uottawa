import unittest
import numpy as np
import torch
from scipy.linalg import expm
from quantum_world.physics import (PAULIS,LABELS,GENERATORS,HAMILTONIANS,unitary,
    state_to_pauli,pauli_to_density,haar_states,pauli_rotation,midpoint_collision,
    physical_metrics,project_density,concurrence)
from quantum_world.data import transitions,physical_path
from quantum_world.models import OrthogonalEncoder,PauliLinearBaseline,LatentModel


class QuantumWorldTests(unittest.TestCase):
    def test_qiskit_wire_convention_and_gates(self):
        from qiskit import QuantumCircuit
        from qiskit.quantum_info import Operator
        for g in range(6):
            qc=QuantumCircuit(2)
            if g<2:qc.h(1-g)
            elif g==2:qc.cx(1,0)
            elif g==3:qc.cx(0,1)
            else:qc.rz(.73,5-g)
            np.testing.assert_allclose(Operator(qc).data,unitary(g,.73 if g>=4 else 1),atol=1e-12)

    def test_pauli_roundtrip_and_dynamics(self):
        psi=haar_states(20,14); r=state_to_pauli(psi)
        np.testing.assert_allclose(pauli_to_density(r),psi[:,:,None]*psi.conj()[:,None,:],atol=1e-12)
        for g in range(6):
            np.testing.assert_allclose(state_to_pauli(psi@unitary(g,.8).T),r@expm(.8*GENERATORS[g]).T,atol=1e-12)
        np.testing.assert_allclose(GENERATORS+GENERATORS.transpose(0,2,1),0,atol=1e-12)

    def test_bell_local_blindness(self):
        a=np.array([1,0,0,1])/np.sqrt(2); b=np.array([1,0,0,-1])/np.sqrt(2)
        local=[i for i,s in enumerate(LABELS) if 'I' in s]
        np.testing.assert_allclose(state_to_pauli(a)[local],state_to_pauli(b)[local],atol=1e-12)
        self.assertGreater(np.linalg.norm(state_to_pauli(a)-state_to_pauli(b)),2)
        self.assertAlmostEqual(float(concurrence(a)),1)

    def test_midpoint_ambiguity(self):
        result=midpoint_collision()
        self.assertEqual(result['lost_dimensions'],8)
        self.assertGreater(result['velocity_separation'],1)
        self.assertGreater(result['physical_path_halfway_separation'],1)

    def test_finite_difference_path_velocity(self):
        d=transitions(16,77); t=np.linspace(.1,.9,16); h=1e-5
        x,v=physical_path(d,t)
        plus,_=physical_path(d,t+h);minus,_=physical_path(d,t-h)
        np.testing.assert_allclose(v,(plus-minus)/(2*h),atol=1e-8)

    def test_encoder_is_invertible_and_gradients(self):
        m=OrthogonalEncoder().double()
        with torch.no_grad():m.raw.normal_(std=.05)
        x=torch.randn(12,15,dtype=torch.float64)
        torch.testing.assert_close(m.decode(m(x)),x)
        m(x).square().mean().backward()
        self.assertTrue(torch.isfinite(m.raw.grad).all())

    def test_projection_metrics_do_not_hide_invalid_states(self):
        psi=haar_states(8,5); r=state_to_pauli(psi)
        metrics=physical_metrics(r,psi)
        self.assertAlmostEqual(metrics['mean_projected_fidelity'],1)
        bad=physical_metrics(2*r,psi)
        self.assertEqual(bad['raw_valid_fraction'],0)
        self.assertGreater(bad['raw_overlap_mean'],1)
        values=np.linalg.eigvalsh(project_density(pauli_to_density(2*r)))
        self.assertGreaterEqual(values.min(),-1e-12)
        np.testing.assert_allclose(values.sum(axis=-1),1,atol=1e-12)
        extreme=project_density(np.diag([1e30,-1e30,0,0]).astype(complex))
        self.assertTrue(np.isfinite(extreme).all())
        self.assertAlmostEqual(float(np.trace(extreme).real),1)

    def test_classical_baseline_extrapolates(self):
        train=transitions(2048,101); test=transitions(64,103,angle_limit=3.1)
        model=PauliLinearBaseline().fit(train)
        np.testing.assert_allclose(model.predict(test['x'],test['gate'],test['duration']),test['y'],atol=2e-7)

    def test_hamiltonian_generator_is_physical_and_composes(self):
        m=LatentModel('hamiltonian').double()
        with torch.no_grad():m.coefficients.normal_(std=.2);m.encoder.raw.normal_(std=.02)
        x=torch.tensor(state_to_pauli(haar_states(8,71)),dtype=torch.float64)
        g=torch.full((8,),4,dtype=torch.long)
        a=torch.full((8,),.4,dtype=torch.float64);b=2*a
        out=m.predict(x,g,a+b)
        composed=m.predict(m.predict(x,g,a),g,b)
        torch.testing.assert_close(out,composed)
        torch.testing.assert_close(m.predict(m.predict(x,g,a),g,-a),x)
        self.assertGreaterEqual(np.linalg.eigvalsh(pauli_to_density(out.detach().numpy())).min(),-1e-12)

    def test_shot_noise_is_unbiased_and_preserves_inputs(self):
        from scripts.quantum_world_endpoint_pilot import shot_targets
        d=transitions(20,831)
        clean=shot_targets(d,0,1)
        np.testing.assert_array_equal(clean['y'],d['y'])
        noisy=shot_targets(d,128,5)
        np.testing.assert_array_equal(noisy['x'],d['x'])
        self.assertTrue((np.abs(noisy['y'])<=1).all())
        # Independent Pauli measurement means converge to exact expectations.
        stacked=np.array([shot_targets(d,128,s)['y'] for s in range(400)])
        self.assertLess(np.max(np.abs(stacked.mean(axis=0)-d['y'])),.02)

    def test_endpoint_training_has_no_oracle_derivative(self):
        from scripts.quantum_world_pilot import train
        from unittest.mock import patch
        torch.set_num_threads(1)
        d=transitions(64,132)
        with patch('scripts.quantum_world_pilot.physical_path',side_effect=AssertionError('Oracle accessed')):
            m,metadata=train('hamiltonian',212,d,steps=3,supervision='endpoints')
        self.assertEqual(metadata['supervision'],'endpoints only')
        self.assertTrue(all(torch.isfinite(p).all() for p in m.parameters()))

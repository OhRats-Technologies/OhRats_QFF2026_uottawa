import unittest
import torch
from quantum_world.jepa import JEPAWorld,train_world,fit_readout,covariance_anchor
from quantum_world.data import transitions
from quantum_world.physics import haar_states,state_to_pauli


class QuantumJEPATests(unittest.TestCase):
    def test_readout_training_cannot_modify_world(self):
        torch.set_num_threads(1)
        m=JEPAWorld('direct')
        before={k:v.clone() for k,v in m.state_dict().items()}
        r=torch.tensor(state_to_pauli(haar_states(64,38)),dtype=torch.float32)
        fit_readout(m,r,32,steps=3)
        self.assertTrue(all(torch.equal(v,before[k]) for k,v in m.state_dict().items()))

    def test_latent_generator_group_and_norm(self):
        torch.manual_seed(9)
        m=JEPAWorld('latent_generator').double()
        with torch.no_grad():m.raw_generator.normal_(std=.1)
        z=torch.randn(6,15,dtype=torch.float64)
        gate=torch.full((6,),4,dtype=torch.long)
        t=torch.full((6,),.31,dtype=torch.float64)
        y=m.advance(z,gate,t)
        torch.testing.assert_close(y.norm(dim=-1),z.norm(dim=-1))
        torch.testing.assert_close(m.advance(y,gate,-t),z)
        torch.testing.assert_close(m.advance(y,gate,t),m.advance(z,gate,2*t))

    def test_no_reconstruction_training_objective(self):
        torch.set_num_threads(1)
        m,metadata=train_world('latent_generator',34,transitions(64,41),steps=3)
        self.assertFalse(metadata['reconstruction_loss'])
        self.assertTrue(all(torch.isfinite(p).all() for p in m.parameters()))

    def test_covariance_anchor_detects_constant_representation(self):
        constant=torch.zeros(128,15)
        self.assertGreater(float(covariance_anchor(constant)),.05)

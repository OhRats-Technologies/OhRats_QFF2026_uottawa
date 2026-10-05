import unittest
import torch
import numpy as np
from quantum_world.readout import PhysicalReadout,fit_physical_readout
from quantum_world.jepa import JEPAWorld
from quantum_world.physics import haar_states,state_to_pauli,pauli_to_density


class PhysicalReadoutTests(unittest.TestCase):
    def test_valid_even_for_ood_latents(self):
        torch.set_num_threads(1);torch.manual_seed(22)
        probe=PhysicalReadout().double()
        for scale in (1,10,100):
            z=scale*torch.randn(16,15,dtype=torch.float64)
            with torch.no_grad():rho=probe.density(z);r=probe(z)
            self.assertGreater(float(torch.linalg.eigvalsh(rho).min()),-1e-10)
            torch.testing.assert_close(rho.diagonal(dim1=-2,dim2=-1).sum(dim=-1),torch.ones(16,dtype=torch.complex128))
            np.testing.assert_allclose(pauli_to_density(r.numpy()),rho.numpy(),atol=1e-10)

    def test_gradient_is_finite_and_probe_does_not_update_encoder(self):
        torch.set_num_threads(1);model=JEPAWorld('direct')
        before={k:v.clone() for k,v in model.state_dict().items()}
        r=torch.tensor(state_to_pauli(haar_states(64,628)),dtype=torch.float32)
        probe=fit_physical_readout(model,r,882,steps=3)
        self.assertTrue(all(torch.equal(v,before[k]) for k,v in model.state_dict().items()))
        z=torch.randn(8,15,requires_grad=True)
        probe(z).square().mean().backward()
        self.assertTrue(torch.isfinite(z.grad).all())

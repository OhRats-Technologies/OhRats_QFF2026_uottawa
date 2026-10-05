import unittest
import numpy as np
import torch
from quantum_world.latent_linear import LatentLinear
from quantum_world.data import transitions,trajectory
from quantum_world.physics import state_to_pauli


class TransferredLinearTests(unittest.TestCase):
    def test_frozen_encoder_periodic_extrapolation_and_rollout(self):
        encoder=torch.nn.Linear(23,15,bias=False).double()
        with torch.no_grad():encoder.weight.copy_(torch.cat([torch.eye(15),torch.zeros(15,8)],dim=-1))
        before=encoder.weight.detach().clone()
        model=LatentLinear(encoder).fit(transitions(2048,2901))
        self.assertTrue(torch.equal(before,encoder.weight))
        trajectory_data=trajectory(16,64,2902)
        z=torch.tensor(state_to_pauli(trajectory_data['psi'][0]))
        for g,t in zip(trajectory_data['gate'],trajectory_data['duration']):
            z=model.advance(z,torch.tensor(g),torch.tensor(t))
        np.testing.assert_allclose(z.numpy(),state_to_pauli(trajectory_data['psi'][-1]),atol=1e-5)
        duration=torch.tensor([1.8],requires_grad=True,dtype=torch.float64)
        prediction=model.advance(z[:1],torch.tensor([4]),duration)
        prediction[:,3].sum().backward()
        self.assertTrue(torch.isfinite(duration.grad).all())
        self.assertGreater(float(duration.grad.abs().sum()),1e-4)


if __name__=='__main__':unittest.main()

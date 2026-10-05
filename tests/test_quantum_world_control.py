import unittest
import numpy as np
import torch
from quantum_world.control import CachedRotation,ExactPauliModel,control_template,rollout,exact_states,plan
from quantum_world.physics import GENERATORS,haar_states,state_to_pauli


class ControlTests(unittest.TestCase):
    def test_cached_evolution_and_duration_gradient(self):
        cache=CachedRotation(GENERATORS)
        z=torch.tensor(state_to_pauli(haar_states(3,77)),dtype=torch.float64)
        t=torch.tensor([-.7,.2,2.8],dtype=torch.float64,requires_grad=True)
        actual=cache.advance(z,4,t)
        expected=torch.einsum('nij,nj->ni',torch.matrix_exp(torch.tensor(GENERATORS[4])*t[:,None,None]),z)
        torch.testing.assert_close(actual,expected,rtol=1e-9,atol=1e-9)
        actual[:,3].sum().backward();self.assertTrue(torch.isfinite(t.grad).all())
        self.assertGreater(float(t.grad.abs().sum()),1e-4)

    def test_template_exact_agreement(self):
        self.assertEqual(len(control_template()),43)
        self.assertEqual(len([i for _,i in control_template() if i is not None]),24)
        states=haar_states(2,91);angles=np.random.default_rng(92).uniform(-np.pi,np.pi,(2,24))
        actual=rollout(ExactPauliModel(),torch.tensor(state_to_pauli(states)),torch.tensor(angles)).numpy()
        np.testing.assert_allclose(actual,state_to_pauli(exact_states(states,angles)),atol=1e-10)

    def test_planner_selects_latent_objective(self):
        states=haar_states(2,3);target=haar_states(2,4);model=ExactPauliModel()
        result=plan(model,state_to_pauli(states),state_to_pauli(target),5,steps=4,restarts=2)
        final=rollout(model,model.encode(state_to_pauli(states)),torch.tensor(result['angles']))
        cost=(final-model.encode(state_to_pauli(target))).square().mean(dim=-1).numpy()
        np.testing.assert_allclose(cost,result['latent_cost'],atol=1e-10)


if __name__=='__main__':unittest.main()

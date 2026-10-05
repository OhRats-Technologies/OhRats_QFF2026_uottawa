import unittest
import torch
from quantum_world.algebra import gate_algebra_penalty
from quantum_world.physics import GENERATORS


class AlgebraTests(unittest.TestCase):
    def test_true_gate_algebra_and_wrong_generator(self):
        physical=torch.tensor(GENERATORS,dtype=torch.float64)
        self.assertLess(float(gate_algebra_penalty(physical)),1e-20)
        wrong=physical.clone();wrong[2]*=.65;wrong.requires_grad_(True)
        loss=gate_algebra_penalty(wrong)
        self.assertGreater(float(loss.detach()),.01)
        loss.backward();self.assertTrue(torch.isfinite(wrong.grad).all())
        self.assertGreater(float(wrong.grad.abs().sum()),.01)


if __name__=='__main__':unittest.main()

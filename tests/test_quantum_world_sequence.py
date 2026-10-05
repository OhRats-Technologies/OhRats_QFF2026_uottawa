import unittest
import numpy as np
import torch
from quantum_world.sequence_jepa import triplets,train_sequence,prediction_objective
from quantum_world.physics import state_to_pauli,unitary


class SequenceTests(unittest.TestCase):
    def test_normalized_prediction_has_fixed_total_weight(self):
        teacher=torch.tensor(2.,requires_grad=True);rollout=torch.tensor(4.,requires_grad=True)
        loss=prediction_objective(teacher,rollout,1.,True);loss.backward()
        self.assertEqual(float(loss),3.)
        self.assertEqual(float(teacher.grad+rollout.grad),1.)
        self.assertEqual(float(prediction_objective(teacher,rollout,0.,True)),2.)
        with self.assertRaises(ValueError):prediction_objective(teacher,rollout,-1.)

    def test_observed_triplets_are_correct_compositions(self):
        data=triplets(16,991)
        for k in (0,1):
            truth=np.array([unitary(int(g),float(t))@p for p,g,t in zip(data['psi'][k],data['gate'][k],data['duration'][k])])
            np.testing.assert_allclose(truth,data['psi'][k+1],atol=1e-12)
        np.testing.assert_allclose(data['observed'],state_to_pauli(data['psi']),atol=1e-12)

    def test_both_matched_objectives_train_without_reconstruction(self):
        torch.set_num_threads(1);data=triplets(64,992)
        for weight in (0.,1.):
            model,metadata=train_sequence('latent_generator',993,data,steps=3,consistency=weight,batch=16)
            self.assertFalse(metadata['reconstruction_loss'])
            self.assertTrue(all(torch.isfinite(v).all() for v in model.state_dict().values()))
            self.assertEqual(metadata['history'][-1]['step'],2)


if __name__=='__main__':unittest.main()

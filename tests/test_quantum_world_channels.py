import unittest
import numpy as np
import torch
from scipy.linalg import expm
from quantum_world.channels import states,channel,density_to_pauli,lindblad_bases,mixed_metrics,ChannelWorld,anchor_conflict,depolarizing_certificate,choi_from_transfer
from quantum_world.physics import pauli_to_density


class ChannelTests(unittest.TestCase):
    def test_generator_matches_independent_kraus_reference_and_composition(self):
        rho=states(16,712)
        for g in (0,1):
            before=np.column_stack([np.ones(len(rho)),density_to_pauli(rho)])
            predicted=(before@expm(lindblad_bases()[g]*.83).T)[:,1:]
            truth=np.array([channel(r,g,.83,1.) for r in rho])
            np.testing.assert_allclose(pauli_to_density(predicted),truth,atol=1e-12)
            composed=np.array([channel(channel(r,g,.4,1.),g,.43,1.) for r in rho])
            np.testing.assert_allclose(composed,truth,atol=1e-12)
            self.assertAlmostEqual(mixed_metrics(predicted,truth)['mean_fidelity'],1.,places=7)

    def test_cptp_physical_prediction_and_time_guard(self):
        model=ChannelWorld('physical').double()
        source=torch.tensor(density_to_pauli(states(20,713)))
        prediction=model(source,torch.arange(20)%2,torch.full((20,),4.,dtype=torch.float64))
        rho=pauli_to_density(prediction.detach().numpy())
        self.assertGreaterEqual(float(np.linalg.eigvalsh(rho).min()),-1e-12)
        np.testing.assert_allclose(np.trace(rho,axis1=-2,axis2=-1),1,atol=1e-12)
        prediction.square().sum().backward();self.assertTrue(torch.isfinite(model.raw_rate.grad).all())
        with self.assertRaises(ValueError):model(source,torch.arange(20)%2,torch.full((20,),-1.))

    def test_anchor_conflict_minimum(self):
        self.assertEqual(anchor_conflict(1.)['minimum_paired_anchor'],0.)
        result=anchor_conflict(.5)
        self.assertGreater(result['minimum_paired_anchor'],.2)
        s=result['optimal_current_covariance'];p=.5
        derivative=(s-1)+p*p*(p*p*s-1)
        self.assertAlmostEqual(derivative,0.,places=12)

    def test_isotropic_choi_crossing_is_not_complete_forgetting(self):
        result=depolarizing_certificate(1.1,.5)
        self.assertEqual(result['entanglement_breaking_index'],3)
        self.assertLess(result['before']['choi_pt_min_eigenvalue'],0.)
        self.assertGreater(result['after']['choi_pt_min_eigenvalue'],0.)
        self.assertAlmostEqual(result['at_threshold']['choi_pt_min_eigenvalue'],0.,places=12)
        self.assertAlmostEqual(result['at_threshold']['worst_case_trace_distance_to_stationary'],.15,places=12)

    def test_choi_normalization_complete_positivity_and_tp(self):
        for generator in lindblad_bases():
            choi=choi_from_transfer(expm(generator*2.))
            self.assertGreater(float(np.linalg.eigvalsh(choi).min()),-1e-12)
            self.assertAlmostEqual(float(np.trace(choi).real),1.,places=12)
            marginal=np.trace(choi.reshape(4,4,4,4),axis1=1,axis2=3)
            np.testing.assert_allclose(marginal,np.eye(4)/4,atol=1e-12)

    def test_noise_channels_match_qiskit_aer(self):
        from qiskit.quantum_info import DensityMatrix,Operator
        from qiskit_aer.noise import depolarizing_error,amplitude_damping_error
        rho=states(4,793);t=.7;rate=.8;p=np.exp(-rate*t)
        references=[depolarizing_error(1-p,2).to_quantumchannel(),
            amplitude_damping_error(1-p).to_quantumchannel().tensor(Operator(np.eye(2)))]
        for g,reference in enumerate(references):
            for source in rho:
                np.testing.assert_allclose(DensityMatrix(source).evolve(reference).data,
                    channel(source,g,t,rate),atol=1e-12)


if __name__=='__main__':unittest.main()

import unittest
import numpy as np
from quantum_world.channels import transitions,channel,density_to_pauli
from scripts.quantum_world_rate_audit import expected_pauli,fit


class RateAuditTests(unittest.TestCase):
    def test_likelihood_predictions_match_independent_kraus_reference(self):
        data=transitions(16,791)
        for g in (0,1):
            expected=np.array([channel(r,g,float(t),.83) for r,t in zip(data['rho'],data['duration'])])
            np.testing.assert_allclose(expected_pauli(data['x'],g,data['duration'],.83),density_to_pauli(expected),atol=1e-12)

    def test_expected_count_fit_recovers_rates(self):
        data=transitions(512,792)
        counts=(data['y']+1)*500
        fitted=fit(data['x'],data['gate'],data['duration'],counts,1000)
        np.testing.assert_allclose(fitted,[1.10,.65],atol=1e-5)


if __name__=='__main__':unittest.main()

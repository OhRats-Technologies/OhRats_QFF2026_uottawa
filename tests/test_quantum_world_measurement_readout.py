import unittest
import numpy as np
from quantum_world.measurement_readout import probabilities,blind_estimate,calibrated_estimate,goodness_of_fit


class ReadoutCalibrationTests(unittest.TestCase):
    def test_readout_formula_matches_independent_bit_flip_matrix(self):
        e=.03;p=np.exp(-1.05*.8);before=np.array([(1+3*p)/4,*([(1-p)/4]*3)])
        flip=np.array([[1-e,e],[e,1-e]])
        np.testing.assert_allclose(probabilities(1.05,.8,e),np.kron(flip,flip)@before,atol=1e-12)

    def test_calibration_restores_known_rate_and_propagates_intervals(self):
        budget=1000000;e=.01;gamma=1.05
        reference=np.rint(probabilities(0.,.8,e)*budget).astype(int)
        probe=np.rint(probabilities(gamma,.8,e)*budget).astype(int)
        result=calibrated_estimate(reference,probe)
        self.assertAlmostEqual(result['rate'],gamma,places=4)
        self.assertLess(result['interval'][0],gamma);self.assertGreater(result['interval'][1],gamma)
        self.assertGreater(blind_estimate(probe)['rate'],gamma+.03)
        self.assertTrue(goodness_of_fit(probe)['reject'])

    def test_cli_serializes_all_stress_scenarios(self):
        import contextlib,io,json,tempfile
        from pathlib import Path
        from unittest.mock import patch
        from scripts.quantum_world_readout_pilot import main
        with tempfile.TemporaryDirectory() as directory:
            output=Path(directory)/'fresh'
            with patch('sys.argv',['pilot','--output',str(output),'--replicates','2']),contextlib.redirect_stdout(io.StringIO()):main()
            self.assertEqual(json.loads((output/'completion.json').read_text())['comparisons'],36)
            self.assertEqual(len(json.loads((output/'results.json').read_text())),36)


if __name__=='__main__':unittest.main()

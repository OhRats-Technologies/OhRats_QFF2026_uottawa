"""Public hardware replay forbids new quantum work, fits, draws and service access."""
from contextlib import ExitStack
from pathlib import Path
import unittest
from unittest.mock import patch
import numpy as np
from wildfire_lab.saved_hardware_selector import audit as selector_audit, counts_checked
from wildfire_lab.saved_hardware_kernels import audit as kernel_audit, audit_shards, repair

ROOT = Path(__file__).resolve().parents[1]


class SavedHardwareTests(unittest.TestCase):
    def test_published_evidence_replays_without_execution(self):
        guards = ['wildfire_lab.forest_models.Ridge.fit','wildfire_lab.forest_models.SVR.fit',
                  'wildfire_lab.forest_models.QSVR.fit','qiskit.quantum_info.Statevector.from_instruction',
                  'qiskit.primitives.StatevectorSampler.run','numpy.random.default_rng',
                  'wildfire_lab.selector_hardware.service','urllib.request.urlopen',
                  'wildfire_lab.selector_sector.diagonal_sqd']
        with ExitStack() as stack:
            for name in guards:
                stack.enter_context(patch(name,side_effect=AssertionError('Replay executed '+name)))
            receipt = selector_audit(ROOT)
            self.assertEqual(receipt['predictor_equations'],33)
            self.assertEqual(receipt['physical_shots'],18432)
            kernel = kernel_audit(ROOT)
            self.assertEqual(kernel['status'],'verified_terminal_failure')
            self.assertEqual(kernel['returned_physical_shots'],0)
            if (ROOT/'docs/results/selector-hardware-kernel-shards.json').exists():
                measured = audit_shards(ROOT)
                self.assertEqual(measured['predictor_equations'],60)
                self.assertEqual(measured['physical_shots'],343040)

    def test_corrupt_shot_or_bit_width_rejected(self):
        for counts,shots,width in [({'001':4},5,3),({'001':4},4,4),({'00x':4},4,3)]:
            with self.assertRaises(AssertionError):
                counts_checked(counts,shots,width)

    def test_psd_repair_projects_cross_to_same_support(self):
        gram = np.diag([-2.,1.,3.])
        cross = np.array([[5.,7.,11.]])
        fixed,test = repair(gram,cross,rank=1)
        np.testing.assert_array_equal(fixed,np.diag([0.,0.,3.]))
        np.testing.assert_array_equal(test,[[0.,0.,11.]])


if __name__ == '__main__':
    unittest.main()

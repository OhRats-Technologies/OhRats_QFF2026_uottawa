"""Sparse bit ordering, independent calibration and observed-basis-only correction."""
import unittest
import numpy as np
from wildfire_lab.selector_hardware_analysis import bit_rows, assignment, observed_readout


class AnalysisTests(unittest.TestCase):
    def test_candidate_counter_order(self):
        states,bits,weights = bit_rows({'001101':3,'110010':5},6)
        np.testing.assert_array_equal(states,[13,50])
        np.testing.assert_array_equal(bits[:,:4],[[1,0,1,1],[0,1,0,0]])
        np.testing.assert_array_equal(states>>4,[0,3])
        self.assertEqual(int(weights.sum()),8)

    def test_perfect_readout_preserves_existing_basis_only(self):
        channels = assignment({'000':128},{'111':128},3)
        np.testing.assert_array_equal(channels,np.repeat(np.eye(2)[None,:,:],3,axis=0))
        result = observed_readout({'011':9,'101':7},channels,[3,5])
        self.assertEqual(result['basis_states'],[3,5])
        np.testing.assert_allclose(result['conditional_positive_weights'],[9/16,7/16])
        self.assertEqual(result['negative_entries'],0)


if __name__=='__main__':
    unittest.main()

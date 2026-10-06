"""Hardware-output parsing, timing and replay safety on synthetic fixtures."""
from pathlib import Path
import hashlib
import json
import tempfile
import unittest
from unittest.mock import patch
import numpy as np
from wildfire_lab.mitigation_hardware_analysis import analyze,dense,channels,elapsed

class AnalysisTests(unittest.TestCase):
    def test_bit_order_calibration_and_utc_elapsed(self):
        np.testing.assert_array_equal(dense({'0010':7,'0001':3},4)[:4],[0,3,7,0])
        zero=np.zeros(16);one=np.zeros(16);zero[0]=512;one[-1]=512
        np.testing.assert_array_equal(channels(zero,one,4),np.repeat(np.eye(2)[None],4,axis=0))
        self.assertEqual(elapsed({'created':'2026-10-06T10:00:00Z','finished':'2026-10-06T10:00:07+00:00'},'created','finished'),7)
        self.assertIsNone(elapsed({},'created','finished'))

    def fixture(self,root):
        output=root/'private';output.mkdir()
        (root/'docs/results').mkdir(parents=True)
        parent=dict(actual_ha=[1.,2.,3.,4.],scaled_targets=np.linspace(-1,1,8).tolist(),
                    scaled_train=np.arange(80).reshape(8,10).tolist(),
                    scaled_cross=np.arange(40).reshape(4,10).tolist(),y_mean=1.,y_scale=.2,
                    predictions=[dict(label='ideal_fidelity',kind='kernel',gram=np.ones((8,8)).tolist(),
                                      cross=np.ones((4,8)).tolist())],
                    selector_resources={'objective':{'linear':[-14.]*10,
                      'pair':np.triu(np.ones((10,10))*4,1).tolist(),'constant':32.,'k':4,'penalty':2.}},
                    validation_years=[2007,2008,2009,2010])
        (output/'parent.json').write_text(json.dumps(parent))
        receipt=dict(parent_sha256=hashlib.sha256((output/'parent.json').read_bytes()).hexdigest(),
                     backend='synthetic_fixture',plan={'study':'fixture'},plan_sha256='fixture')
        (output/'prepared.json').write_text(json.dumps(receipt))
        counts=[{'0000':512} if i==j else {'0000':384,'0001':128}
                for i in range(8) for j in range(i,8)]
        counts += [{'0000':256,'0001':256} for _ in range(32)]
        counts += [{'0000001111':512},
                    {'0000':512},{'1111':512},{'0000000000':512},{'1111111111':512}]
        for arm in ['raw','dd_twirl']:
            (output/f'{arm}_counts.json').write_text(json.dumps({'counts':counts}))
            (output/f'{arm}_metrics.json').write_text(json.dumps({'usage':{'quantum_seconds':7.},
                     'timestamps':{'created':'2026-10-06T10:00:00Z','running':'2026-10-06T10:00:20Z',
                                   'finished':'2026-10-06T10:00:27Z'}}))
            (output/f'{arm}_submitted.json').write_text(json.dumps({'submission_roundtrip_seconds':.3}))
        return output

    def test_complete_counts_analyze_then_collect_without_refitting(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp);output=self.fixture(root)
            with patch('qiskit_aer.AerSimulator.run',side_effect=AssertionError('hardware data only')):
                result=analyze(root,output)
            self.assertEqual(result['hardware_jobs'],2)
            self.assertEqual(result['quantum_seconds_total'],14.)
            self.assertEqual(len(result['rows']),16)
            self.assertEqual(result['timings']['raw']['created_to_finished_seconds'],27.)
            with patch('wildfire_lab.mitigation_hardware_analysis.fit',side_effect=AssertionError('no refit')):
                self.assertEqual(analyze(root,output),result)

if __name__=='__main__':
    unittest.main()

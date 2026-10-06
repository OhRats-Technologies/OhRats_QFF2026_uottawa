"""Public collection must work without training, RNG, quantum execution or network."""
from contextlib import ExitStack
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from wildfire_lab.forest_publication import STUDIES, collect
from wildfire_lab.annual_workflow import run

ROOT = Path(__file__).resolve().parents[1]


class PublicTests(unittest.TestCase):
    def test_saved_collections_execute_no_models_or_sampling(self):
        guards = ['wildfire_lab.forest_models.Ridge.fit','wildfire_lab.forest_models.SVR.fit',
                  'wildfire_lab.forest_models.QSVR.fit','qiskit.quantum_info.Statevector.from_instruction',
                  'qiskit.primitives.StatevectorSampler.run','numpy.random.default_rng',
                  'urllib.request.urlopen']
        with ExitStack() as stack, tempfile.TemporaryDirectory() as temp:
            for name in guards:
                stack.enter_context(patch(name,side_effect=AssertionError('Collection executed '+name)))
            for name in STUDIES:
                output = Path(temp)/name
                receipt = collect(ROOT,name,output)
                self.assertEqual(receipt['status'],'verified')
                self.assertEqual(receipt['new_predictor_fits'],0)
                self.assertEqual(receipt['new_quantum_evaluations'],0)
                self.assertEqual(receipt['new_draws'],0)
                with self.assertRaises(FileExistsError):
                    collect(ROOT,name,output)

    def test_frontdoor_previews_without_execution(self):
        with patch('wildfire_lab.annual_workflow.subprocess.run') as execute:
            for name in ['forest','forest-orders','selector-scaling','forest-collect',
                         'forest-orders-collect','selector-scaling-collect','forest-source-collect']:
                result = run(Path('/no-inputs'),name,Path('/new'))
                self.assertFalse(result['executes'])
                self.assertIn('--output',result['command'])
        execute.assert_not_called()


if __name__=='__main__':
    unittest.main()

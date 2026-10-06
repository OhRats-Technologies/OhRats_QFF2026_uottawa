"""The annual front door previews training-only commands without executing."""

from pathlib import Path
import unittest
import tempfile
import json
import hashlib
from zipfile import ZipFile
from unittest.mock import patch
from wildfire_lab.annual_workflow import run


class AnnualWorkflowTests(unittest.TestCase):
    def test_quantum_preview_preserves_dataset_and_width(self):
        with patch('wildfire_lab.annual_workflow.subprocess.run') as launch:
            result = run(Path('/repo'), 'quantum', Path('/new'), Path('/annual.csv'), 10)
        launch.assert_not_called()
        self.assertEqual(result['command'][-4:], ['--dataset', '/annual.csv', '--qubits', '10'])
        self.assertFalse(result['executes'])


    def fixture_bundle(self, root):
        (root / 'docs/data').mkdir(parents=True)
        bundle = root / 'docs/data/evidence.zip'
        with ZipFile(bundle, 'w') as archive:
            archive.writestr('training.json', '{}')
        index = dict(bundle='docs/data/evidence.zip', sha256=hashlib.sha256(bundle.read_bytes()).hexdigest(), members=1)
        (root / 'docs/data/annual_final_bundle.json').write_text(json.dumps(index))
        return bundle

    def test_collection_preview_reads_no_bundle_and_creates_no_directory(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            output = root / 'new'
            result = run(root, 'collect', output)
            self.assertFalse(output.exists())
            self.assertFalse(result['executes'])

    def test_changed_bundle_stops_before_extraction(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            bundle = self.fixture_bundle(root)
            bundle.write_bytes(b'changed')
            with self.assertRaisesRegex(ValueError, 'bundle changed'):
                run(root, 'collect', root / 'new', execute=True)
            self.assertFalse((root / 'new').exists())

    def test_collection_preserves_existing_records_and_calls_no_runner(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            self.fixture_bundle(root)
            receipt = dict(prediction_records_checked=83, kernel_records_checked=24)
            with patch('wildfire_lab.annual_final_audit.collect', return_value=receipt) as audit, \
                 patch('wildfire_lab.annual_workflow.subprocess.run') as runner:
                result = run(root, 'collect', root / 'new', execute=True)
                audit.assert_called_once()
                runner.assert_not_called()
                self.assertEqual(result['predictor_fits'], 0)
                original = (root / 'new/audit.json').read_bytes()
                with self.assertRaises(FileExistsError):
                    run(root, 'collect', root / 'new', execute=True)
                self.assertEqual((root / 'new/audit.json').read_bytes(), original)


if __name__ == '__main__':
    unittest.main()

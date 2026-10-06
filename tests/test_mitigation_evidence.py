"""Public mitigation evidence and explicit historical environment qualification."""
from pathlib import Path
import hashlib
import importlib.util
import json
import tempfile
import unittest
from unittest.mock import patch
from zipfile import ZipFile
from wildfire_lab.mitigation_collect import collect

ROOT=Path(__file__).resolve().parents[1]

class EvidenceTests(unittest.TestCase):
    def test_public_collect_without_states_draws_or_fits(self):
        summary=json.loads((ROOT/'docs/results/pipeline-mitigation.json').read_text())
        bundle=ROOT/summary['bundle']
        self.assertEqual(hashlib.sha256(bundle.read_bytes()).hexdigest(),summary['bundle_sha256'])
        with tempfile.TemporaryDirectory() as temp:
            with ZipFile(bundle) as archive:
                archive.extractall(temp)
            with patch('qiskit_aer.AerSimulator.run',side_effect=AssertionError('simulation forbidden')), \
                 patch('qiskit.quantum_info.Statevector.from_instruction',side_effect=AssertionError('new states forbidden')), \
                 patch('numpy.random.default_rng',side_effect=AssertionError('new draws forbidden')), \
                 patch('qiskit_machine_learning.algorithms.QSVR.fit',side_effect=AssertionError('fitting forbidden')), \
                 patch('sklearn.linear_model.Ridge.fit',side_effect=AssertionError('fitting forbidden')):
                result=collect(ROOT,Path(temp))
            self.assertEqual(result['prediction_records_checked'],76)
            self.assertEqual(result['measured_count_paths_checked'],3933)
            self.assertEqual(result['predictor_fits'],0)
            manifest=Path(temp)/'manifest.json'
            manifest.write_text('{}')
            # A missing manifest is not proof; this fixture preserves the content pin below.
            evidence=Path(temp)/'evidence.json'
            evidence.write_text('{}')
            manifest.write_text(json.dumps({'evidence.json':'bad'}))
            with self.assertRaisesRegex(ValueError,'evidence'):
                collect(ROOT,Path(temp))

    def verifier(self):
        spec=importlib.util.spec_from_file_location('ordering_public',ROOT/'scripts/context/ordering_public.py')
        module=importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module.verify_order

    def read(self,path):
        return json.loads((ROOT/path).read_text())

    def sha(self,path):
        return hashlib.sha256((ROOT/path).read_bytes()).hexdigest()

    def test_environment_difference_is_reported_not_certified(self):
        rows=[]
        self.verifier()(self.read,self.sha,lambda *args:rows.append(args))
        result=rows[0][2]
        self.assertFalse(result['current_environment_matches_original'])
        self.assertEqual(set(result['environment_manifest_changes']),{'pyproject.toml','uv.lock'})

    def test_changed_scientific_source_still_rejected(self):
        def changed(path):
            return 'bad' if path=='scripts/context/ordering.py' else self.sha(path)
        with self.assertRaises(AssertionError):
            self.verifier()(self.read,changed,lambda *args:None)

if __name__=='__main__':
    unittest.main()


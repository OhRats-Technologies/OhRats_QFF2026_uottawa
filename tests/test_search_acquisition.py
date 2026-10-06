"""Never duplicate accepted/ambiguous acquisition intents or overspend reserve."""
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch, MagicMock
from wildfire_lab.search_acquisition import submit


class AcquisitionTests(unittest.TestCase):
    def fixture(self, root):
        (root/'experiments').mkdir()
        (root/'experiments/plan.json').write_text('{}')
        output = root/'private'
        output.mkdir()
        (output/'pool-20').mkdir()
        receipt = dict(plan={'backend': 'fake', 'remaining_reserve_seconds': 210},
                       plan_path='experiments/plan.json', plan_sha256='hash', code_sha256={},
                       jobs=[dict(label='pool-20', cap_seconds=30)])
        (output/'prepared.json').write_text(json.dumps(receipt))
        return output

    def test_existing_ambiguous_intent_blocks_all_submissions(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            output = self.fixture(root)
            (output/'pool-20/submission_intent.json').write_text('{}')
            svc = MagicMock()
            svc.usage.return_value = {'usage_remaining_seconds': 404}
            with patch('wildfire_lab.search_acquisition.sha', return_value='hash'), \
                 patch('wildfire_lab.search_acquisition.service', return_value=svc), \
                 patch('wildfire_lab.search_acquisition.Sampler') as sampler:
                with self.assertRaisesRegex(AssertionError, 'Existing intent'):
                    submit(root, output)
                sampler.assert_not_called()
                svc.backend.assert_not_called()

    def test_guard_reserves_future_stages_before_acceptance(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            output = self.fixture(root)
            svc = MagicMock()
            svc.usage.return_value = {'usage_remaining_seconds': 200}
            with patch('wildfire_lab.search_acquisition.sha', return_value='hash'), \
                 patch('wildfire_lab.search_acquisition.service', return_value=svc), \
                 patch('wildfire_lab.search_acquisition.Sampler') as sampler:
                with self.assertRaises(AssertionError):
                    submit(root, output)
                sampler.assert_not_called()
                self.assertFalse((output/'pool-20/submission_intent.json').exists())


if __name__ == '__main__':
    unittest.main()

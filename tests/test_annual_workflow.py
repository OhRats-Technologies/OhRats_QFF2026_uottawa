"""The annual front door previews training-only commands without executing."""

from pathlib import Path
import unittest
from unittest.mock import patch
from wildfire_lab.annual_workflow import run


class AnnualWorkflowTests(unittest.TestCase):
    def test_quantum_preview_preserves_dataset_and_width(self):
        with patch('wildfire_lab.annual_workflow.subprocess.run') as launch:
            result = run(Path('/repo'), 'quantum', Path('/new'), Path('/annual.csv'), 10)
        launch.assert_not_called()
        self.assertEqual(result['command'][-4:], ['--dataset', '/annual.csv', '--qubits', '10'])
        self.assertFalse(result['executes'])


if __name__ == '__main__':
    unittest.main()

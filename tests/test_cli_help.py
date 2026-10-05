import contextlib
import io
import runpy
import sys
import unittest
from pathlib import Path
from unittest.mock import patch
import scripts.build_operational_pilot


class CLIHelpTests(unittest.TestCase):
    def test_operational_help_exits_before_production_reads(self):
        script=Path(scripts.build_operational_pilot.__file__)
        with patch.object(sys,'argv',[str(script),'--help']), \
             patch.object(Path,'read_bytes',side_effect=AssertionError('Help read production inputs')), \
             contextlib.redirect_stdout(io.StringIO()) as output:
            with self.assertRaises(SystemExit) as exit:
                runpy.run_path(str(script),run_name='__main__')
        self.assertEqual(exit.exception.code,0)
        self.assertIn('usage:',output.getvalue())

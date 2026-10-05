import json
import subprocess
import tempfile
import unittest
from pathlib import Path
from wildfire_lab.final_gate import validate_plan,reserve


class FinalGateTests(unittest.TestCase):
    def test_draft_and_uncommitted_changes_cannot_open_test(self):
        plan=dict(status='draft',train_years=[1988,2018],test_years=[2019,2024],hardware_default=False,cover_policy={'mode':'fixed_historical'},training_dataset_fingerprint='fixed',training_data_sha256='a'*64,threshold_ha=10)
        with self.assertRaisesRegex(ValueError,'draft'):validate_plan(plan)
        plan['status']='frozen_final'
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp);subprocess.run(['git','init','-q',str(root)],check=True)
            path=root/'plan.json';recipe=root/'recipe.py';path.write_text(json.dumps(plan));recipe.write_text('pass\n')
            subprocess.run(['git','add','plan.json','recipe.py'],cwd=root,check=True)
            subprocess.run(['git','-c','user.name=Test','-c','user.email=test@example.invalid','commit','-qm','frozen'],cwd=root,check=True)
            recipe.write_text('print(1)\n')
            with self.assertRaisesRegex(ValueError,'Commit final'):reserve(path,root/'cache',root,[recipe])
            self.assertFalse((root/'cache/intent.json').exists())
            recipe.write_text('pass\n');reserve(path,root/'cache',root,[recipe])
            with self.assertRaises(FileExistsError):reserve(path,root/'cache',root,[recipe])
            plan['training_dataset_fingerprint']='another';path.write_text(json.dumps(plan))
            with self.assertRaisesRegex(ValueError,'Commit final'):reserve(path,root/'cache',root,[recipe])

import json
import tempfile
import unittest
from pathlib import Path
from scripts.pipeline import normalized, reserve, status
from wildfire_lab.followup_status import summarize


class PipelineTests(unittest.TestCase):
    def test_followup_status_preserves_repairs_and_does_not_imply_live_runtime(self):
        with tempfile.TemporaryDirectory() as temp:
            cache=Path(temp)
            for name,status_value in [('library-followup','failed_preserved'),('library-followup-v3','complete'),
                                      ('kernel-ridge','running'),('seasonal-baseline','complete'),('constrained-selection','complete'),('local-geometry','complete'),('tangent-prediction','complete'),('landmark-shot-ridge','complete'),('proxy-alignment','complete')]:
                directory=cache/name;directory.mkdir();(directory/'intent.json').write_text('{}')
                (directory/'outcome.json').write_text(json.dumps(dict(status=status_value,seeds=[{}],seconds=2)))
            pending=cache/'quantum-landmarks';pending.mkdir();(pending/'intent.json').write_text('{}')
            diagnostic=cache/'shot-feasibility';diagnostic.mkdir()
            (diagnostic/'outcome.json').write_text(json.dumps(dict(status='complete',conditions=[{},{}],seconds=1)))
            broken=cache/'kernel-convergence';broken.mkdir();(broken/'outcome.json').write_text('{')
            private=cache/'private-hardware';private.mkdir();(private/'outcome.json').write_text('private sentinel')
            report=summarize(cache)
            self.assertEqual(report['record_count'],12)
            self.assertFalse(report['runtime_verified'])
            self.assertEqual(report['by_saved_status'],dict(failed_preserved=1,complete=8,running=1,
                intent_without_outcome=1,unreadable=1))
            self.assertNotIn('private',json.dumps(report))
            self.assertEqual((private/'outcome.json').read_text(),'private sentinel')
            self.assertEqual(next(r for r in report['records'] if r['namespace']=='shot-feasibility')['completed_condition_records'],2)

    def test_status_counts_reservations_once_and_distinguishes_final_opening(self):
        with tempfile.TemporaryDirectory() as temp:
            cache=Path(temp);study=cache/'experiments/study';study.mkdir(parents=True)
            for name in ['one','two','three','four']:(study/f'attempt-{name}.json').write_text('{}')
            (study/'attempt-one-outcome.json').write_text('{"status":"complete"}')
            (study/'attempt-two-outcome.json').write_text('{"status":"failed"}')
            (study/'attempt-four-outcome.json').write_text('{')
            report=status(cache)
            self.assertEqual(report['reserved_attempts'],4)
            self.assertEqual(report['attempts_by_status'],dict(complete=1,failed=1,pending=1,unreadable=1))
            self.assertEqual(report['final_evaluation_status'],'unopened')
            final=cache/'final-test';final.mkdir();(final/'intent.json').write_text('{}')
            self.assertEqual(status(cache)['final_evaluation_status'],'opened_without_outcome')
            (final/'outcome.json').write_text('{"status":"complete"}')
            self.assertEqual(status(cache)['final_evaluation_status'],'complete')
            (final/'outcome.json').write_text('{')
            self.assertEqual(status(cache)['final_evaluation_status'],'unreadable')

    def test_missing_zero_identity_and_suspect_days(self):
        row = dict(Clim_ID="A001", Stn_Name="Station", Prov_or_Ter="ON", Long="-78", Lat="45", Tm="NA", P="0", DwTm="32")
        result = normalized(row, 1988, 2, "train")
        self.assertEqual(result["climate_id"], "A001")
        self.assertEqual(result["mean_temp_c"], "")
        self.assertEqual(result["total_precip_mm"], 0.)
        self.assertIn("suspect_day_count", result["quality_flags"])
        row["Lat"] = "nan"
        self.assertIn("invalid_location", normalized(row, 1988, 2, "train")["quality_flags"])

    def test_reservation_budget_parent_and_sealed_test(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            path = root / "plan.json"
            plan = dict(id="study", hypothesis="test", research_model="gpt-6.1-sol", primary_metric="pending", final_test_sealed=True, screen_max_proposals=2)
            path.write_text(json.dumps(plan))
            first = reserve(path, root / "cache")
            second = reserve(path, root / "cache", first.stem)
            self.assertEqual(json.loads(second.read_text())["parent"], first.stem)
            self.assertIsNone(json.loads(first.read_text())["actual_model"])
            with self.assertRaisesRegex(ValueError, "budget"):
                reserve(path, root / "cache")
            with self.assertRaisesRegex(ValueError, "parent"):
                reserve(path, root / "cache", "../../outside")
            plan["final_test_sealed"] = False
            path.write_text(json.dumps(plan))
            with self.assertRaisesRegex(ValueError, "sealed"):
                reserve(path, root / "cache")
            plan['final_test_sealed']=True;path.write_text(json.dumps(plan))
            final=root/'cache/final-test';final.mkdir();(final/'intent.json').write_text('{}')
            with self.assertRaisesRegex(ValueError,'reservations are closed'):reserve(path,root/'cache')

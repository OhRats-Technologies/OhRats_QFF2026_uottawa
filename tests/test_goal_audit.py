import copy
import unittest
import hashlib
import json
import tempfile
from datetime import timedelta
from pathlib import Path

from wildfire_lab.goal_handoff import ARTIFACTS, DEADLINE, deadline_handoff

from scripts.audit_goal import measured_library_queries, selection_stability


class GoalAuditTests(unittest.TestCase):
    def test_predictor_reuse_is_not_extra_selection_replication(self):
        rows = [
            dict(group="selector", seed=s, features=features, predictor=p)
            for s, features in [(1, ["a", "b"]), (2, ["a", "c"]), (3, ["a", "b"])]
            for p in ("linear", "rbf", "quantum")
        ]
        result = selection_stability(rows, 2)["selector"]
        self.assertEqual(result["seeds"], 3)
        self.assertAlmostEqual(result["mean_pairwise_jaccard"], 5 / 9)
        self.assertEqual(result["feature_seed_counts"], dict(a=3, b=2, c=1))
        changed = copy.deepcopy(rows)
        changed[-1]["features"] = ["a", "c"]
        with self.assertRaisesRegex(ValueError, "disagree"):
            selection_stability(changed, 2)

    def test_shared_psd_measurements_are_not_double_counted(self):
        raw = dict(pair_circuits=10, synthetic_shots=100)
        repaired = dict(raw, shared_measurements=True)
        exact = dict(pair_circuits=10, synthetic_shots=None)
        report = measured_library_queries([dict(kernel_rows=[raw, repaired, exact])])
        self.assertEqual(report, dict(pair_circuits=20, synthetic_shots=100))


class DeadlineHandoffTests(unittest.TestCase):
    def test_time_alone_never_completes_handoff(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            before = deadline_handoff(root, DEADLINE - timedelta(seconds=1))
            after = deadline_handoff(root, DEADLINE + timedelta(seconds=1))
            self.assertFalse(before["published"])
            self.assertFalse(after["published"])
            self.assertIn("publish", after["open_item"])

    def test_handoff_requires_complete_unchanged_artifacts_and_valid_time(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            for name in ARTIFACTS:
                path = root / name
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text("fixture")
            saved = dict(
                status="completed_goal_handoff",
                completed_utc=DEADLINE.isoformat(),
                files_sha256={
                    name: hashlib.sha256((root / name).read_bytes()).hexdigest()
                    for name in ARTIFACTS
                },
            )
            path = root / "docs/data/goal_handoff.json"
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(json.dumps(saved))
            self.assertTrue(deadline_handoff(root, DEADLINE)["published"])
            saved["completed_utc"] = (DEADLINE - timedelta(seconds=1)).isoformat()
            path.write_text(json.dumps(saved))
            with self.assertRaisesRegex(ValueError, "completion time"):
                deadline_handoff(root, DEADLINE)
            saved["completed_utc"] = DEADLINE.isoformat()
            path.write_text(json.dumps(saved))
            (root / "docs/REPORT.md").write_text("changed")
            with self.assertRaisesRegex(ValueError, "Changed handoff artifact"):
                deadline_handoff(root, DEADLINE)

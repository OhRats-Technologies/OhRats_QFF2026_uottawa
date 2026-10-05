import json
import tempfile
import unittest
from pathlib import Path

from wildfire_lab.evidence import write_summary


class EvidenceSummaryTests(unittest.TestCase):
    def test_combination_summary_keeps_predictors_separate_and_balances_folds(self):
        rows = [
            dict(
                selector="l1",
                predictor=predictor,
                fold=fold,
                status="complete",
                metric=dict(average_precision=ap, prevalence=0.1),
            )
            for predictor, fold, ap in [
                ("logistic", [1, 2], 0.2),
                ("logistic", [1, 2], 0.4),
                ("logistic", [3, 4], 0.5),
                ("ZZ", [1, 2], 0.8),
                ("ZZ", [3, 4], 0.6),
            ]
        ]
        record = dict(
            status="complete",
            rows=rows,
            plan=dict(id="fixture"),
            id="attempt-fixture",
            axis="combinations",
            seconds=1,
            quality_checks=dict(final_test_sealed=True),
        )
        with tempfile.TemporaryDirectory() as tmp:
            outcome, summary = Path(tmp) / "outcome.json", Path(tmp) / "summary.json"
            outcome.write_text(json.dumps(record))
            before = outcome.read_bytes()
            write_summary([outcome], summary)
            models = json.loads(summary.read_text())["studies"][0]["models"]
            scores = {
                model["name"]: model["mean_average_precision"] for model in models
            }
            self.assertEqual(set(scores), {"l1 / logistic", "l1 / ZZ"})
            self.assertAlmostEqual(scores["l1 / logistic"], 0.4)
            self.assertAlmostEqual(scores["l1 / ZZ"], 0.7)
            self.assertEqual(outcome.read_bytes(), before)
            for row in record["rows"]:
                row["group"] = row.pop("selector")
            outcome.write_text(json.dumps(record))
            write_summary([outcome], summary)
            grouped = json.loads(summary.read_text())["studies"][0]["models"]
            self.assertEqual(grouped, models)

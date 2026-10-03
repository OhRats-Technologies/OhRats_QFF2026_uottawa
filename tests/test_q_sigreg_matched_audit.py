import json
import unittest
from pathlib import Path

from scripts.q_sigreg_matched_audit import (
    corrected_untrained,
    holm_adjust,
    recompute_stats,
)


class MatchedStudyAuditTests(unittest.TestCase):
    def test_holm_controls_three_reported_comparisons(self):
        actual = holm_adjust([0.556640625, 0.048828125, 0.001953125])
        self.assertEqual(actual, [0.556640625, 0.09765625, 0.005859375])
        self.assertEqual(holm_adjust([0.9, 0.9, 0.9]), [1.0, 1.0, 1.0])

    def test_paired_statistics_match_saved_evidence(self):
        source = json.loads(
            Path("results/q_sigreg/matched_10seed_results.json").read_text()
        )
        saved = json.loads(
            Path("artifacts/q-sigreg-matched-audit-20261003/results.json").read_text()
        )
        self.assertEqual(recompute_stats(source), saved["paired_statistics"])

    def test_corrected_probe_trains_classifier_preserves_encoder(self):
        import torch

        torch.set_num_threads(1)
        result = corrected_untrained(2026)
        self.assertGreater(result["probes"]["probe_100pct"], 95)
        self.assertEqual(len(result["probe_training_audit"]), 4)
        for record in result["probe_training_audit"]:
            self.assertEqual(record["original_requested_epochs"], 0)
            self.assertEqual(record["actual_classifier_epochs"], 40)
            self.assertTrue(record["encoder_unchanged"])


if __name__ == "__main__":
    unittest.main()

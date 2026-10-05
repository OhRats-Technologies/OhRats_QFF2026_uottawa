import hashlib
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from wildfire_lab import workflow


class WorkflowTests(unittest.TestCase):
    def test_end_to_end_screen_receives_prepared_dataset_and_exports_summary(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            dataset = root / "derived"
            outcome = root / "attempt-outcome.json"
            plan = root / "plan.json"
            with (
                patch.object(
                    workflow, "doctor", return_value=dict(ready=True, mismatched=[])
                ),
                patch.object(
                    workflow, "prepare", return_value=dict(dataset=str(dataset))
                ),
                patch("scripts.run_pilot_screen.run", return_value=outcome) as screen,
                patch("wildfire_lab.evidence.write_summary") as summary,
            ):
                result = workflow.run(root, True, plan, "combinations")
                screen.assert_called_once_with(plan, dataset, "combinations")
                summary.assert_called_once_with(
                    [outcome], root / "summary-attempt-outcome.json"
                )
                self.assertEqual(result["outcome"], str(outcome))
                self.assertFalse(Path(result["summary"]).match("attempt-*.json"))

    def test_final_intent_blocks_end_to_end_training_before_any_preparation(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            directory = root / ".cache/wildfire/final-test"
            directory.mkdir(parents=True)
            (directory / "intent.json").write_text("{}")
            with (
                patch.object(workflow, "prepare") as prepare,
                patch.object(workflow, "acquire") as acquire,
            ):
                with self.assertRaisesRegex(ValueError, "discovery is closed"):
                    workflow.run(root, True, root / "plan.json", "prediction")
                prepare.assert_not_called()
                acquire.assert_not_called()

    def test_preparation_requires_recoverable_committed_recipe(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            for name in workflow.RECIPES:
                path = root / name
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_bytes(b"working tree")
            with patch(
                "wildfire_lab.workflow.subprocess.check_output",
                side_effect=["commit\n", b"different committed bytes"],
            ):
                with self.assertRaisesRegex(ValueError, "Commit preparation recipe"):
                    workflow.recipe_commit(root)

    def make_inputs(self, root):
        directory = root / "docs/data"
        directory.mkdir(parents=True)
        raw = root / "weather.csv"
        raw.write_text("fixture weather")
        digest = hashlib.sha256(raw.read_bytes()).hexdigest()
        receipt = root / "weather.json"
        receipt.write_text(json.dumps(dict(status="downloaded", sha256=digest)))
        crop_receipt = dict(
            crop_sha256="crop",
            archive_sha256="archive",
            requested_bbox_wgs84=[1, 2, 3, 4],
        )
        crop = root / "crop.json"
        crop.write_text(json.dumps(crop_receipt))
        index = dict(
            weather_years=[
                dict(inputs=[dict(file=raw.name, sha256=digest, sidecar=receipt.name)])
            ],
            other_inputs=[
                dict(
                    file=crop.name,
                    sha256=hashlib.sha256(crop.read_bytes()).hexdigest(),
                    original_receipt=crop_receipt,
                )
            ],
            training_csv_sha256="training",
        )
        (directory / "reproduction_inputs.json").write_text(json.dumps(index))
        return raw, receipt, crop

    def test_doctor_distinguishes_data_changes_from_receipt_metadata(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            raw, receipt, crop = self.make_inputs(root)
            self.assertTrue(workflow.doctor(root, True)["ready"])
            data = json.loads(crop.read_text())
            data["retrieved_utc"] = "new acquisition"
            crop.write_text(json.dumps(data))
            result = workflow.doctor(root, True)
            self.assertTrue(result["ready"])
            self.assertEqual(result["provenance_differences"], [crop.name])
            raw.write_text("changed weather")
            self.assertEqual(workflow.doctor(root, True)["mismatched"], [raw.name])
            receipt.unlink()
            self.assertEqual(workflow.doctor(root)["missing"], [receipt.name])

    def test_run_preview_cannot_download_or_prepare(self):
        with (
            patch.object(workflow, "acquire", side_effect=AssertionError("download")),
            patch.object(workflow, "prepare", side_effect=AssertionError("prepare")),
        ):
            result = workflow.run(Path("unused"))
            self.assertFalse(result["executes"])
            self.assertFalse(result["opens_final_test"])

    def test_prepare_hands_actual_dataset_to_cover_and_checks_table(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.make_inputs(root)
            weather_path = root / "derived-weather"
            cover_path = root / "derived-cover"
            with (
                patch.object(workflow, "recipe_commit", return_value=("fixture", {})),
                patch.object(workflow, "doctor", return_value=dict(ready=True)),
                patch(
                    "scripts.build_historical_features.build",
                    return_value=(weather_path, {}),
                ) as weather,
                patch(
                    "scripts.add_woodland_features.build",
                    return_value=(cover_path, dict(rows=2, data_sha256="training")),
                ) as cover,
            ):
                result = workflow.prepare(root)
                weather.assert_called_once_with((1, 2, 3))
                cover.assert_called_once_with(weather_path, fixed_year=1984)
                self.assertEqual(result["dataset"], str(cover_path))
                cover.return_value = (cover_path, dict(rows=2, data_sha256="changed"))
                with self.assertRaisesRegex(ValueError, "table differs"):
                    workflow.prepare(root)

    def test_source_mismatch_stops_run_before_preparation(self):
        with (
            patch.object(
                workflow, "doctor", return_value=dict(ready=False, mismatched=[])
            ),
            patch.object(workflow, "acquire", return_value=dict(ready=False)),
            patch.object(workflow, "prepare") as prepare,
        ):
            with self.assertRaisesRegex(ValueError, "sources differ"):
                workflow.run(Path("unused"), execute=True)
            prepare.assert_not_called()

    def test_verified_existing_sources_skip_acquisition(self):
        with (
            patch.object(
                workflow, "doctor", return_value=dict(ready=True, mismatched=[])
            ),
            patch.object(workflow, "acquire") as acquire,
            patch.object(workflow, "prepare", return_value=dict(dataset="fixture")),
        ):
            self.assertEqual(
                workflow.run(Path("unused"), execute=True), dict(dataset="fixture")
            )
            acquire.assert_not_called()

    def test_collection_requires_saved_records_and_never_starts_runners(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            output = root / "collected"
            with self.assertRaisesRegex(FileNotFoundError, "Saved run records"):
                workflow.collect(root, output)
            self.assertFalse(output.exists())
            for namespace in (
                "final-test",
                "policy-evolution-development",
                "policy-evolution-confirmation",
            ):
                directory = root / ".cache/wildfire" / namespace
                directory.mkdir(parents=True)
                (directory / "outcome.json").write_text("{}")
            with patch("wildfire_lab.workflow.subprocess.run") as execute:
                result = workflow.collect(root, output)
                commands = [call.args[0] for call in execute.call_args_list]
                self.assertEqual(len(commands), 4)
                self.assertTrue(all("--output" in command for command in commands))
                self.assertEqual(commands[2][2], "collect")
                self.assertFalse(
                    any(
                        "run_final_evaluation" in " ".join(command)
                        for command in commands
                    )
                )
                self.assertEqual(result["model_fits"], 0)
                with self.assertRaises(FileExistsError):
                    workflow.collect(root, output)


if __name__ == "__main__":
    unittest.main()

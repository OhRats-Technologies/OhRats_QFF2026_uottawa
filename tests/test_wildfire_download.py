import csv
import io
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from scripts.download_wildfires import download


def page(*rows):
    stream = io.StringIO()
    writer = csv.writer(stream)
    writer.writerow(["id", "agency_code", "national_fire_id", "status_year", "situation_report_date"])
    writer.writerows(rows)
    return stream.getvalue()


class DownloadTests(unittest.TestCase):
    def test_pages_preserve_updates_and_raw_values(self):
        calls = []
        pages = iter([page(["1", "ON", "fire-a", "2025", "2025-06-01T12:00:00"], ["2", "ON", "fire-a", "2025", "2025-06-02T12:00:00"]), page(["3", "ON", "fire-b", "2025", "2025-06-02T12:00:00"])])
        def fetch(url):
            calls.append(url)
            return next(pages)
        with tempfile.TemporaryDirectory() as root, patch("scripts.download_wildfires.PAGE_SIZE", 2):
            output = Path(root) / "snapshot"
            result = download(output, fetch=fetch)
            self.assertEqual(result["rows"], 3)
            self.assertEqual(result["distinct_fire_ids"], 2)
            self.assertEqual(result["distinct_report_dates_by_status_year"], {"2025": 2})
            self.assertIn("startIndex=2", calls[1])
            self.assertIn("2025-06-01T12:00:00", (output / "reports.csv").read_text())
            with self.assertRaises(FileExistsError):
                download(output, fetch=lambda _: self.fail("Must not fetch when output exists"))

    def test_repeated_updates_reject_snapshot(self):
        with tempfile.TemporaryDirectory() as root, patch("scripts.download_wildfires.PAGE_SIZE", 1):
            output = Path(root) / "snapshot"
            with self.assertRaisesRegex(ValueError, "repeated update ID"):
                download(output, fetch=lambda _: page(["1", "ON", "fire-a", "2025", "2025-06-01"]))
            self.assertFalse(output.exists())

    def test_invalid_response_or_wrong_agency_reject_snapshot(self):
        for response in ("<ExceptionReport>failed</ExceptionReport>", page(["1", "BC", "fire-a", "2025", "2025-06-01"])):
            with self.subTest(response=response), tempfile.TemporaryDirectory() as root:
                output = Path(root) / "snapshot"
                with self.assertRaises(ValueError):
                    download(output, fetch=lambda _: response)
                self.assertFalse(output.exists())

    def test_changing_schema_reject_snapshot(self):
        pages = iter([page(["1", "ON", "fire-a", "2025", "2025-06-01"]), "id,agency_code,national_fire_id,status_year,situation_report_date,extra\n"])
        with tempfile.TemporaryDirectory() as root, patch("scripts.download_wildfires.PAGE_SIZE", 1):
            output = Path(root) / "snapshot"
            with self.assertRaisesRegex(ValueError, "schema changed"):
                download(output, fetch=lambda _: next(pages))
            self.assertFalse(output.exists())

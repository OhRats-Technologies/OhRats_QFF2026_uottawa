"""Geometry integrity, physical units, and model/measurement boundary checks."""

import base64
import gzip
import hashlib
import json
from pathlib import Path
import re
import struct
import unittest
import numpy as np
from flybrain.morphology import parse_swc, decode_mesh
from flybrain.data import REPO


class MorphologyTests(unittest.TestCase):
    def test_swc_units_and_unsorted_parent_ids(self):
        p, e, r = parse_swc("9 3 125 250 375 10 4\n4 1 0 0 0 25 -1")
        np.testing.assert_allclose(p[0], [1, 2, 3])
        np.testing.assert_array_equal(e, [[1, 0]])
        np.testing.assert_allclose(r, [0.08, 0.2])

    def test_swc_rejects_broken_and_cyclic_topology(self):
        for s in [
            "1 1 0 0 0 1 2",
            "1 1 0 0 0 1 2\n2 1 0 0 0 1 1",
            "1 1 0 0 0 1 -1\n1 1 0 0 0 1 -1",
            "1 1 nan 0 0 1 -1",
        ]:
            with self.subTest(s=s), self.assertRaises(ValueError):
                parse_swc(s)

    def test_mesh_nm_conversion_and_topology(self):
        v = np.array([[0, 0, 0], [5000, 0, 0], [0, 5000, 0]], dtype="<f4")
        f = np.array([[0, 1, 2]], dtype="<u4")
        out, faces = decode_mesh(struct.pack("<I", 3) + v.tobytes() + f.tobytes())
        np.testing.assert_allclose(np.sort(out, axis=0), np.sort(v / 1000, axis=0))
        self.assertEqual(faces.shape, (1, 3))
        self.assertEqual(set(faces.ravel()), {0, 1, 2})

    def test_mesh_rejects_truncation_and_invalid_indices(self):
        for blob in [
            b"",
            struct.pack("<I", 3) + bytes(36),
            struct.pack("<I", 3) + bytes(36) + struct.pack("<III", 0, 1, 5),
        ]:
            with self.subTest(blob=blob), self.assertRaises(ValueError):
                decode_mesh(blob)

    def test_committed_snapshot_is_finite_with_valid_edges(self):
        path = REPO / "datasets/fly/morphology/geometry.json"
        manifest = json.loads((path.parent / "manifest.json").read_text())
        self.assertEqual(
            hashlib.sha256(path.read_bytes()).hexdigest(), manifest["geometry_sha256"]
        )
        geometry = json.loads(path.read_text())
        self.assertEqual(len(geometry["neurons"]), manifest["neuron_count"])
        self.assertEqual(
            len({n["id"] for n in geometry["neurons"]}), manifest["neuron_count"]
        )
        self.assertEqual(sum(n["group"] is not None for n in geometry["neurons"]), 80)
        for n in geometry["neurons"]:
            p = np.array(n["points"]).reshape(-1, 3)
            e = np.array(n["edges"]).reshape(-1, 2)
            self.assertTrue(np.isfinite(p).all())
            self.assertTrue((e >= 0).all())
            self.assertTrue((e < len(p)).all())
        for r in geometry["regions"]:
            p = np.array(r["vertices"]).reshape(-1, 3)
            f = np.array(r["faces"]).reshape(-1, 3)
            self.assertTrue(np.isfinite(p).all())
            self.assertTrue((f >= 0).all())
            self.assertTrue((f < len(p)).all())

    def test_offline_payload_matches_geometry_and_returned_counts(self):
        html = (REPO / "explorer/index.html").read_text()
        payload = re.search(r'<script id="payload"[^>]*>([^<]+)</script>', html).group(
            1
        )
        data = json.loads(gzip.decompress(base64.b64decode(payload)))
        original = json.loads(
            (REPO / "datasets/fly/morphology/geometry.json").read_text()
        )
        self.assertEqual(data["anatomy"], original)
        public = json.loads(
            (
                REPO / "artifacts/sprint-20261003/hardware-counts/hardware.json"
            ).read_text()
        )
        self.assertEqual(data["hardware"], public)
        for case in data["hardware"]["cases"]:
            counts = case["counts"]
            self.assertEqual(sum(counts.values()), 1024)
            self.assertEqual(
                case["observed"],
                [counts.get(format(i, "03b"), 0) / 1024 for i in range(8)],
            )
        for lesion, model in data["models"].items():
            for kind in ["quantum", "classical"]:
                p = np.array(model[kind])
                self.assertEqual(p.shape, (81, 8, 8))
                np.testing.assert_allclose(p.sum(axis=1), 1, atol=5e-8)
                self.assertTrue((p >= 0).all())
                np.testing.assert_allclose(p[0], np.eye(8), atol=1e-8)
                if lesion != "-1":
                    np.testing.assert_allclose(
                        p[:, :, int(lesion)],
                        np.tile(np.eye(8)[:, int(lesion)], (81, 1)),
                        atol=1e-8,
                    )
        q = np.array(data["models"]["-1"]["quantum"])[-1, :, 0]
        c = np.array(data["models"]["-1"]["classical"])[-1, :, 0]
        self.assertAlmostEqual(np.abs(q - c).sum() / 2, 0.4034910318148942, places=7)
        manifest = json.loads((REPO / "explorer/manifest.json").read_text())
        self.assertEqual(
            hashlib.sha256(html.encode()).hexdigest(), manifest["html_sha256"]
        )
        self.assertNotIn("__SCRIPT__", html)
        self.assertNotRegex(html, r"<script[^>]+src=")


if __name__ == "__main__":
    unittest.main()

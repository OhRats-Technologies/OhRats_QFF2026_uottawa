"""Draw the full official Ontario boundary for the console; no raster inference."""

import hashlib
import json
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def simplify(points, tolerance=4000):
    if len(points) < 3:
        return points
    a, b = points[0], points[-1]
    dx, dy = b[0] - a[0], b[1] - a[1]
    norm = math.hypot(dx, dy)
    distances = [
        abs(dx * (a[1] - p[1]) - (a[0] - p[0]) * dy) / norm if norm else math.dist(p, a)
        for p in points
    ]
    i = max(range(len(points)), key=distances.__getitem__)
    if distances[i] <= tolerance:
        return [a, b]
    return simplify(points[: i + 1], tolerance)[:-1] + simplify(points[i:], tolerance)


def build():
    source = ROOT / "data/raw/boundaries/ontario-2021.geojson"
    geometry = json.loads(source.read_text())["features"][0]["geometry"]
    polygons = (
        geometry["coordinates"]
        if geometry["type"] == "MultiPolygon"
        else [geometry["coordinates"]]
    )
    # Standard Web Mercator, preserving a single uniform projected display scale.
    rings = [
        [
            (
                6378137 * math.radians(lon),
                6378137 * math.log(math.tan(math.pi / 4 + math.radians(lat) / 2)),
            )
            for lon, lat in polygon[0]
        ]
        for polygon in polygons
    ]
    points = [p for ring in rings for p in ring]
    xmin, xmax = min(p[0] for p in points), max(p[0] for p in points)
    ymin, ymax = min(p[1] for p in points), max(p[1] for p in points)
    scale = 180 / max(xmax - xmin, ymax - ymin)
    paths = [
        "M"
        + " L".join(
            f"{10 + (x - xmin) * scale:.1f},{10 + (ymax - y) * scale:.1f}"
            for x, y in simplify(ring)
        )
        + " Z"
        for ring in rings
    ]
    digest = hashlib.sha256(source.read_bytes()).hexdigest()
    svg = (
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 200 200">'
        "<title>Complete Ontario boundary, Statistics Canada 2021</title>"
        f"<desc>EPSG:3857, uniform scale, 4 projected-km simplification. Source SHA256 {digest}</desc>"
        f'<path d="{" ".join(paths)}" fill="none" stroke="#a8ad71" stroke-width="1.4"/></svg>\n'
    )
    (ROOT / "web/demo/console/ontario.svg").write_text(svg)


if __name__ == "__main__":
    build()

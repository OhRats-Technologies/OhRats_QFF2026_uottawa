"""Bounded, attributed MaleCNS geometry snapshot for the browser explorer.

SWC coordinates use 8 nm voxels; legacy ROI mesh vertices use nm. Both
are converted to micrometres. Skeleton topology is preserved; ROI meshes
are simplified by declared vertex clustering for interactive display.
"""

from concurrent.futures import ThreadPoolExecutor
import hashlib
import json
from pathlib import Path
import struct
from urllib.request import urlopen
import numpy as np
from .data import REPO, load_graph

ROOT = "https://storage.googleapis.com/flyem-male-cns/"
ANNOTATIONS = (
    ROOT
    + "v1.0/connectome-data/flat-connectome/body-annotations-male-cns-v1.0-minconf-0.5.feather"
)
SKELS = ROOT + "v1.0/segmentation/skeletons-malecns/skeletons-swc/"
ROIS = ROOT + "rois/fullbrain-roi-v4/"
CONTEXT = [
    "LC10a",
    "LC6",
    "LC4",
    "LPLC2",
    "MeTu1",
    "EPG",
    "PEN_a",
    "DNp01",
    "MBON01",
    "MBON02",
    "MBON03",
    "MBON05",
    "MBON06",
    "MBON14",
    "DNa01",
    "DNge104",
]
REGIONS = [
    "ME(L)",
    "ME(R)",
    "LO(L)",
    "LO(R)",
    "LOP(L)",
    "LOP(R)",
    "AL(L)",
    "AL(R)",
    "LH(L)",
    "LH(R)",
    "CA(L)",
    "CA(R)",
    "FB",
    "EB",
    "PB",
    "GNG",
    "SLP(L)",
    "SLP(R)",
]


def parse_swc(text):
    rows = [
        line.split() for line in text.splitlines() if line and not line.startswith("#")
    ]
    if not rows or any(len(r) != 7 for r in rows):
        raise ValueError("Malformed SWC rows")
    ids = [int(r[0]) for r in rows]
    lookup = {node: i for i, node in enumerate(ids)}
    if len(lookup) != len(ids):
        raise ValueError("Duplicate SWC node")
    parents = [int(r[6]) for r in rows]
    points = np.array([[float(x) for x in r[2:5]] for r in rows]) * 0.008
    radii = np.array([float(r[5]) for r in rows]) * 0.008
    if (
        not np.isfinite(points).all()
        or not np.isfinite(radii).all()
        or np.any(radii < 0)
    ):
        raise ValueError("Invalid SWC geometry")
    edges = []
    for i, p in enumerate(parents):
        if p != -1:
            if p not in lookup or p == ids[i]:
                raise ValueError("Invalid SWC parent")
            edges.append([lookup[p], i])
    # Follow each parent chain; cache complete chains to keep this linear.
    done = set()
    for node in ids:
        chain = set()
        current = node
        while current != -1 and current not in done:
            if current in chain:
                raise ValueError("Cyclic SWC")
            chain.add(current)
            current = parents[lookup[current]]
        done.update(chain)
    return points, np.asarray(edges, dtype=int), radii


def decode_mesh(blob, cell_um=2.5):
    if len(blob) < 4 or not np.isfinite(cell_um) or cell_um <= 0:
        raise ValueError("Invalid legacy mesh header or clustering size")
    n = struct.unpack_from("<I", blob)[0]
    if (
        n < 3
        or n > 1_000_000
        or len(blob) < 4 + n * 12 + 12
        or (len(blob) - 4 - n * 12) % 12
    ):
        raise ValueError("Invalid legacy mesh size")
    vertices = (
        np.frombuffer(blob, dtype="<f4", count=n * 3, offset=4)
        .reshape(-1, 3)
        .astype(float)
        / 1000
    )
    faces = np.frombuffer(blob, dtype="<u4", offset=4 + n * 12).reshape(-1, 3)
    if not np.isfinite(vertices).all() or np.max(faces) >= n:
        raise ValueError("Invalid mesh geometry")
    cells = np.floor(vertices / cell_um).astype(int)
    _, inverse = np.unique(cells, axis=0, return_inverse=True)
    counts = np.bincount(inverse)
    v = np.vstack(
        [np.bincount(inverse, weights=vertices[:, k]) / counts for k in range(3)]
    ).T
    f = inverse[faces]
    keep = (f[:, 0] != f[:, 1]) & (f[:, 1] != f[:, 2]) & (f[:, 0] != f[:, 2])
    f = f[keep]
    _, idx = np.unique(np.sort(f, axis=1), axis=0, return_index=True)
    f = f[np.sort(idx)]
    return v, f


def main():
    import pandas as pd

    cache = REPO / "results/morphology-source"
    cache.mkdir(parents=True, exist_ok=True)
    sources = []

    def fetch(url):
        name = hashlib.sha256(url.encode()).hexdigest()
        p = cache / name
        if not p.exists():
            with urlopen(url, timeout=40) as r:
                b = r.read(20_000_001)
            if len(b) > 20_000_000:
                raise ValueError("Source exceeds bounded download size")
            p.write_bytes(b)
        b = p.read_bytes()
        return b, {"url": url, "sha256": hashlib.sha256(b).hexdigest(), "bytes": len(b)}

    raw, s = fetch(ANNOTATIONS)
    sources.append(s)
    import io

    table = pd.read_feather(io.BytesIO(raw))
    groups, _, _ = load_graph()
    chosen = []
    counts = {}
    for group in groups:
        typ, side = group.rsplit("_", 1)
        matches = table[
            (table["type"] == typ) & (table["somaSide"] == side)
        ].sort_values("bodyId")
        counts[group] = len(matches)
        # Spatially cover each class using evenly spaced sorted soma X coordinates.
        matches = matches[matches.somaLocation.map(lambda x: x is not None)]
        matches = matches.assign(
            sx=matches.somaLocation.map(lambda x: x[0])
        ).sort_values(["sx", "bodyId"])
        for index in np.linspace(0, len(matches) - 1, min(10, len(matches)), dtype=int):
            row = matches.iloc[index]
            chosen.append((row, group))
    # Contralateral representatives are anatomy context only, not model nodes.
    for group in groups:
        typ, _ = group.rsplit("_", 1)
        matches = table[(table["type"] == typ) & (table["somaSide"] == "L")]
        matches = matches[matches.somaLocation.map(lambda x: x is not None)]
        matches = matches.assign(
            sx=matches.somaLocation.map(lambda x: x[0])
        ).sort_values(["sx", "bodyId"])
        for index in np.linspace(0, len(matches) - 1, min(10, len(matches)), dtype=int):
            chosen.append((matches.iloc[index], None))
    for typ in CONTEXT:
        for side in ["L", "R"]:
            matches = table[(table.type == typ) & (table.somaSide == side)].sort_values(
                "bodyId"
            )
            for index in (
                np.linspace(0, len(matches) - 1, min(3, len(matches)), dtype=int)
                if len(matches)
                else []
            ):
                chosen.append((matches.iloc[index], None))

    def neuron(item):
        row, group = item
        body = int(row.bodyId)
        blob, source = fetch(SKELS + str(body) + ".swc")
        p, e, r = parse_swc(blob.decode())
        soma = row.somaLocation
        return {
            "id": body,
            "type": row.type,
            "side": row.somaSide,
            "instance": str(row.instance),
            "group": group,
            "status": str(row.statusLabel),
            "points": np.round(p, 3).ravel().tolist(),
            "edges": e.ravel().tolist(),
            "soma": np.round(np.asarray(soma, dtype=float) * 0.008, 3).tolist()
            if soma is not None
            else p[0].tolist(),
        }, source

    with ThreadPoolExecutor(max_workers=6) as pool:
        cells = list(pool.map(neuron, chosen))
    neurons = [x[0] for x in cells]
    sources.extend(x[1] for x in cells)
    raw, s = fetch(ROIS + "segment_properties/info")
    sources.append(s)
    props = json.loads(raw)["inline"]
    labels = next(p["values"] for p in props["properties"] if p["type"] == "label")
    ids = dict(zip(labels, props["ids"]))

    def region(name):
        raw, s = fetch(ROIS + "mesh/" + ids[name] + ":0")
        sources = [s]
        fragments = json.loads(raw)["fragments"]
        verts = []
        faces = []
        offset = 0
        for fragment in fragments:
            raw, s = fetch(ROIS + "mesh/" + fragment)
            sources.append(s)
            v, f = decode_mesh(raw)
            verts.extend(v.tolist())
            faces.extend((f + offset).tolist())
            offset += len(v)
        return {
            "name": name,
            "vertices": np.round(verts, 3).ravel().tolist(),
            "faces": np.asarray(faces, dtype=int).ravel().tolist(),
        }, sources

    with ThreadPoolExecutor(max_workers=4) as pool:
        regions = list(pool.map(region, REGIONS))
    meshes = [r[0] for r in regions]
    sources.extend(s for _, ss in regions for s in ss)
    output = REPO / "datasets/fly/morphology"
    output.mkdir(exist_ok=True)
    data = {
        "units": "micrometres",
        "coordinate_space": "MaleCNS EM",
        "neurons": neurons,
        "regions": meshes,
        "population_counts": counts,
        "selection": "10 spatially spread soma-X representatives per modeled right-side population, plus 10 contralateral anatomy-only representatives of each type; up to 3 neurons per side for 16 context types, selected by sorted body ID. Missing types are omitted. Not the full connectome.",
        "roi_display_simplification_um": 2.5,
    }
    p = output / "geometry.json"
    p.write_text(json.dumps(data, separators=(",", ":"), allow_nan=False) + "\n")
    manifest = {
        "dataset": "male-cns:v1.0",
        "license": "CC-BY-4.0",
        "license_url": "https://creativecommons.org/licenses/by/4.0/",
        "attribution": "FlyEM / HHMI Janelia, Cambridge, MRC LMB, Google Research",
        "source_home": "https://male-cns.janelia.org/download/",
        "sources": sources,
        "geometry_sha256": hashlib.sha256(p.read_bytes()).hexdigest(),
        "neuron_count": len(neurons),
        "region_count": len(meshes),
        "units": "micrometres",
        "coordinate_conversion": "SWC 8 nm voxels * 0.008; ROI mesh nm * 0.001. No alignment transform between specimens.",
        "limitations": "Coarse published skeletons; selected representative neurons; simplified selected neuropil surfaces. Geometry is measured anatomy; quantum walks are a separate aggregate graph model.",
    }
    (output / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    print(
        json.dumps(
            {
                "neurons": len(neurons),
                "regions": len(meshes),
                "bytes": p.stat().st_size,
                "sources": len(sources),
            }
        )
    )


if __name__ == "__main__":
    main()

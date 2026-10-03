"""Build the portable 3D explorer from attributed anatomy and checked walk models."""

import hashlib, json
import numpy as np
from .data import REPO, load_graph
from .walks import undirected, laplacian
from .atlas import all_source_trajectories


def main():
    nodes, a, provenance = load_graph()
    w = undirected(a)
    scale = w.sum(axis=1).max()
    times = np.linspace(0, 8, 81)
    models = {}
    for lesion in range(-1, 8):
        weights = w.copy()
        if lesion >= 0:
            weights[lesion, :] = weights[:, lesion] = 0
        L = laplacian(weights, scale)
        c, q = all_source_trajectories(L, times)
        ev, vec = np.linalg.eigh(L)
        phases = []
        for t in times:
            U = (vec * np.exp(-1j * ev * t)) @ vec.T
            references = np.angle(np.diag(U))
            phases.append(np.angle(U * np.exp(-1j * references)[None, :]))
        models[str(lesion)] = {
            "classical": np.round(c, 8).tolist(),
            "quantum": np.round(q, 8).tolist(),
            "phase": np.round(phases, 5).tolist(),
            "spectral": {"values": ev.tolist(), "vectors": vec.tolist()},
        }
    p = REPO / "datasets/fly/morphology/geometry.json"
    m = json.loads((p.parent / "manifest.json").read_text())
    if hashlib.sha256(p.read_bytes()).hexdigest() != m["geometry_sha256"]:
        raise ValueError("Anatomy hash mismatch")
    hardware = json.loads(
        (REPO / "artifacts/sprint-20261003/hardware-counts/hardware.json").read_text()
    )
    data = {
        "anatomy": json.loads(p.read_text()),
        "anatomyManifest": m,
        "nodes": nodes,
        "adjacency": a.tolist(),
        "weights": w.tolist(),
        "times": times.tolist(),
        "models": models,
        "graphProvenance": provenance,
        "hardware": hardware,
    }
    (REPO / "explorer/data.json").write_text(
        json.dumps(data, separators=(",", ":"), allow_nan=False) + "\n"
    )
    print("Built explorer/data.json; anatomy and model origins remain separate.")


if __name__ == "__main__":
    main()

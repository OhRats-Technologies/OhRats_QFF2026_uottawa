"""Extract slide data from frozen records; never fit or select a model."""
import argparse
import csv
import hashlib
import json
from collections import defaultdict
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
FILES = {
    "final": "docs/results/annual-final.json",
    "training": "docs/results/annual-final-training.json",
    "matched": "docs/results/annual-matched.json",
    "classical": "docs/results/annual-classical.json",
    "selectors": "docs/results/annual-selectors.json",
    "geometry": "docs/results/annual-bandwidth-geometry.json",
    "source_review": "docs/data/annual_source_review.json",
}


def snapshot():
    records = {key: json.loads((ROOT / name).read_text()) for key, name in FILES.items()}
    sources = {name: hashlib.sha256((ROOT / name).read_bytes()).hexdigest()
               for name in FILES.values()}
    annual_path = ROOT / "docs/data/annual_reused_evaluation.csv"
    with annual_path.open() as stream:
        example = next(r for r in csv.DictReader(stream) if r["year"] == "2021")
    sources[str(annual_path.relative_to(ROOT))] = hashlib.sha256(annual_path.read_bytes()).hexdigest()
    dev = defaultdict(list)
    for row in records["matched"]["results"]:
        key = f'{row["model"]}_{len(row["features"])}'
        dev[key].append(row["mae_ha"])
    for row in records["classical"]["results"]:
        if row["model"] == "training_mean":
            dev["training_mean"].append(row["mae_ha"])
    geometry = []
    for row in records["geometry"]["results"]:
        path = ROOT / ".cache/wildfire/annual-qsvr/guide-geometry-v1" / row["file"]
        assert hashlib.sha256(path.read_bytes()).hexdigest() == row["matrix_sha256"]
        with np.load(path) as data:
            matrix = data[data.files[0]]
        assert matrix.shape == (31, 31)
        geometry.append({**row, "matrix": matrix.round(6).tolist()})
    selections = defaultdict(list)
    for row in records["selectors"]["results"]:
        selections[row["selector"]].append(row["mae_ha"])
    return {
        "sources_sha256": sources,
        "scope": "Frozen annual evidence; displayed heatmaps rounded to six decimals",
        "development": {key: {"fold_mae": values, "mae": float(np.mean(values))}
                        for key, values in dev.items()},
        "final": records["final"]["main_results"],
        "geometry": geometry,
        "selectors": {key: float(np.mean(values)) for key, values in selections.items()},
        "source_review": records["source_review"],
        "annual_example": {key: float(value) for key, value in example.items()},
        "map": json.loads((HERE / "assets/map.json").read_text()),
        "resources": {"training_seconds": records["training"]["wall_seconds"],
                      "evaluation_seconds": records["final"]["wall_seconds"],
                      "geometry_seconds": records["geometry"]["wall_seconds"],
                      "geometry_pair_circuits": records["geometry"]["pair_circuits"]},
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="Verify published snapshot")
    args = parser.parse_args()
    data = snapshot()
    target = HERE / "evidence.json"
    if args.check:
        assert json.loads(target.read_text()) == data, "Slide evidence differs from sources"
        print("Slide evidence matches six frozen result records, the source review and ten saved matrices; no fits/states.")
    else:
        target.write_text(json.dumps(data, separators=(",", ":")) + "\n")
        print("Wrote frozen slide snapshot.")

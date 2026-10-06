"""Publish a teaching snapshot from frozen selector evidence; no fitting or states."""
import argparse
import hashlib
import itertools
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
SOURCES = ["experiments/annual_selectors.json", "experiments/annual_qsvr.json",
           "docs/results/annual-selectors.json"]


def snapshot():
    plan, parent, result = [json.loads((ROOT / p).read_text()) for p in SOURCES]
    record = result["selection_records"][0]
    choices = [r for r in result["results"]
               if r["fold"] == record["fold"] and r["seed"] == record["seed"]
               and len(r.get("feature_indices", [])) == 4]
    def cost(indices):
        relevance = sum(record["relevance"][i] for i in indices) / 4
        redundancy = sum(record["redundancy"][i][j]
                         for i, j in itertools.combinations(indices, 2)) / 6
        return -relevance + plan["redundancy_weight"] * redundancy
    unique = {tuple(sorted(r["feature_indices"])): r["selector"] for r in choices}
    basis = [dict(indices=list(indices), energy=cost(indices), selector=name)
             for indices, name in unique.items()]
    basis.sort(key=lambda r: r["energy"])
    exact = min(cost(s) for s in itertools.combinations(range(10), 4))
    assert abs(exact - record["exact_objective"]) < 1e-12
    for row in choices:
        assert abs(cost(sorted(row["feature_indices"])) - row["objective"]) < 1e-12
    return dict(
        sources_sha256={p: hashlib.sha256((ROOT / p).read_bytes()).hexdigest()
                        for p in SOURCES},
        features=parent["features"], physical_indices=[0, 1, 2, 3],
        record=record, choices=choices, teaching_basis=basis,
        redundancy_weight=plan["redundancy_weight"],
        basis_limitation=f"{len(basis)} distinct saved selector outputs form a teaching basis; "
                         "this is not the original sampled bitstring stream.",
        execution="Read-only arithmetic; no fitting, quantum states or hardware.",
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    data = snapshot()
    path = HERE / "data.json"
    if args.check:
        assert json.loads(path.read_text()) == data
        print("Demo snapshot matches frozen records and original objective.")
    else:
        path.write_text(json.dumps(data, separators=(",", ":")) + "\n")
        print("Published saved selector teaching basis; no fits/states.")

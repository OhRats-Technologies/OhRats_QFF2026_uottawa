"""Validate saved SQD evidence without submitting or rerunning an experiment."""

import argparse
import hashlib
import json
from pathlib import Path

import numpy as np
from .sampling import valid_mask


def audit_run(path):
    path = Path(path)
    manifest = json.loads((path / "manifest.json").read_text())
    config = json.loads((path / "config.json").read_text())
    records = json.loads((path / "results.json").read_text())
    if (
        hashlib.sha256((path / "config.json").read_bytes()).hexdigest()
        != manifest["config_sha256"]
    ):
        raise ValueError("Configuration hash mismatch")
    for source, digest in manifest["sources"].items():
        snapshot = path / "source_snapshot" / Path(source).name
        if hashlib.sha256(snapshot.read_bytes()).hexdigest() != digest:
            raise ValueError(f"Source snapshot hash mismatch: {snapshot.name}")
    nelec = tuple(manifest["nelec"])
    archives = 0
    for seed in config["seeds"]:
        for budget in config["shots"]:
            with np.load(path / f"samples-{seed}-{budget}.npz") as samples:
                raw = samples["raw"]
                filtered = samples["filtered"]
                uniform = samples["uniform"]
                if raw.dtype != bool or raw.shape != (budget, 2 * manifest["norb"]):
                    raise ValueError("Invalid raw sample shape or type")
                np.testing.assert_array_equal(filtered, raw[valid_mask(raw, nelec)])
                if not valid_mask(uniform, nelec).all() or len(uniform) != budget:
                    raise ValueError("Invalid classical-sector samples")
                row = next(
                    r
                    for r in records
                    if r["seed"] == seed
                    and r["shots"] == budget
                    and r["method"] == "postselected_qsci"
                )
                if row["dimension"] != len(np.unique(filtered, axis=0)) or row[
                    "accepted_shots"
                ] != len(filtered):
                    raise ValueError("Postselected sample accounting mismatch")
            archives += 1
    for record in records:
        if record["energy"] is None:
            if record["dimension"] != 0:
                raise ValueError("Missing energy for nonempty basis")
            continue
        if (
            not np.isfinite(record["energy"])
            or record["energy"] < manifest["exact_fci_energy"] - 1e-8
        ):
            raise ValueError("Non-finite energy or variational-bound violation")
        if (
            abs(
                record["error_hartree"]
                - (record["energy"] - manifest["exact_fci_energy"])
            )
            > 1e-10
        ):
            raise ValueError("Energy error accounting mismatch")
    completion = json.loads((path / "completion.json").read_text())
    if completion["comparisons"] != len(records):
        raise ValueError("Incomplete comparison accounting")
    return dict(
        run=str(path),
        comparisons=len(records),
        sample_archives=archives,
        config_and_source_hashes_valid=True,
        particle_number_and_shot_accounting_valid=True,
        energy_accounting_valid=True,
    )


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "runs",
        nargs="*",
        default=[
            "artifacts/sqd/h2-matched-20261004",
            "artifacts/sqd/h4-matched-20261004",
        ],
    )
    args = parser.parse_args()
    print(json.dumps([audit_run(p) for p in args.runs], indent=2))


if __name__ == "__main__":
    main()

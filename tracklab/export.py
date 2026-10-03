"""Export a small, public-safe evidence snapshot with a hash manifest."""

import json, hashlib, shutil
import math
import re
from datetime import datetime, timezone
from flybrain.data import REPO

FILES = {
    "flywalk": ["metrics.json", "probabilities.csv", "sampled_probabilities.csv"],
    "noise": ["metrics.json", "raw.csv"],
    "atlas": ["metrics.json", "lesions.csv", "null.csv"],
    "chemistry": ["metrics.json", "samples.csv"],
    "budgetbond": ["metrics.json", "samples.csv"],
    "eigenbudget": ["metrics.json", "samples.csv"],
    "spinweave": ["metrics.json", "samples.csv"],
    "scheduling": ["metrics.json", "samples.csv"],
    "kernelforge": ["metrics.json", "scores.csv"],
    "statistics": ["summary.json"],
    "evidence": ["summary.json"],
    "mixerbench": ["metrics.json", "runs.csv"],
    "phaseguard": [
        "metrics.json",
        "samples.csv",
        "placements.json",
        "phase_sweep.json",
        "calibration_forecast.json",
    ],
    "spintherm": ["metrics.json"],
    "flyflux": ["metrics.json", "comparisons.csv"],
    "activebudget": ["metrics.json", "samples.csv"],
    "activenoise": ["metrics.json", "samples.csv"],
    "spinshield": ["metrics.json", "samples.csv"],
    "spinaudit": ["metrics.json", "audit.csv"],
    "strengthnull": ["metrics.json", "controls.csv"],
    "forecastaudit": ["metrics.json", "predictions.csv"],
}


def public_hardware_counts(record):
    """Allowlisted raw counts; private service identity never enters the snapshot."""
    if record.get("evidence") != "real_ibm_hardware":
        raise ValueError("Only collected hardware evidence can be exported")
    backend = record["backend"]
    if not re.fullmatch(r"ibm_[A-Za-z0-9_-]{1,64}", backend):
        raise ValueError("Unexpected backend name")
    cases = []
    allowed = {
        "name",
        "basis",
        "distance",
        "time",
        "source",
        "lesion",
        "expected",
        "observed",
        "actual_shots",
        "counts",
        "depth",
        "operations",
        "total_variation_from_ideal",
    }
    for case in record["cases"]:
        expected = case["expected"]
        shots = case["actual_shots"]
        counts = case["counts"]
        width = (len(expected) - 1).bit_length()
        if len(expected) not in [4, 8, 16] or not 0 < shots <= 4096:
            raise ValueError("Unexpected hardware case size")
        if any(not math.isfinite(p) or p < 0 for p in expected) or not math.isclose(
            sum(expected), 1, abs_tol=1e-8
        ):
            raise ValueError("Invalid ideal reference distribution")
        if any(
            not re.fullmatch("[01]{" + str(width) + "}", bits)
            or type(n) is not int
            or n < 0
            for bits, n in counts.items()
        ):
            raise ValueError("Invalid measured counts")
        if sum(counts.values()) != shots:
            raise ValueError("Measured shots do not match counts")
        cases.append({k: case[k] for k in allowed if k in case})
    if not 1 <= len(cases) <= 6:
        raise ValueError("Unexpected hardware publication count")
    return {
        "origin": "REAL_IBM_HARDWARE",
        "backend": backend,
        "collected_utc": record["collected_utc"],
        "cases": cases,
        "interpretation": "Raw returned counts and ideal references; omitted private job and service identity. Physical model settings are in the matching public experiment snapshot. Unknown device systematics are not removed.",
    }


def main():
    root = REPO / "artifacts/sprint-20261003"
    root.mkdir(parents=True, exist_ok=True)
    hashes = {}
    for folder, names in FILES.items():
        for name in names:
            source = REPO / "results" / folder / name
            if not source.exists():
                continue
            dest = root / folder / name
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(source, dest)
            hashes[str(dest.relative_to(root))] = hashlib.sha256(
                dest.read_bytes()
            ).hexdigest()
    for p in (REPO / "results/kernelforge-replications").glob("*/metrics.json"):
        dest = root / "kernelforge-replications" / p.parent.name / "metrics.json"
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(p, dest)
        hashes[str(dest.relative_to(root))] = hashlib.sha256(
            dest.read_bytes()
        ).hexdigest()
    for folder in ["hardware", "chemistry-hardware", "scheduling-hardware"]:
        collected = REPO / "results" / folder / "collected.json"
        if collected.exists():
            public = public_hardware_counts(json.loads(collected.read_text()))
            dest = root / "hardware-counts" / (folder + ".json")
            dest.parent.mkdir(parents=True, exist_ok=True)
            dest.write_text(json.dumps(public, indent=2, sort_keys=True) + "\n")
            hashes[str(dest.relative_to(root))] = hashlib.sha256(
                dest.read_bytes()
            ).hexdigest()
    sources = {
        str(p.relative_to(REPO)): hashlib.sha256(p.read_bytes()).hexdigest()
        for folder in ["flybrain", "tracklab", "tests"]
        for p in (REPO / folder).glob("*.py")
    }
    sources["uv.lock"] = hashlib.sha256((REPO / "uv.lock").read_bytes()).hexdigest()
    (root / "manifest.json").write_text(
        json.dumps(
            {
                "created_utc": datetime.now(timezone.utc).isoformat(),
                "source_sha256": sources,
                "files": hashes,
                "purpose": "Frozen local experiment evidence; simulation/hardware origins are explicit in each file.",
                "excluded": "Credentials, service-instance configuration, job IDs, circuit bundles and full backend calibration model.",
            },
            indent=2,
        )
        + "\n"
    )
    (root / "README.md").write_text(
        "# Sprint evidence snapshot\n\nGenerated by `uv run python -m tracklab.export`. This snapshot contains raw local sample tables and result settings for inspection without rerunning the lab. Check `manifest.json` for SHA-256 hashes. Simulation, local calibration forecasts, and any collected IBM evidence are labeled separately; queued submissions are not measurements.\n\nPlots and interactive controls are bundled in `demo/index.html`. Source data and attribution live in `datasets/fly/`. Commands and caveats live in the repository README.\n"
    )
    print(f"Exported {len(hashes)} evidence files; private service artifacts excluded.")


if __name__ == "__main__":
    main()

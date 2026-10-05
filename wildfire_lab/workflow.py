"""One front door for sources, bounded screens and saved evidence."""

import hashlib
import json
import subprocess
import sys
from pathlib import Path

RECIPES = [
    "scripts/pipeline.py",
    "wildfire_lab/workflow.py",
    "scripts/build_historical_features.py",
    "scripts/add_woodland_features.py",
    "wildfire_lab/weather_preparation.py",
    "wildfire_lab/nfdb.py",
    "wildfire_lab/weather.py",
    "wildfire_lab/feature_joins.py",
    "wildfire_lab/woodland.py",
    "uv.lock",
    "configs/wildfires/ontario.json",
    "docs/data/reproduction_inputs.json",
]


def recipe_commit(root):
    commit = subprocess.check_output(
        ["git", "rev-parse", "HEAD"], cwd=root, text=True
    ).strip()
    hashes = {}
    for name in RECIPES:
        raw = (root / name).read_bytes()
        if raw != subprocess.check_output(
            ["git", "show", f"{commit}:{name}"], cwd=root
        ):
            raise ValueError(
                "Commit preparation recipe changes before running prepare: " + name
            )
        hashes[name] = hashlib.sha256(raw).hexdigest()
    return commit, hashes


def doctor(root, verify=False):
    index = json.loads((root / "docs/data/reproduction_inputs.json").read_text())
    weather = [row for year in index["weather_years"] for row in year["inputs"]]
    sources = weather + index["other_inputs"]
    required = [row["file"] for row in sources] + [row["sidecar"] for row in weather]
    missing = [name for name in required if not (root / name).is_file()]
    mismatched = []
    provenance_differences = []
    if verify:
        for row in sources:
            path = root / row["file"]
            if path.is_file() and "original_receipt" in row:
                actual = json.loads(path.read_text())
                expected = row["original_receipt"]
                if any(
                    actual.get(key) != expected[key]
                    for key in ("crop_sha256", "archive_sha256", "requested_bbox_wgs84")
                ):
                    mismatched.append(row["file"])
                elif hashlib.sha256(path.read_bytes()).hexdigest() != row["sha256"]:
                    provenance_differences.append(row["file"])
                continue
            if (
                path.is_file()
                and hashlib.sha256(path.read_bytes()).hexdigest() != row["sha256"]
            ):
                mismatched.append(row["file"])
        for row in weather:
            path = root / row["sidecar"]
            if path.is_file():
                receipt = json.loads(path.read_text())
                if (
                    receipt.get("sha256") != row["sha256"]
                    or receipt.get("status") != "downloaded"
                ):
                    mismatched.append(row["sidecar"])
    return dict(
        required_files=len(required),
        missing=missing,
        mismatched=mismatched,
        provenance_differences=provenance_differences,
        hashes_verified=verify,
        ready=not missing and not mismatched,
        next_step="Restore original snapshots for exact reproduction; current downloads may differ.",
    )


def acquire(root):
    from scripts.audit_nfdb import acquire as nfdb
    from scripts.download_weather import download
    from scripts.download_woodland import download_year

    config = json.loads((root / "configs/wildfires/ontario.json").read_text())
    nfdb(root / "data/raw/nfdb-audit/source.zip")
    download(root / "data/raw/weather", 1987, 2024, "ON", workers=3)
    download_year(
        1984,
        root / "data/raw/woodland",
        config["woodland_bbox_wgs84"],
        config["max_archive_gib"],
    )
    return doctor(root, verify=True)


def prepare(root):
    from scripts.build_historical_features import build as weather_features
    from scripts.add_woodland_features import build as cover_features

    commit, hashes = recipe_commit(root)
    report = doctor(root, verify=True)
    if not report["ready"]:
        raise ValueError(
            "Original inputs missing or changed; run pipeline.py doctor --verify"
        )
    weather_path, _ = weather_features((1, 2, 3))
    cover_path, manifest = cover_features(weather_path, fixed_year=1984)
    expected = json.loads((root / "docs/data/reproduction_inputs.json").read_text())[
        "training_csv_sha256"
    ]
    if manifest["data_sha256"] != expected:
        raise ValueError("Prepared training table differs from the published snapshot")
    return dict(
        opening_commit=commit,
        recipe_sha256=hashes,
        weather_dataset=str(weather_path),
        dataset=str(cover_path),
        rows=manifest["rows"],
        data_sha256=manifest["data_sha256"],
    )


def run(root, execute=False, plan=None, axis=None):
    if (plan is None) != (axis is None):
        raise ValueError("Declare both a plan and screen axis")
    steps = [
        "acquire selected sources",
        "verify original snapshot hashes",
        "prepare lagged weather and NFDB training labels",
        "join static 1984 woodland",
    ]
    if plan:
        steps += [
            "execute declared training-only screen",
            "export compact outcome summary",
        ]
    if not execute:
        return dict(
            steps=steps,
            executes=False,
            opens_final_test=False,
            note="Use --execute for these steps. Models run only with an explicit plan/axis; no hardware.",
        )
    if plan and (root / ".cache/wildfire/final-test/intent.json").exists():
        raise ValueError(
            "Adaptive discovery is closed after final opening; use collect or a separate replica"
        )
    inputs = doctor(root, verify=True)
    if inputs["mismatched"]:
        raise ValueError(
            "Existing snapshot bytes changed; preserve them and inspect doctor --verify"
        )
    if not inputs["ready"]:
        inputs = acquire(root)
    if not inputs["ready"]:
        raise ValueError(
            "Downloaded sources differ from original snapshots; inspect doctor --verify"
        )
    result = prepare(root)
    if plan:
        from scripts.run_pilot_screen import run as screen
        from wildfire_lab.evidence import write_summary

        outcome = screen(plan, Path(result["dataset"]), axis)
        summary = outcome.with_name("summary-" + outcome.stem + ".json")
        write_summary([outcome], summary)
        result.update(outcome=str(outcome), summary=str(summary))
    return result


def collect(root, output):
    required = [
        root / ".cache/wildfire/final-test/outcome.json",
        root / ".cache/wildfire/policy-evolution-development/outcome.json",
        root / ".cache/wildfire/policy-evolution-confirmation/outcome.json",
    ]
    if any(not path.is_file() for path in required):
        raise FileNotFoundError(
            "Saved run records are required; a fresh clone cannot recollect them"
        )
    output.mkdir(parents=True, exist_ok=False)
    jobs = [
        ("audit_experiment_evidence.py", [], "experiments.json"),
        ("audit_final_evaluation.py", [], "final.json"),
        ("run_policy_evolution.py", ["collect"], "policy.json"),
        ("audit_goal.py", [], "goal.json"),
    ]
    for script, arguments, name in jobs:
        subprocess.run(
            [
                sys.executable,
                str(root / "scripts" / script),
                *arguments,
                "--output",
                str(output / name),
            ],
            cwd=root,
            check=True,
        )
    return dict(
        output=str(output), collected=[name for _, _, name in jobs], model_fits=0
    )


def check(root):
    commands = [[sys.executable, "-m", "unittest", "discover", "-s", "tests", "-v"]]
    commands += [
        [sys.executable, str(path), "--help"]
        for path in sorted((root / "scripts").glob("*.py"))
        if "ArgumentParser(" in path.read_text()
    ]
    for command in commands:
        subprocess.run(command, cwd=root, check=True, stdout=subprocess.DEVNULL)
    return dict(fixture_suite_passed=True, cli_help_paths=len(commands) - 1)

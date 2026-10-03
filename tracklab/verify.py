"""Verify the checked-in evidence and offline demo without contacting hardware."""

import argparse, hashlib, json, re, subprocess, sys
from pathlib import Path
from datetime import datetime
from flybrain.data import REPO, load_graph


def safe_file(root, name):
    path = Path(name)
    if path.is_absolute() or ".." in path.parts:
        raise ValueError("Unsafe manifest path")
    target = (root / path).resolve()
    if not target.is_relative_to(root.resolve()):
        raise ValueError("Manifest path escapes its root")
    return target


def validate_hashes(root, entries):
    for name, expected in entries.items():
        if not re.fullmatch("[0-9a-f]{64}", expected):
            raise ValueError("Invalid SHA-256 value")
        actual = hashlib.sha256(safe_file(root, name).read_bytes()).hexdigest()
        if actual != expected:
            raise ValueError(f"Hash mismatch: {name}")
    return len(entries)


def validate_board(path):
    seen = set()
    required = {"v", "id", "ts", "from", "to", "type", "ref", "scope", "msg"}
    for number, line in enumerate(path.read_text().splitlines(), 1):
        r = json.loads(line)
        if set(r) != required or r["v"] != 1:
            raise ValueError(f"Invalid board schema at line {number}")
        for name in ["from", "to"]:
            if not (name == "to" and r[name] == "*") and not re.fullmatch(
                "[A-Za-z0-9][A-Za-z0-9_-]{0,63}", r[name]
            ):
                raise ValueError(f"Invalid participant at line {number}")
        stamp = datetime.strptime(r["ts"], "%Y-%m-%dT%H:%M:%SZ").strftime(
            "%Y%m%dT%H%M%SZ"
        )
        if (
            not re.fullmatch(
                re.escape(r["from"] + "-" + stamp) + "-[0-9a-f]{8}", r["id"]
            )
            or r["id"] in seen
        ):
            raise ValueError(f"Invalid or duplicate board ID at line {number}")
        if r["type"] not in ["MSG", "ASK", "ACK", "CLM", "DONE", "BLK", "DEC", "CORR"]:
            raise ValueError("Invalid record type")
        if r["ref"] is not None and r["ref"] not in seen:
            raise ValueError("Reference must point backward")
        if r["type"] in ["ACK", "DONE", "BLK", "CORR"] and r["ref"] is None:
            raise ValueError("Required reference missing")
        if not isinstance(r["scope"], str) or not r["scope"].strip():
            raise ValueError("Empty scope")
        if (
            not isinstance(r["msg"], str)
            or not r["msg"].strip()
            or "\n" in r["msg"]
            or "\r" in r["msg"]
        ):
            raise ValueError("Invalid single-line message")
        seen.add(r["id"])
    if path.read_bytes() and not path.read_bytes().endswith(b"\n"):
        raise ValueError("Board needs a trailing newline")
    return len(seen)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--tests", action="store_true")
    args = parser.parse_args()
    root = REPO / "artifacts/sprint-20261003"
    manifest = json.loads((root / "manifest.json").read_text())
    files = validate_hashes(root, manifest["files"])
    sources = validate_hashes(REPO, manifest["source_sha256"])
    nodes, _, _ = load_graph()
    board = validate_board(REPO / "AGENT_BOARD.jsonl")
    demo = REPO / "demo/index.html"
    dm = json.loads((REPO / "demo/manifest.json").read_text())
    if hashlib.sha256(demo.read_bytes()).hexdigest() != dm["sha256"]:
        raise ValueError("Demo hash mismatch")
    html = demo.read_text()
    if re.search(r"<script\b[^>]*\bsrc\s*=", html, re.I) or re.search(
        r"url\(\s*[\"\x27]?https?://", html, re.I
    ):
        raise ValueError("Offline demo loads an external script or CSS resource")
    private_tracked = subprocess.run(
        ["git", "ls-files", ".env", "results", "*.qpy"],
        cwd=REPO,
        text=True,
        capture_output=True,
        check=True,
    ).stdout
    if private_tracked.strip():
        raise ValueError("Ignored private/runtime artifacts are tracked")
    if args.tests:
        subprocess.run(
            [sys.executable, "-m", "unittest", "discover", "-s", "tests", "-q"],
            cwd=REPO,
            check=True,
        )
    print(
        json.dumps(
            {
                "evidence_files_verified": files,
                "source_hashes_verified": sources,
                "dataset_populations": len(nodes),
                "board_records_validated": board,
                "demo_hash_verified": True,
                "private_runtime_artifacts_tracked": False,
                "tests_executed": args.tests,
            }
        )
    )


if __name__ == "__main__":
    main()

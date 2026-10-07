"""Prepare, submit one declared block, or collect the repetition-code study."""
import argparse
import json
from pathlib import Path
import sys
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from wildfire_lab.repetition_hardware import prepare, submit, collect


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=["prepare", "submit", "collect"])
    parser.add_argument("--output", type=Path, default=ROOT/"results/repetition-microkernel-v1")
    parser.add_argument("--backend", choices=["ibm_marrakesh", "ibm_quebec"])
    parser.add_argument("--block", type=int)
    args = parser.parse_args()
    try:
        if args.mode == "prepare":
            result = prepare(ROOT, args.output)
        elif args.mode == "submit":
            result = submit(ROOT, args.output, args.backend, args.block)
        else:
            result = collect(args.output)
        print(json.dumps(result, indent=2))
    except Exception as error:
        print(json.dumps(dict(error_type=type(error).__name__,
              message="Action failed; preserve private records and existing intents. No automatic retry.")))
        raise SystemExit(1)


if __name__ == "__main__":
    main()

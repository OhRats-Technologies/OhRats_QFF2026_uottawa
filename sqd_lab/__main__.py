import argparse, json
from pathlib import Path
from .pipeline import run

parser = argparse.ArgumentParser(
    description="Local Qiskit SQD/QSCI hydrogen-chain pipeline"
)
parser.add_argument("--config", type=Path, default=Path("configs/sqd/h2.json"))
parser.add_argument("--output", type=Path, required=True)
args = parser.parse_args()
manifest, records = run(json.loads(args.config.read_text()), args.output)
print(
    json.dumps(
        dict(
            output=str(args.output),
            exact_fci_energy=manifest["exact_fci_energy"],
            seconds=manifest["seconds"],
            comparisons=len(records),
        ),
        indent=2,
    )
)

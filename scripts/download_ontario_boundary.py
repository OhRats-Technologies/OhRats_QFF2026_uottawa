"""Acquire the official fixed Ontario geometry required by annual cover summaries."""

import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[1]


def main():
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument('--output', type=Path, default=ROOT / 'data/raw/boundaries/ontario-2021.geojson')
    args = cli.parse_args()
    source = json.loads((ROOT / 'experiments/annual_woodland.json').read_text())['boundary']
    if args.output.exists():
        data = args.output.read_bytes()
    else:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(dir=args.output.parent) as temporary:
            path = Path(temporary) / 'boundary.geojson'
            subprocess.run(['curl', '--fail', '--silent', '--show-error', '--max-time', '60',
                            source['source'], '-o', str(path)], check=True)
            data = path.read_bytes()
    actual_hash = hashlib.sha256(data).hexdigest()
    if actual_hash != source['sha256']:
        raise ValueError('Official boundary bytes differ from the frozen snapshot; preserve for review separately')
    doc = json.loads(data)
    if len(doc['features']) != 1 or doc['features'][0]['properties']['PRUID'] != '35':
        raise ValueError('Boundary must be exactly Ontario province 35')
    if not args.output.exists():
        args.output.write_bytes(data)
        args.output.with_suffix('.json').write_text(json.dumps(dict(
            url=source['source'], retrieved_utc=datetime.now(timezone.utc).isoformat(),
            sha256=actual_hash, properties=doc['features'][0]['properties'],
            purpose=source['purpose']), indent=2) + '\n')
    print(json.dumps(dict(path=str(args.output), sha256=actual_hash, province='Ontario')))


if __name__ == '__main__':
    main()

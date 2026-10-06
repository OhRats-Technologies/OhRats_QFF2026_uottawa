"""Acquire advertised training-era SCANFI height overviews under an explicit byte cap."""
import argparse
import hashlib
import json
import re
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urljoin
from urllib.request import urlopen

from scanfi import BASE

LIMIT = 20_000_000
YEARS = range(1985, 2020, 5)


def acquire(url, directory):
    target = directory / url.rsplit('/', 1)[-1]
    receipt_path = target.with_suffix(target.suffix + '.json')
    if target.exists():
        receipt = json.loads(receipt_path.read_text())
        assert hashlib.sha256(target.read_bytes()).hexdigest() == receipt['sha256']
        return receipt
    with urlopen(url, timeout=45) as response:
        expected = int(response.headers.get('Content-Length', '0'))
        if expected > LIMIT:
            raise ValueError(f'Advertised overview exceeds {LIMIT} bytes')
        body = response.read(LIMIT + 1)
        if len(body) > LIMIT:
            raise ValueError('Overview exceeds acquisition budget')
        if expected and len(body) != expected:
            raise ValueError('Incomplete overview response')
    receipt = {'url': url, 'retrieved_utc': datetime.now(timezone.utc).isoformat(),
               'bytes': len(body), 'sha256': hashlib.sha256(body).hexdigest(),
               'role': 'downsampled height context; not native 30m values'}
    target.write_bytes(body)
    receipt_path.write_text(json.dumps(receipt, indent=2) + '\n')
    print(f'Acquired {target.name}: {len(body):,} bytes', flush=True)
    return receipt


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--cache', type=Path, default=Path('.cache/catalogue/20261006'))
    parser.add_argument('--output', type=Path, default=Path('docs/data/scanfi_overviews.json'))
    args = parser.parse_args()
    links = re.findall(r'href="([^"]+)"', (args.cache / 'guides/scanfi-directory.raw').read_text())
    resources = []
    for year in YEARS:
        matches = [name for name in links if re.fullmatch(fr'SCANFI_att_height_{year}_v2_\d+\.tif\.ovr', name)]
        if len(matches) != 1:
            raise ValueError(f'Expected exactly one advertised {year} overview')
        resources.append(urljoin(BASE, matches[0]))
    directory = args.cache / 'scanfi-overviews'
    directory.mkdir(parents=True, exist_ok=True)
    with ThreadPoolExecutor(max_workers=3) as executor:
        records = list(executor.map(lambda url: acquire(url, directory), resources))
    total = sum(item['bytes'] for item in records)
    result = {'purpose': 'Training-era coarse context acquisition; no fitting or test-year download',
              'budget': {'files': 7, 'max_bytes_per_file': LIMIT, 'parallel_requests': 3},
              'total_bytes': total, 'records': records,
              'limitations': ['Overview resampling/units/CRS must be audited before numerical use.',
                              'Retrospective reconstruction is not an as-of historical product.']}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + '\n')
    print(f'Total {total:,} bytes; native rasters were not downloaded.', flush=True)


if __name__ == '__main__':
    main()

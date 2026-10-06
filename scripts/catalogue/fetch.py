"""Cache official CKAN package metadata; preserve a per-request receipt."""
import argparse
import csv
import hashlib
import json
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from pathlib import Path
from urllib.request import Request, urlopen

API = 'https://open.canada.ca/data/api/action/package_show?id='
EXTRA = [
    '7cbdfae1-f724-4679-8f0f-1c611f17186f',
    'a6b81e8b-d429-4629-9121-5a56786fcb83',
    '836082d5-d55f-46c3-9b9c-aaf1a306c247',
    '0bce352f-6f3f-4a30-9763-c80805fcf272',
    '347a2de5-1006-4c1f-ba09-b66947654d0a',
    '1728e7f9-472a-474e-9e04-f96bf59479f9',
    'adfa340a-1781-48b1-ab17-2e1ca1b915df',
]


def fetch(identifier, cache):
    path = cache / 'packages' / f'{identifier}.json'
    if path.exists():
        return {'id': identifier, 'status': 'cached'}
    url = API + identifier
    observed = datetime.now(timezone.utc).isoformat()
    try:
        with urlopen(Request(url, headers={'Accept': 'application/json'}), timeout=45) as response:
            body = response.read(4_000_001)
            status = response.status
        if len(body) > 4_000_000:
            raise ValueError('Metadata exceeds 4 MB budget')
        package = json.loads(body)
        if not package.get('success') or package['result']['id'] != identifier:
            raise ValueError('API response does not match requested identifier')
        path.write_bytes(body)
        receipt = {'id': identifier, 'url': url, 'observed': observed,
                   'status': status, 'bytes': len(body),
                   'sha256': hashlib.sha256(body).hexdigest()}
        path.with_suffix('.receipt.json').write_text(json.dumps(receipt, indent=2) + '\n')
        return receipt
    except Exception as error:
        return {'id': identifier, 'url': url, 'observed': observed,
                'status': 'failed', 'error': str(error)}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--cache', type=Path, default=Path('.cache/catalogue/20261006'))
    parser.add_argument('--workers', type=int, default=4, choices=range(1, 5))
    args = parser.parse_args()
    source = args.cache / 'fire-search-export.csv'
    rows = list(csv.DictReader(source.open(encoding='utf-8-sig')))
    identifiers = sorted({row['ID'] for row in rows} | set(EXTRA))
    (args.cache / 'packages').mkdir(parents=True, exist_ok=True)
    receipts = []
    with ThreadPoolExecutor(max_workers=args.workers) as pool:
        futures = {pool.submit(fetch, identifier, args.cache): identifier for identifier in identifiers}
        for future in as_completed(futures):
            receipts.append(future.result())
            if len(receipts) % 25 == 0:
                print(f'{len(receipts)}/{len(identifiers)} metadata records collected', flush=True)
    audit = {'export_sha256': hashlib.sha256(source.read_bytes()).hexdigest(),
             'export_records': len(rows), 'export_overflow_rows': sum(None in r for r in rows),
             'note': 'Export has extra unlabelled CSV fields; only its early ID column is used. Structured fields come from package_show.',
             'requested': len(identifiers), 'receipts': sorted(receipts, key=lambda r: r['id'])}
    (args.cache / 'fetch-receipt.json').write_text(json.dumps(audit, indent=2) + '\n')
    failed = [r for r in receipts if r['status'] == 'failed']
    print(json.dumps({'requested': len(identifiers), 'failed': failed}, indent=2))


if __name__ == '__main__':
    main()

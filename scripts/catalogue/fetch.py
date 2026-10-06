"""Cache official CKAN package metadata; preserve a per-request receipt."""
import argparse
import csv
import hashlib
import json
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from pathlib import Path
from urllib.request import Request, urlopen

from metadata import API, MAX_BYTES, OWNER_IDS, read_package

ROOT = Path(__file__).resolve().parents[2]


def fetch(identifier, cache):
    path = cache / 'packages' / f'{identifier}.json'
    url = API + identifier
    observed = datetime.now(timezone.utc).isoformat()
    try:
        if path.exists() or path.with_suffix('.receipt.json').exists():
            _, receipt = read_package(path)
            return {**receipt, 'status': 'cached', 'http_status': receipt['status']}
        with urlopen(Request(url, headers={'Accept': 'application/json'}), timeout=45) as response:
            body = response.read(MAX_BYTES + 1)
            status = response.status
        if len(body) > MAX_BYTES:
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
    parser.add_argument('--manifest', type=Path, default=ROOT / 'docs/data/fire_catalogue_pages.json',
                        help='Committed screened IDs, used when the original export is absent')
    parser.add_argument('--dry-run', action='store_true', help='List acquisition count/source without requests')
    args = parser.parse_args()
    source = args.cache / 'fire-search-export.csv'
    if source.exists():
        rows = list(csv.DictReader(source.open(encoding='utf-8-sig')))
        identifiers = {row['ID'] for row in rows}
        provenance = {'export_sha256': hashlib.sha256(source.read_bytes()).hexdigest(),
                      'export_records': len(rows), 'export_overflow_rows': sum(None in r for r in rows)}
    else:
        manifest = json.loads(args.manifest.read_text())
        identifiers = {identifier for page in manifest['pages'] for identifier in page['ids']}
        assert len(identifiers) == manifest['unique_ids']
        provenance = {'manifest_sha256': hashlib.sha256(args.manifest.read_bytes()).hexdigest(),
                      'screened_records': len(identifiers),
                      'note': 'Reacquires screened IDs, not the current search ranking. Metadata may have changed.'}
    identifiers = sorted(identifiers | set(OWNER_IDS))
    if args.dry_run:
        print(json.dumps({'requested': len(identifiers), **provenance}, indent=2))
        return
    (args.cache / 'packages').mkdir(parents=True, exist_ok=True)
    receipts = []
    with ThreadPoolExecutor(max_workers=args.workers) as pool:
        futures = {pool.submit(fetch, identifier, args.cache): identifier for identifier in identifiers}
        for future in as_completed(futures):
            receipts.append(future.result())
            if len(receipts) % 25 == 0:
                print(f'{len(receipts)}/{len(identifiers)} metadata records collected', flush=True)
    audit = {**provenance,
             'requested': len(identifiers), 'receipts': sorted(receipts, key=lambda r: r['id'])}
    (args.cache / 'fetch-receipt.json').write_text(json.dumps(audit, indent=2) + '\n')
    failed = [r for r in receipts if r['status'] == 'failed']
    print(json.dumps({'requested': len(identifiers), 'failed': failed}, indent=2))
    if failed:
        raise SystemExit(1)


if __name__ == '__main__':
    main()

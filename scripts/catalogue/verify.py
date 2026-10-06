"""Verify the preserved catalogue snapshot and ignored inventory rebuild, offline."""
import argparse
import csv
import hashlib
import io
import json
import tempfile
from collections import Counter
from contextlib import redirect_stdout
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import patch

import fetch
from inventory import publish
from metadata import OWNER_IDS, read_package

ROOT = Path(__file__).resolve().parents[2]


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def damaged_cache_checks(original, output):
    identifier = original.stem
    body = original.read_bytes()
    receipt = json.loads(original.with_suffix('.receipt.json').read_text())
    results = []
    with tempfile.TemporaryDirectory(prefix='cache-fixtures-', dir=output) as directory:
        root = Path(directory)
        for case in ['valid', 'body_hash', 'identity', 'request_url', 'missing_receipt', 'missing_body']:
            cache = root / case
            path = cache / 'packages' / original.name
            path.parent.mkdir(parents=True)
            encoded, request = body, dict(receipt)
            if case == 'body_hash':
                encoded += b'\n'  # Valid JSON, changed bytes.
            elif case == 'identity':
                package = json.loads(body)
                package['result']['id'] = 'different-package'
                encoded = json.dumps(package).encode()
                request['sha256'] = hashlib.sha256(encoded).hexdigest()
                request['bytes'] = len(encoded)
            elif case == 'request_url':
                request['url'] = 'https://example.invalid/wrong-source'
            if case != 'missing_body':
                path.write_bytes(encoded)
            if case != 'missing_receipt':
                path.with_suffix('.receipt.json').write_text(json.dumps(request))
            before = {p.name: p.read_bytes() for p in path.parent.iterdir()}
            with patch.object(fetch, 'urlopen', side_effect=AssertionError('Offline check')) as network:
                result = fetch.fetch(identifier, cache)
                network.assert_not_called()
            assert result['status'] == ('cached' if case == 'valid' else 'failed'), case
            assert before == {p.name: p.read_bytes() for p in path.parent.iterdir()}, case
            if case == 'body_hash':
                manifest = cache / 'one-id-manifest.json'
                manifest.write_text(json.dumps({'unique_ids': 1, 'pages': [{'ids': [identifier]}]}))
                with (
                    patch.object(fetch, 'OWNER_IDS', []),
                    patch('sys.argv', ['fetch.py', '--cache', str(cache), '--manifest', str(manifest)]),
                    patch.object(fetch, 'urlopen', side_effect=AssertionError('Offline check')) as network,
                    redirect_stdout(io.StringIO()),
                ):
                    try:
                        fetch.main()
                    except SystemExit as error:
                        assert error.code == 1
                    else:
                        raise AssertionError('Failed acquisition must exit nonzero')
                    network.assert_not_called()
                assert before == {p.name: p.read_bytes() for p in path.parent.iterdir()}
            results.append({'case': case, 'status': result['status'], 'bytes_preserved': True,
                            'network_requests': 0})
        rejected_output = root / 'partial-output'
        try:
            publish(root / 'valid', rejected_output, ROOT / 'docs/data/fire_catalogue_pages.json')
        except ValueError:
            assert not rejected_output.exists()
        else:
            raise AssertionError('Incomplete cache must not publish a partial inventory')
    return results


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--cache', type=Path, default=ROOT / '.cache/catalogue/20261006')
    parser.add_argument('--output', type=Path, default=ROOT / '.cache/catalogue/handoff-check')
    args = parser.parse_args()
    output = args.output.resolve()
    if not output.is_relative_to(ROOT / '.cache'):
        parser.error('Check output must be under ignored .cache/')
    manifest = ROOT / 'docs/data/fire_catalogue_pages.json'
    pages = json.loads(manifest.read_text())
    assert [page['page'] for page in pages['pages']] == list(range(1, pages['page_count'] + 1))
    ordered = [identifier for page in pages['pages'] for identifier in page['ids']]
    assert len(ordered) == len(set(ordered)) == pages['unique_ids'] == pages['record_count']
    assert all(len(page['ids']) == 10 for page in pages['pages'][:-1])
    assert len(pages['pages'][-1]['ids']) == 5
    export = args.cache / 'fire-search-export.csv'
    assert digest(export) == pages['export_sha256']
    with export.open(encoding='utf-8-sig') as stream:
        rows = list(csv.DictReader(stream))
    assert {row['ID'] for row in rows} == set(ordered)
    assert not pages['missing_ids'] and not pages['extra_ids']
    paths = sorted(p for p in (args.cache / 'packages').glob('*.json') if '.receipt.' not in p.name)
    assert {p.stem for p in paths} == set(ordered) | set(OWNER_IDS)
    originals = [export, *paths, *(p.with_suffix('.receipt.json') for p in paths)]
    original_hashes = {str(p.relative_to(args.cache)): digest(p) for p in originals}
    validated = [read_package(path) for path in paths]
    output.mkdir(parents=True, exist_ok=True)
    publish(args.cache, output / 'inventory', manifest)
    matches = {}
    for name in ['fire_catalogue_inventory.json', 'FIRE_CATALOGUE_PAGES.md']:
        expected = ROOT / 'docs/data' / name
        actual = output / 'inventory' / name
        assert actual.read_bytes() == expected.read_bytes(), name
        matches[name] = digest(actual)
    inventory = json.loads((output / 'inventory/fire_catalogue_inventory.json').read_text())
    counts = Counter(row['category'] for row in inventory['records'] if row['page'])
    assert dict(counts) == inventory['categories'] and sum(counts.values()) == len(ordered)
    cases = damaged_cache_checks(paths[0], output)
    assert original_hashes == {str(p.relative_to(args.cache)): digest(p) for p in originals}
    code = ['metadata.py', 'fetch.py', 'inventory.py', 'verify.py']
    receipt = {
        'checked_utc': datetime.now(timezone.utc).isoformat(), 'status': 'passed',
        'snapshot_observed_utc': pages['observed_utc'], 'pages': pages['page_count'],
        'search_ids': len(ordered), 'metadata_responses': len(validated),
        'metadata_bytes': sum(record['bytes'] for _, record in validated),
        'export_sha256': digest(export), 'page_manifest_sha256': digest(manifest),
        'export_overflow_rows': sum(None in row for row in rows),
        'byte_identical_rebuild': matches, 'cache_cases': cases,
        'incomplete_cache_rejected_before_output': True, 'original_cache_preserved': True,
        'original_source_files_checked': len(originals), 'failed_cli_exits_nonzero': True,
        'code_sha256': {f'scripts/catalogue/{name}': digest(Path(__file__).with_name(name)) for name in code},
        'network_requests': 0, 'predictor_fits': 0, 'quantum_states': 0, 'hardware_jobs': 0,
        'scope': 'Saved snapshot hashes, identity, CSV membership, all-page reconstruction and cache-failure handling. Not a new live search audit or validation of all downloadable datasets.',
    }
    (output / 'receipt.json').write_text(json.dumps(receipt, indent=2) + '\n')
    print(json.dumps({'pages': receipt['pages'], 'search_ids': len(ordered),
                      'metadata_responses': len(validated), 'offline_rebuild': 'identical'}, indent=2))


if __name__ == '__main__':
    main()

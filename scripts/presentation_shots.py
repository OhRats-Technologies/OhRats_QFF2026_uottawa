"""Build the presentation's measured yield asset from public hardware receipts."""
import hashlib
import json
from pathlib import Path
import zipfile

ROOT = Path(__file__).resolve().parents[1]


def build(root=ROOT):
    result = dict(rows=[], jobs=0, charged_seconds=0, physical_shots=0,
        source='docs/SHOT_SWEEP.md', source_sha256={},
        scope='20-candidate/four-selected circuits; one execution per condition; percentages are not prediction accuracy')
    for device in ['marrakesh', 'quebec']:
        path = root/f'docs/data/shot-sweep-{device}-evidence.zip'
        result['source_sha256'][str(path.relative_to(root))] = hashlib.sha256(path.read_bytes()).hexdigest()
        with zipfile.ZipFile(path) as archive:
            evidence = json.loads(archive.read('evidence.json'))['analysis']
        result['jobs'] += evidence['hardware_jobs']
        result['charged_seconds'] += evidence['charged_seconds']
        result['physical_shots'] += evidence['physical_shots']
        for row in evidence['rows']:
            if row['specification']['pool_size'] != 20 or row['specification']['kind'] != 'confirmation':
                continue
            valid = sum(count for bits, count in row['measured_counts'].items() if bits.count('1') == 4)
            assert valid == row['feasible_shots']
            assert sum(row['measured_counts'].values()) == row['shots']
            assert valid/row['shots'] == row['feasible_fraction']
            result['rows'].append(dict(device=device, arm=row['arm'], shots=row['shots'],
                valid=valid, fraction=row['feasible_fraction'], wilson95=row['wilson95']))
    return result


if __name__ == '__main__':
    (ROOT/'web/presentation/assets/shot-sweep.json').write_text(json.dumps(build(), indent=2)+'\n')
    print('Rebuilt twelve measured yield points from public counts; no hardware calls.')

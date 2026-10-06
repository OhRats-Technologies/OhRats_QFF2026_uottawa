"""Independent raw NFDB arithmetic and saved 2018 prediction checks; no fits."""

import argparse
from collections import Counter
import csv
import hashlib
import io
import json
import math
from pathlib import Path
import statistics
import zipfile

import numpy as np

ROOT = Path(__file__).resolve().parents[1]


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def fire_audit(archive):
    manifest = json.loads((ROOT / 'docs/data/annual_reused_evaluation_manifest.json').read_text())
    if digest(archive) != manifest['source_sha256']['nfdb']:
        raise ValueError('Archive differs from the frozen source snapshot')
    with zipfile.ZipFile(archive) as z:
        name, = [n for n in z.namelist() if n.startswith('NFDB_point_') and n.endswith('.txt')]
        with z.open(name) as stream:
            rows = [r for r in csv.DictReader(io.TextIOWrapper(stream, encoding='utf-8-sig'))
                    if r['SRC_AGENCY'] == 'ON']
    identities = Counter(r['NFDBFIREID'].strip() for r in rows)
    published = {}
    for file in ['annual_training.csv', 'annual_reused_evaluation.csv']:
        with (ROOT / 'docs/data' / file).open() as stream:
            published.update({int(r['year']): r for r in csv.DictReader(stream)})
    annual, mismatches = [], []
    for year in range(1988, 2025):
        raw = [r for r in rows if r['YEAR'] == str(year)]
        accepted, exclusions, removed = [], Counter(), []
        for row in raw:
            identity = row['NFDBFIREID'].strip()
            if not identity or identities[identity] != 1:
                exclusions['identity'] += 1
                removed.append(float(row['SIZE_HA']))
                continue
            if row['PRESCRIBED'].strip() or row['FIRE_TYPE'].strip() == 'PB':
                exclusions['prescribed'] += 1
                continue
            try:
                size = float(row['SIZE_HA'])
            except ValueError:
                size = math.nan
            if not math.isfinite(size) or size < 0:
                exclusions['unknown_size'] += 1
            else:
                accepted.append(size)
        sizes = sorted(accepted, reverse=True)
        total = math.fsum(sizes)
        mean = total / len(sizes)
        expected = published[year]
        checks = {
            'size_observed_incidents': len(sizes), 'mean_reported_size_ha': mean,
            'total_observed_size_ha': total, 'identity_exclusions': exclusions['identity'],
            'prescribed_exclusions': exclusions['prescribed'],
            'unknown_size_incidents': exclusions['unknown_size'],
            'recorded_incidents': len(sizes) + exclusions['unknown_size'],
        }
        for field, actual in checks.items():
            if not math.isclose(actual, float(expected[field]), rel_tol=1e-12, abs_tol=1e-6):
                mismatches.append(dict(year=year, field=field, actual=actual, published=expected[field]))
        annual.append(dict(year=year, raw_rows=len(raw), **checks,
                           median_size_ha=statistics.median(sizes), largest_size_ha=sizes[0],
                           largest_five_area_fraction=math.fsum(sizes[:5]) / total,
                           identity_excluded_reported_ha=math.fsum(v for v in removed if v >= 0)))
    return dict(source_member=name, source_sha256=digest(archive), annual=annual,
                comparison_fields=list(checks), mismatches=mismatches,
                identity_policy='Quarantine blank or globally repeated ON NFDBFIREID; not deduplication.')


def check_2018():
    matched = json.loads((ROOT / 'docs/results/annual-matched.json').read_text())
    training = json.loads((ROOT / 'docs/results/annual-final-training.json').read_text())
    with (ROOT / 'docs/data/annual_training.csv').open() as stream:
        years = [int(r['year']) for r in csv.DictReader(stream)]
    index = years.index(2018)
    held_out = []
    for row in matched['results']:
        if row['fold'] == [1988, 2014, 2015, 2018] and len(row['features']) == 4:
            i = row['years'].index(2018)
            held_out.append(dict(model=row['model'], trained_through=2014,
                                 actual_ha=row['actual_ha'][i], predicted_ha=row['predicted_ha'][i]))
    in_sample = []
    with zipfile.ZipFile(ROOT / 'docs/data/annual_final_evidence.zip') as bundle:
        for model in training['main_models']:
            if model['id'] not in ['matched_rbf_svr_4', 'matched_fidelity_svr_4']:
                continue
            body = bundle.read(f"kernels/{model['kernel_id']}/matrix.npz")
            entry = next(r for r in training['kernels'] if r['id'] == model['kernel_id'])
            if hashlib.sha256(body).hexdigest() != entry['matrix_sha256']:
                raise ValueError('Saved training matrix hash differs')
            matrix = np.load(io.BytesIO(body))['gram']
            state, scaling = model['state'], model['scaling']
            scaled = matrix[index, state['support']] @ state['dual'] + state['intercept']
            value = float(np.expm1(scaling['target_mean'] + scaling['target_scale'] * scaled))
            in_sample.append(dict(model=model['id'], trained_through=2018, predicted_ha=value,
                                  epsilon_standardized_log=model['params']['epsilon']))
    return dict(held_out=held_out, final_in_sample=in_sample,
                interpretation='Final training includes 2018; in-sample estimates are not validation.')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--archive', type=Path, default=ROOT / 'data/raw/nfdb-audit/source.zip')
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    source = fire_audit(args.archive)
    receipt = dict(status='passed' if not source['mismatches'] else 'failed', **source,
                   year_2018=check_2018(), audit_script_sha256=digest(Path(__file__)),
                   method='Independent csv/stdlib parser and arithmetic; no annual_data/nfdb imports.',
                   predictor_fits=0, new_quantum_states=0, hardware_jobs=0,
                   limitation='Checks frozen-source arithmetic, not completeness or correctness of every agency record.')
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open('x') as stream:
        json.dump(receipt, stream, indent=2)
        stream.write('\n')
    print(receipt['status'], len(source['annual']), 'years checked; mismatches:', len(source['mismatches']))
    if source['mismatches']:
        raise SystemExit(1)


if __name__ == '__main__':
    main()

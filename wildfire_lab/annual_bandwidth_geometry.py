"""Post-final input-only bandwidth geometry; no targets, fits, shots or hardware."""

from datetime import datetime, timezone
import json
import time

import numpy as np
import pandas as pd

from wildfire_lab.annual_data import digest
from wildfire_lab.annual_final_kernel import fidelity


def summary(gram):
    np.testing.assert_allclose(gram, gram.T, atol=1e-10)
    np.testing.assert_allclose(np.diag(gram), 1., atol=1e-10)
    eigenvalues = np.linalg.eigvalsh(gram)
    if not np.isfinite(gram).all() or eigenvalues.min() < -1e-8:
        raise ValueError('Invalid exact Gram matrix')
    weights = np.maximum(eigenvalues, 0) / eigenvalues.sum()
    positive = weights[weights > 0]
    off = gram[~np.eye(len(gram), dtype=bool)]
    return dict(minimum_eigenvalue=float(eigenvalues.min()),
                maximum_eigenvalue=float(eigenvalues.max()),
                condition_number=float(np.linalg.cond(gram)) if eigenvalues.min() > 1e-12 else None,
                effective_rank=float(np.exp(-np.sum(positive * np.log(positive)))),
                off_diagonal_mean=float(off.mean()), off_diagonal_std=float(off.std()),
                fraction_off_diagonal_below_001=float(np.mean(off < .01)),
                relative_distance_from_identity=float(np.linalg.norm(gram-np.eye(len(gram))) / np.linalg.norm(gram)))


def inputs(root, plan_path):
    plan = json.loads(plan_path.read_text())
    parent_path = root / plan['parent']
    if digest(parent_path) != plan['parent_sha256'] or digest(root / plan['dataset']) != plan['dataset_sha256']:
        raise ValueError('Frozen training inputs or parent changed')
    parent = json.loads(parent_path.read_text())
    # usecols excludes every target/denominator column, even during CSV parsing.
    table = pd.read_csv(root / plan['dataset'], usecols=['year', *parent['features']])
    if table.year.tolist() != list(range(plan['years'][0], plan['years'][1] + 1)):
        raise ValueError('Unexpected training years')
    return plan, parent, table


def recipe(root, plan_path):
    paths = ['wildfire_lab/annual_bandwidth_geometry.py', 'scripts/annual_bandwidth_geometry.py',
             'wildfire_lab/annual_final_kernel.py', 'wildfire_lab/library_kernel.py', 'uv.lock']
    return dict(plan_sha256=digest(plan_path), code_sha256={p: digest(root / p) for p in paths})


def run(root, plan_path, output):
    if output.exists():
        raise FileExistsError(output)
    plan, parent, table = inputs(root, plan_path)
    pinned = recipe(root, plan_path)
    output.mkdir(parents=True)
    (output / 'intent.json').write_text(json.dumps(dict(created_utc=datetime.now(timezone.utc).isoformat(), **pinned), indent=2) + '\n')
    start = time.perf_counter()
    records = []
    for width in plan['widths']:
        features = parent['four_feature_subset'] if width == 4 else parent['features']
        values = table[features].to_numpy()
        x = (values-values.mean(axis=0)) / values.std(axis=0)
        if not np.isfinite(x).all():
            raise ValueError('Nonfinite standardized training inputs')
        for denominator in plan['amplitudes_pi_denominator']:
            if time.perf_counter()-start > plan['budget']['execution_seconds']:
                raise TimeoutError('Geometry allowance exhausted; preserve partial records')
            angles = np.pi / denominator * np.tanh(x / 2)
            kernel, sampler = fidelity(width, plan['repetitions'])
            gram = kernel.evaluate(angles)
            name = f'width-{width}-pi-over-{denominator}.npz'
            np.savez(output / name, gram=gram, angles=angles)
            records.append(dict(inputs=width, amplitude_pi_denominator=denominator,
                                file=name, matrix_sha256=digest(output / name),
                                pair_circuits=sampler.circuits, **summary(gram)))
            (output / 'progress.json').write_text(json.dumps(records, indent=2) + '\n')
            print(json.dumps(dict(completed=len(records), total=10, inputs=width,
                                  denominator=denominator, effective_rank=records[-1]['effective_rank'])), flush=True)
    pairs = sum(r['pair_circuits'] for r in records)
    if len(records) != plan['budget']['matrices'] or pairs > plan['budget']['pair_circuits'] or recipe(root, plan_path) != pinned:
        raise ValueError('Geometry recipe or budget changed')
    outcome = dict(study=plan['study'], status='complete', recipe=pinned, results=records,
                   wall_seconds=time.perf_counter()-start, pair_circuits=pairs,
                   target_columns_read=False, test_rows_read=False, post_final_test_exposure=True,
                   predictor_fits=0, shots=0, hardware_jobs=0,
                   interpretation='Scale affects fixed training geometry. No predictive outcome, scale selection or model promotion follows.')
    (output / 'outcome.json').write_text(json.dumps(outcome, indent=2) + '\n')
    return outcome


def collect(root, plan_path, directory):
    plan, parent, table = inputs(root, plan_path)
    outcome = json.loads((directory / 'outcome.json').read_text())
    if outcome['recipe'] != recipe(root, plan_path):
        raise ValueError('Executed geometry recipe changed')
    for row in outcome['results']:
        path = directory / row['file']
        if digest(path) != row['matrix_sha256']:
            raise ValueError('Saved geometry matrix changed')
        saved = np.load(path)
        features = parent['four_feature_subset'] if row['inputs'] == 4 else parent['features']
        values = table[features].to_numpy()
        expected = np.pi / row['amplitude_pi_denominator'] * np.tanh((values-values.mean(axis=0))/values.std(axis=0)/2)
        np.testing.assert_allclose(saved['angles'], expected)
        for name, value in summary(saved['gram']).items():
            if value is None:
                assert row[name] is None
            else:
                np.testing.assert_allclose(row[name], value)
    return dict(status='passed', records=len(outcome['results']), outcome_sha256=digest(directory / 'outcome.json'),
                predictor_fits=0, new_quantum_states=0, target_columns_read=False, test_rows_read=False)

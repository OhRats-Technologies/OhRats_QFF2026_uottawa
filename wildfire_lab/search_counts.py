"""Score measured basis-start grids and freeze training-only parameter choices."""
from datetime import datetime
import json
import numpy as np
from wildfire_lab.selection import energies
from wildfire_lab.selector_sector import Sector, sample, diagonal_sqd
from wildfire_lab.mitigation_hardware import sha, write


def score(counts, objective):
    n = len(objective['linear'])
    states = np.asarray([int(key.replace(' ', ''), 2) for key in counts], dtype=np.int64)
    frequencies = np.asarray(list(counts.values()))
    bits = ((states[:, None] >> np.arange(n)) & 1).astype(float)
    costs = energies(objective, bits)
    feasible = bits.sum(axis=1) == objective['k']
    valid_counts = {str(int(state)): int(count) for state, count, valid
                    in zip(states, frequencies, feasible) if valid}
    result = dict(shots=int(frequencies.sum()), feasible_shots=int(frequencies[feasible].sum()),
                  unconditional_expected_objective=float(frequencies @ costs/frequencies.sum()),
                  conditional_expected_objective=(float(frequencies[feasible] @ costs[feasible]/
                      frequencies[feasible].sum()) if feasible.any() else None),
                  measured_counts=counts, feasible_counts=valid_counts)
    if valid_counts:
        index = min(np.flatnonzero(feasible), key=lambda i: (costs[i], states[i]))
        result.update(selected_indices=np.flatnonzero(bits[index]).tolist(),
                      objective=float(costs[index]), unique_subsets=len(valid_counts))
    return result


def timing(child):
    metrics = json.loads((child/'metrics.json').read_text())
    charge = metrics['usage'].get('quantum_seconds', metrics['usage'].get('qpu_charge_time_seconds'))
    assert charge is not None
    timestamps = metrics.get('timestamps', {})
    elapsed = None
    if timestamps.get('created') and timestamps.get('finished'):
        elapsed = (datetime.fromisoformat(timestamps['finished'].replace('Z', '+00:00'))-
                   datetime.fromisoformat(timestamps['created'].replace('Z', '+00:00'))).total_seconds()
    usage = json.loads((child/'usage.json').read_text())
    return dict(charged_seconds=float(charge), job_usage_seconds=usage,
                created_to_finished_seconds=elapsed, timestamps=timestamps)


def analyze(output):
    if (output/'analysis.json').exists():
        return json.loads((output/'analysis.json').read_text())
    receipt = json.loads((output/'prepared.json').read_text())
    cohorts, choices = [], []
    charged, shots = 0., 0
    for job, case in zip(receipt['jobs'], receipt['cases'], strict=True):
        child = output/job['label']
        assert json.loads((child/'status.json').read_text())['status'] == 'DONE'
        physical = json.loads((child/'counts.json').read_text())['counts']
        obj = {key: np.asarray(value) if isinstance(value, list) else value
               for key, value in case['objective'].items()}
        rows = []
        for index, (record, counts) in enumerate(zip(job['records'], physical, strict=True)):
            assert sum(counts.values()) == job['shots']
            if record['kind'] == 'calibration':
                continue
            rows.append(dict(index=index, specification=record, ideal=case['ideal'][index],
                             **score(counts, obj)))
        eligible = [row for row in rows if row['specification']['kind'] == 'candidate'
                    and row['feasible_shots'] > 0]
        resources = timing(child)
        charged += resources['charged_seconds']
        shots += sum(sum(record.values()) for record in physical)
        if not eligible:
            cohorts.append(dict(pool_size=case['pool_size'], features=case['features'],
                                objective=case['objective'], rows=rows, resources=resources,
                                status='no_feasible_candidate', native_reference=case['dicke_reference']))
            continue
        winner = min(eligible, key=lambda row: (row['unconditional_expected_objective'], row['index']))
        sqd = diagonal_sqd(obj, dict(counts=winner['feasible_counts']))
        np.testing.assert_allclose(sqd['sqd_energy'], winner['objective'], atol=1e-8)
        sector = Sector(obj)
        uniform = [sample(sector, np.full(len(sector.states), 1/len(sector.states)),
                          winner['feasible_shots'], 901+replicate) for replicate in range(20)]
        choices.append(dict(pool_size=case['pool_size'], index=winner['index'],
                            parameters=winner['specification']['parameters'],
                            initial=winner['specification']['initial'],
                            selected_indices=winner['selected_indices'],
                            selection_criterion='unconditional full training-QUBO expectation',
                            feasible_shots=winner['feasible_shots'], objective=winner['objective']))
        cohorts.append(dict(pool_size=case['pool_size'], features=case['features'],
                            objective=case['objective'], rows=rows, winner_index=winner['index'],
                            winner_sqd=sqd, exact_objective=float(sector.cost.min()),
                            matched_uniform_samples=uniform, native_reference=case['dicke_reference'],
                            calibration=[dict(record=record, counts=counts) for record, counts in
                                zip(job['records'], physical) if record['kind'] == 'calibration'],
                            resources=resources))
    result = dict(stage='hardware_exploration', backend=receipt['plan']['backend'],
                  plan_sha256=receipt['plan_sha256'], prepared_sha256=sha(output/'prepared.json'),
                  cohorts=cohorts, choices=choices, physical_shots=shots, hardware_jobs=len(cohorts),
                  charged_seconds=charged, final_test_accessed=False,
                  code_sha256=sha(__import__('pathlib').Path(__file__)),
                  limitation='Training hardware grid selection; winner bias requires separate frozen confirmation. Conditional filtering is a diagnostic, not the selection criterion. Diagonal SQD cannot add unsampled states.')
    write(output/'analysis.json', result)
    with (output/'choices.json').open('x') as stream:
        json.dump(dict(choices=choices, analysis_sha256=sha(output/'analysis.json')), stream, indent=2)
    return result

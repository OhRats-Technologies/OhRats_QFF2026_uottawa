"""Measured shot-count sweep with retained uniform draws and objective controls."""
import base64
import json
from pathlib import Path
import zlib
import numpy as np
from wildfire_lab.search_counts import score, timing
from wildfire_lab.selector_sector import Sector, diagonal_sqd
from wildfire_lab.selector_hardware_analysis import assignment, observed_readout
from wildfire_lab.mitigation_hardware import sha, write


def wilson(successes, trials, z=1.959963984540054):
    p = successes/trials
    denominator = 1+z*z/trials
    center = (p+z*z/(2*trials))/denominator
    radius = z*np.sqrt(p*(1-p)/trials+z*z/(4*trials*trials))/denominator
    return [max(0., float(center-radius)), min(1., float(center+radius))]


def uniform_control(sector, budget, repeats, seed):
    if budget == 0:
        return dict(draw_budget=0, status='no_accepted_draws')
    indices = np.random.default_rng(seed).integers(len(sector.states), size=(repeats, budget), dtype=np.uint16)
    energies = sector.cost[indices]
    minima = energies.min(axis=1)
    exact = float(sector.cost.min())
    best = indices[np.arange(repeats), energies.argmin(axis=1)]
    optimum = np.isclose(minima, exact, rtol=0., atol=1e-9)
    counts = np.asarray([len(np.unique(row)) for row in indices])
    optimal_states = int(np.isclose(sector.cost, exact, rtol=0., atol=1e-9).sum())
    return dict(draw_budget=budget, replicates=repeats, seed=seed,
        encoded_indices=base64.b64encode(zlib.compress(indices.astype('<u2').tobytes())).decode(),
        encoding='zlib/base64 little-endian uint16 feasible-sector indices; row-major',
        selected_states=sector.states[best].tolist(), minima=minima.tolist(),
        gaps=(minima-exact).tolist(), mean_gap=float(np.mean(minima-exact)),
        optimum_trials=int(optimum.sum()), unique_counts=counts.tolist(),
        exact_uniform_optimum_probability=float(-np.expm1(budget*np.log1p(-optimal_states/len(sector.states)))))


def analyze(output):
    if (output/'analysis.json').exists():
        return json.loads((output/'analysis.json').read_text())
    receipt = json.loads((output/'prepared.json').read_text())
    plan = receipt['plan']
    sectors, controls = {}, {}
    cases = {case['pool_size']: case for case in receipt['cases']}
    for n, case in cases.items():
        objective = {key: np.asarray(value) if isinstance(value, list) else value
                     for key, value in case['objective'].items()}
        sectors[n] = (objective, Sector(objective))
    rows, physical, resources, compilation = [], {}, {}, {}
    for job in receipt['jobs']:
        child = output/job['label']
        assert json.loads((child/'status.json').read_text())['status'] == 'DONE'
        counts = json.loads((child/'counts.json').read_text())['counts']
        assert len(counts) == len(job['records'])
        assert all(sum(c.values()) == job['shots'] for c in counts)
        physical[job['label']] = counts
        compilation[job['label']] = job['records']
        resources[job['label']] = timing(child)
        for index, record in enumerate(job['records']):
            if record['kind'] == 'calibration':
                continue
            n = record['pool_size']
            objective, sector = sectors[n]
            scored = score(counts[index], objective)
            calibrations = [(r, c) for r, c in zip(job['records'], counts)
                            if r['kind'] == 'calibration' and r['pool_size'] == n
                            and r['measured_wires'] == record['measured_wires']]
            channels = assignment(next(c for r, c in calibrations if r['prepared_bit'] == 0),
                                  next(c for r, c in calibrations if r['prepared_bit'] == 1), n)
            row = dict(job_label=job['label'], arm=job['arm'],
                specification=record, features=cases[n]['features'],
                objective_specification=cases[n]['objective'],
                exact_objective=float(sector.cost.min()), feasible_fraction=scored['feasible_shots']/job['shots'],
                wilson95=wilson(scored['feasible_shots'], job['shots']),
                whole_job_charged_seconds=resources[job['label']]['charged_seconds'],
                assignment=channels.tolist(), **scored)
            if scored['feasible_counts']:
                row['sqd'] = diagonal_sqd(objective, dict(counts=scored['feasible_counts']))
                row['gap_to_exact'] = scored['objective']-row['exact_objective']
                row['optimum_found'] = bool(abs(row['gap_to_exact']) <= 1e-9)
                row['readout'] = observed_readout(counts[index], channels,
                                                 sorted(map(int, scored['feasible_counts'])))
            else:
                row['status'] = 'no_feasible_sample'
            if record['kind'] == 'confirmation':
                row['uniform_controls'] = {}
                for label, budget in [('physical', job['shots']), ('accepted', scored['feasible_shots'])]:
                    key = f'{n}-{budget}'
                    if key not in controls:
                        controls[key] = uniform_control(sector, budget, plan['uniform_replicates'],
                                                        plan['uniform_seed']+n)
                    row['uniform_controls'][label] = key
            rows.append(row)
    result = dict(study=plan['study'], backend=plan['backend'], plan_sha256=receipt['plan_sha256'],
        parent_prepared_sha256=plan['parent_prepared_sha256'], rows=rows, uniform_controls=controls,
        physical_counts=physical, compilation=compilation, resources=resources,
        charged_seconds=sum(r['charged_seconds'] for r in resources.values()),
        hardware_jobs=len(resources), physical_shots=sum(sum(c.values()) for job in physical.values() for c in job),
        classical_uniform_draws=sum(c.get('draw_budget', 0)*c.get('replicates', 0) for c in controls.values()),
        final_test_accessed=False, predictor_fits=0, code_sha256=sha(Path(__file__)),
        limitation='One independent job per device/shot/arm, fixed staggered order; calibration drift remains confounded. Wilson intervals assume independent Bernoulli shots and do not cover drift/correlated execution errors. Compare full-shot and accepted-shot uniform feasible draws separately. Charge covers all selector/control/calibration PUBs in the job, not an individual circuit. Actual diagonal SQD only chooses among observed states. No predictor refit, error-correction claim, intrinsic device ranking or quantum advantage.')
    write(output/'analysis.json', result)
    return result

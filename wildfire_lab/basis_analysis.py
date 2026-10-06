"""Compare frozen basis circuits across actual acquisition arms, without retuning."""
import json
from pathlib import Path
import numpy as np
from wildfire_lab.search_counts import score, timing
from wildfire_lab.selector_sector import Sector, diagonal_sqd
from wildfire_lab.selector_hardware_analysis import assignment, observed_readout
from wildfire_lab.mitigation_hardware import sha, write


def analyze(output):
    if (output/'analysis.json').exists():
        return json.loads((output/'analysis.json').read_text())
    receipt = json.loads((output/'prepared.json').read_text())
    cases = {case['pool_size']: case for case in receipt['cases']}
    rows, physical, resources = [], {}, {}
    for job in receipt['jobs']:
        child = output/job['label']
        assert json.loads((child/'status.json').read_text())['status'] == 'DONE'
        counts = json.loads((child/'counts.json').read_text())['counts']
        assert len(counts) == len(job['records'])
        assert all(sum(c.values()) == job['shots'] for c in counts)
        physical[job['arm']] = counts
        resources[job['arm']] = timing(child)
        for index, record in enumerate(job['records']):
            if record['kind'] == 'calibration':
                continue
            n = record['pool_size']
            case = cases[n]
            obj = {key: np.asarray(value) if isinstance(value, list) else value
                   for key, value in case['objective'].items()}
            sector = Sector(obj)
            scored = score(counts[index], obj)
            calibrations = [(spec, measured) for spec, measured in zip(job['records'], counts)
                            if spec['kind'] == 'calibration' and spec['pool_size'] == n
                            and spec['measured_wires'] == record['measured_wires']]
            zero = next(c for r, c in calibrations if r['prepared_bit'] == 0)
            one = next(c for r, c in calibrations if r['prepared_bit'] == 1)
            channels = assignment(zero, one, n)
            row = dict(arm=job['arm'], specification=record, features=case['features'],
                       objective_specification=case['objective'],
                       exact_objective=float(sector.cost.min()), assignment=channels.tolist(), **scored)
            if scored['feasible_counts']:
                row['sqd'] = diagonal_sqd(obj, dict(counts=scored['feasible_counts']))
                row['gap_to_exact'] = scored['objective']-row['exact_objective']
                row['readout'] = observed_readout(counts[index], channels,
                                                 sorted(map(int, scored['feasible_counts'])))
            else:
                row['status'] = 'no_feasible_sample'
            rows.append(row)
    result = dict(study=receipt['plan']['study'], backend=receipt['plan']['backend'],
                  plan_sha256=receipt['plan_sha256'], choices_sha256=receipt['plan']['choices_sha256'],
                  rows=rows, physical_counts=physical, resources=resources,
                  charged_seconds=sum(r['charged_seconds'] for r in resources.values()),
                  physical_shots=sum(sum(c.values()) for arm in physical.values() for c in arm),
                  hardware_jobs=len(resources), final_test_accessed=False,
                  code_sha256=sha(Path(__file__)),
                  limitation='Frozen circuit confirmation, one raw/combined pair per device. No retuning or intrinsic device ranking. Readout weights cover only actually observed feasible states and add no SQD states. Combined DD/twirling cannot attribute an isolated effect. Reused climate folds are not independent prediction validation.')
    write(output/'analysis.json', result)
    return result

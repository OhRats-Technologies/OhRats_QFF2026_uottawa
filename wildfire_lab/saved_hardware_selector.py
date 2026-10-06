"""Audit measured selector evidence by arithmetic, without fitting or sampling."""
import json
from itertools import combinations
from zipfile import ZipFile
import numpy as np
import pandas as pd
from wildfire_lab.forest_collect import digest
from wildfire_lab.saved_forest_models import check
from wildfire_lab.selector_hardware_analysis import assignment, observed_readout
from wildfire_lab.selection import energies


def close(actual, expected):
    np.testing.assert_allclose(actual, expected, atol=1e-7, rtol=1e-9)


def counts_checked(counts, shots, width):
    assert sum(counts.values()) == shots
    assert all(type(v) is int and v > 0 for v in counts.values())
    assert all(len(s) == width and set(s) <= {'0', '1'} for s in counts)


def costs_for(states, n, objective):
    bits = ((np.array(states, dtype=np.int64)[:, None] >> np.arange(n)) & 1)
    assert np.all(bits.sum(axis=1) == objective['k'])
    return energies(objective, bits)


def audit(root):
    plan_path = root/'experiments/selector_hardware.json'
    plan = json.loads(plan_path.read_text())
    result_path = root/'docs/results/selector-hardware.json'
    result = json.loads(result_path.read_text())
    assert result['plan_sha256'] == digest(plan_path)
    index = json.loads((root/'docs/results/selector-scaling.json').read_text())
    bundle = root/index['bundle']
    assert digest(bundle) == index['bundle_sha256']
    with ZipFile(bundle) as archive:
        raw = archive.read('evidence.json')
    import hashlib
    assert hashlib.sha256(raw).hexdigest() == plan['parent_evidence_sha256']
    source = json.loads(raw)
    table_path = root/source['intent']['plan']['dataset']
    assert digest(table_path) == source['intent']['dataset_sha256']
    table = pd.read_csv(table_path)
    first, last, vfirst, vlast = plan['fold']
    train = table[table.year.between(first, last)]
    valid = table[table.year.between(vfirst, vlast)]
    cohorts = {len(c['features']):c for c in source['cohorts'] if c['fold'] == plan['fold']}
    checked, fits, uniform_records = 0, 0, 0
    for arm in plan['arms']:
        records = result['raw_records'][arm]
        assert len(records) == 18
        for index, compiled in enumerate(result['compiled_records'][:6]):
            label = compiled['label']
            n, policy = label['pool_size'], label['policy']
            width = n+label['counter_qubits']
            counts = records[index]
            for entry in [counts, records[6+2*index], records[7+2*index]]:
                counts_checked(entry, plan['selector_shots'], width)
            row = next(r for r in result['rows'] if (r['arm'],r['pool_size'],r['policy']) == (arm,n,policy))
            saved, clean = {}, 0
            for text, weight in counts.items():
                state = int(text, 2)
                candidate = state & ((1 << n)-1)
                if candidate.bit_count() == 4:
                    key = str(candidate)
                    saved[key] = saved.get(key, 0)+weight
                    clean += weight if state >> n == 0 else 0
            assert saved == row['observed_feasible_counts']
            assert row['physical_shots'] == plan['selector_shots']
            assert row['feasible_shots'] == sum(saved.values())
            assert row['clean_counter_feasible_shots'] == clean
            close(row['feasible_fraction'], sum(saved.values())/plan['selector_shots'])
            close(row['clean_counter_feasible_fraction'], clean/plan['selector_shots'])
            channels = assignment(records[6+2*index], records[7+2*index], width)
            close(row['assignment'], channels)
            if not saved:
                assert row['status'] == 'no_feasible_hardware_sample'
                assert f'{arm}-{n}-{policy}' not in result['models']
                checked += 1
                continue
            cohort = cohorts[n]
            objective = {k:np.array(v) if isinstance(v,list) else v for k,v in cohort['objective'].items()}
            states = sorted(map(int,saved))
            values = costs_for(states,n,objective)
            chosen = states[int(np.argmin(values))]
            indices = [j for j in range(n) if chosen >> j & 1]
            assert indices == row['selected_indices']
            all_states = [sum(1 << j for j in subset) for subset in combinations(range(n),4)]
            minimum = float(costs_for(all_states,n,objective).min())
            close(row['objective'],values.min())
            close(row['gap_to_exact'],values.min()-minimum)
            close(row['sqd']['sqd_energy'],values.min())
            close(row['sqd']['sampled_minimum'],values.min())
            assert row['sqd']['basis_size'] == len(states)
            close(row['sqd']['projected_off_diagonal_max'],0)
            reweighted = observed_readout(counts,channels[:n],states)
            for key in ['quasi_weights','conditional_positive_weights','signed_mass','positive_mass','largest_single_channel_condition']:
                close(row['readout'][key],reweighted[key])
            assert row['readout']['basis_states'] == states
            assert row['readout']['negative_entries'] == reweighted['negative_entries']
            uniforms = row['matched_uniform_records']
            assert len(uniforms) == 20
            for sample in uniforms:
                assert sum(sample['counts'].values()) == row['feasible_shots'] == sample['shots']
                sample_states = sorted(map(int,sample['counts']))
                sample_values = costs_for(sample_states,n,objective)
                close(sample['objective'],sample_values.min())
                close(sample['gap'],sample_values.min()-minimum)
                assert sample['optimum_found'] == bool(np.isclose(sample_values.min(),minimum,atol=1e-9,rtol=0))
            close(row['matched_uniform_mean_gap'],np.mean([s['gap'] for s in uniforms]))
            assert row['matched_uniform_optimum_trials'] == sum(s['optimum_found'] for s in uniforms)
            uniform_records += len(uniforms)
            model = result['models'][f'{arm}-{n}-{policy}']
            assert model['rows'][0]['features'] == [cohort['features'][j] for j in indices]
            assert row['predictions'] == model['rows']
            count, _ = check(train,valid,model,source['intent']['plan'])
            fits += count
            checked += 1
    assert checked == 12 and fits == 33
    assert result['physical_shots'] == 2*18*plan['selector_shots']
    close(result['quantum_seconds_total'],sum(t['quantum_seconds'] for t in result['timings'].values()))
    return dict(status='verified',selector_records=checked,predictor_equations=fits,
                uniform_count_records=uniform_records,physical_shots=result['physical_shots'],
                charged_qpu_seconds=result['quantum_seconds_total'],result_sha256=digest(result_path),
                new_fits=0,new_quantum_evaluations=0,new_draws=0,network_requests=0,
                limitation='Arithmetic replay of published counts, diagonal energies, preprocessing and predictions; not a new acquisition or independent predictive replication.')

"""Replay later selector studies without their producing quantum dependencies."""
import numpy as np
from wildfire_lab.saved_search import prediction, metrics


def models(cohort):
    checked = 0
    for result in cohort['models'].values():
        for row in result['rows']:
            if row['model'] == 'ridge':
                cross = result['scaled_cross']
            elif row['model'] == 'qsvr':
                cross = result['quantum_cross']
            else:
                x, raw = np.asarray(result['scaled_train']), np.asarray(result['scaled_cross'])
                cross = np.exp(-result['rbf_gamma']*np.sum((raw[:, None]-x[None])**2, axis=-1))
            prediction(row, result['preprocessing'], cross)
            checked += 1
    return checked


def traces(runs, costs):
    calls = 0
    for run in runs:
        p = np.asarray(run['probability'])
        np.testing.assert_allclose(p.sum(), 1., atol=1e-10)
        assert p.min() >= 0
        np.testing.assert_allclose(p @ costs, run['expected_objective'], atol=1e-9)
        assert len(run['trace']) == run['objective_calls']
        calls += len(run['trace'])
    return calls


def samples(records, states, costs):
    lookup = {str(int(state)): index for index, state in enumerate(states)}
    draws = 0
    for record in records:
        assert sum(record['counts'].values()) == record['shots']
        indices = [lookup[state] for state in record['counts']]
        np.testing.assert_allclose(min(costs[i] for i in indices), record['objective'], atol=1e-9)
        np.testing.assert_allclose(record['objective']-costs.min(), record['gap'], atol=1e-9)
        draws += record['shots']
    return draws


def shallow(evidence):
    equations, calls, draws = 0, 0, 0
    for cohort in evidence['cohorts']:
        states, costs = np.asarray(cohort['sector_states']), np.asarray(cohort['sector_objectives'])
        assert all(int(state).bit_count() == 4 for state in states)
        calls += traces(cohort['runs'].values(), costs)
        for run in cohort['runs'].values():
            assert len(run['parameters']) == 2*run['depth']-1
            assert run['initial_indices'] in cohort['initial'].values()
        draws += samples(cohort['samples'], states, costs)
        for name, sqd in cohort['sqd'].items():
            representative = next(s for s in cohort['samples'] if s['policy'] == name and s['replicate'] == 0)
            np.testing.assert_allclose(sqd['sqd_energy'], representative['objective'], atol=1e-8)
        equations += models(cohort)
    assert calls == evidence['optimizer_calls']
    assert draws == evidence['classical_draws']
    assert equations == evidence['model_fits']
    return dict(prediction_equations=equations, optimizer_trace_records=calls, preserved_draws=draws)


def objective(evidence):
    equations, calls, draws, inner_fits = 0, 0, 0, 0
    for cohort in evidence['cohorts']:
        for row in cohort['tuning']:
            actual, predicted = [], []
            for split in row['splits']:
                assert max(split['training_years']) < min(split['validation_years'])
                assert max(split['validation_years']) <= cohort['fold'][1]
                assert len(split['selected_indices']) == 4
                actual.extend(split['actual_ha'])
                predicted.extend(split['predicted_ha'])
                inner_fits += 1
            metrics(dict(row, actual_ha=actual, predicted_ha=predicted))
        for proxy, chosen in cohort['chosen_weights'].items():
            best = min((r for r in cohort['tuning'] if r['proxy'] == proxy), key=lambda row: row['mae_ha'])
            assert chosen == best['weight']
        for selector in cohort['selectors'].values():
            states, costs = np.asarray(selector['sector_states']), np.asarray(selector['sector_objectives'])
            calls += traces(selector['runs'], costs)
            winner = min(range(len(selector['runs'])), key=lambda i: selector['runs'][i]['expected_objective'])
            assert winner == selector['chosen_run']
            draws += samples(selector['samples'], states, costs)
            np.testing.assert_allclose(selector['sqd']['sqd_energy'], selector['samples'][0]['objective'], atol=1e-8)
        equations += models(cohort)
    assert equations+inner_fits == evidence['model_fits']
    assert calls == evidence['objective_calls']
    assert draws == evidence['classical_sample_draws']
    return dict(prediction_equations=equations, inner_fit_score_records=inner_fits,
                optimizer_trace_records=calls, preserved_draws=draws)

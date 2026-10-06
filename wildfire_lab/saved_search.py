"""Arithmetic replay of saved searches: no fitting, states, draws or network."""
import hashlib
import json
from zipfile import ZipFile
import numpy as np


def metrics(row):
    actual, prediction = np.asarray(row['actual_ha']), np.asarray(row['predicted_ha'])
    residual = prediction-actual
    for name, value in dict(mae_ha=np.abs(residual).mean(),
                            rmse_ha=np.sqrt(np.mean(residual**2)), bias_ha=residual.mean()).items():
        np.testing.assert_allclose(value, row[name], atol=1e-8, rtol=1e-9)


def prediction(row, preprocessing, cross):
    parameters = row['parameters']
    matrix = np.asarray(cross)
    if 'coef' in parameters:
        scaled = matrix @ np.asarray(parameters['coef'])+parameters['intercept']
    else:
        scaled = matrix[:, parameters['support']] @ np.asarray(parameters['dual_coef'])
        scaled += parameters['intercept']
    np.testing.assert_allclose(scaled, row['predicted_scaled'], atol=1e-8)
    values = np.maximum(0, np.expm1(scaled*preprocessing['y_scale']+preprocessing['y_mean']))
    np.testing.assert_allclose(values, row['predicted_ha'], atol=1e-7, rtol=1e-9)
    metrics(row)


def selector(evidence):
    fits, traces, draws = 0, 0, 0
    for cohort in evidence['cohorts']:
        states = np.asarray(cohort['sector_states'])
        costs = np.asarray(cohort['sector_objectives'])
        lookup = {str(int(state)): index for index, state in enumerate(states)}
        assert all(int(state).bit_count() == 4 for state in states)
        for run in cohort['runs']:
            probability = np.asarray(run['probability'])
            np.testing.assert_allclose(probability.sum(), 1., atol=1e-10)
            assert probability.min() >= 0
            np.testing.assert_allclose(probability @ costs, run['expected_objective'], atol=1e-9)
            optimum = np.isclose(costs, costs.min(), atol=1e-9, rtol=0)
            np.testing.assert_allclose(probability[optimum].sum(), run['optimum_probability'])
            assert run['objective_calls'] == len(run['trace']) <= run['call_cap']
            traces += len(run['trace'])
        for name, index in cohort['winners'].items():
            run = cohort['runs'][index]
            assert run['depth'] == int(name[-1])
            assert run['expected_objective'] == min(
                r['expected_objective'] for r in cohort['runs'] if r['depth'] == run['depth'])
        representatives = {}
        for sample in cohort['samples']:
            assert sum(sample['counts'].values()) == sample['shots']
            indices = [lookup[state] for state in sample['counts']]
            best = min(indices, key=lambda index: costs[index])
            np.testing.assert_allclose(costs[best], sample['objective'], atol=1e-9)
            np.testing.assert_allclose(costs[best]-costs.min(), sample['gap'], atol=1e-9)
            assert sample['selected_indices'] == [i for i in range(cohort['selector_qubits'])
                                                  if (int(states[best]) >> i) & 1]
            draws += sample['shots']
            if sample['shots'] == 1024 and sample['replicate'] == 0:
                representatives[sample['policy']] = sample
        for name, sqd in cohort['sqd'].items():
            np.testing.assert_allclose(sqd['sqd_energy'], representatives[name]['objective'], atol=1e-8)
        for model in cohort['models'].values():
            for row in model['rows']:
                if row['model'] == 'ridge':
                    cross = model['scaled_cross']
                elif row['model'] == 'qsvr':
                    cross = model['quantum_cross']
                else:
                    x, cross = np.asarray(model['scaled_train']), np.asarray(model['scaled_cross'])
                    cross = np.exp(-model['rbf_gamma']*np.sum((cross[:, None]-x[None])**2, axis=-1))
                prediction(row, model['preprocessing'], cross)
                fits += 1
    assert fits == evidence['model_fits']
    assert traces == evidence['optimizer_calls']
    assert draws == evidence['classical_sample_draws']
    return dict(prediction_equations=fits, optimizer_trace_records=traces,
                preserved_sample_draws=draws)


def nested(evidence):
    equations, candidates, fits = 0, 0, 0
    for cohort in evidence['cohorts']:
        tuning = cohort['tuning']
        actual = []
        for split in tuning['inner_splits']:
            assert max(split['train_years']) < min(split['validation_years'])
            if split['selection'] is not None:
                assert split['selection']['labelled_years'] == split['train_years']
            actual.extend(split['actual_ha'])
        for candidate in tuning['candidates']:
            metrics(dict(candidate, actual_ha=actual))
            candidates += 1
        for kind, specification in tuning['chosen'].items():
            best = min((r for r in tuning['candidates'] if r['specification']['model'] == kind),
                       key=lambda row: row['mae_ha'])
            assert specification == best['specification']
        fits += tuning['predictor_fits']+len(cohort['results'])
        for row in cohort['results'].values():
            prediction(row, row['preprocessing'], row['cross_matrix'])
            equations += 1
    assert fits == evidence['model_fits']
    return dict(selected_prediction_equations=equations, candidate_score_records=candidates,
                saved_predictor_fits=fits)


def collect(root, study):
    index = json.loads((root/f'docs/results/{study}.json').read_text())
    path = root/index['bundle']
    assert hashlib.sha256(path.read_bytes()).hexdigest() == index['bundle_sha256']
    with ZipFile(path) as archive:
        assert archive.namelist() == ['evidence.json']
        raw = archive.read('evidence.json')
        assert hashlib.sha256(raw).hexdigest() == index['evidence_sha256']
        evidence = json.loads(raw)
    assert evidence['status'] == 'complete' and evidence['hardware_jobs'] == 0
    assert evidence['final_test_accessed'] is False
    if study in {'shallow-preparation', 'objective-alignment'}:
        from wildfire_lab.saved_search_extensions import shallow, objective
        result = shallow(evidence) if study == 'shallow-preparation' else objective(evidence)
    else:
        result = selector(evidence) if study == 'selector-multistart' else nested(evidence)
    for row in evidence['rows']:
        metrics(row)
    result.update(predictor_fits=0, new_quantum_states=0, new_draws=0, network_requests=0,
                  hardware_submissions=0, status='passed')
    return result

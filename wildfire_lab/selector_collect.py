"""Arithmetic collection of larger-pool sampling and prediction evidence; no draws."""
import numpy as np
import pandas as pd
from wildfire_lab.forest_run import digest
from wildfire_lab.forest_collect import check_preprocessing
from wildfire_lab.saved_forest_models import check
from wildfire_lab.selection import energies


def selection(cohort, plan):
    obj = {k:np.array(v) if isinstance(v,list) else v for k,v in cohort['objective'].items()}
    n = len(cohort['features'])
    states = np.array(cohort['sector_states'])
    bits = ((states[:,None] >> np.arange(n)) & 1).astype(float)
    from math import comb
    assert len(states)==comb(n,obj['k']) and len(np.unique(states))==len(states)
    assert np.all(bits.sum(axis=1)==obj['k'])
    costs = energies(obj,bits)
    np.testing.assert_allclose(costs,cohort['sector_objectives'],atol=1e-9)
    np.testing.assert_allclose(costs.min(),cohort['exact_objective'],atol=1e-9)
    assert np.flatnonzero(bits[np.argmin(costs)]).tolist()==cohort['choices']['exact']
    lookup = {int(s):i for i,s in enumerate(states)}
    optimum = np.isclose(costs,costs.min(),atol=1e-9,rtol=0)
    for policy in cohort['policies'].values():
        p = np.array(policy['probability'])
        assert p.shape==costs.shape and p.min()>=0
        np.testing.assert_allclose(p.sum(),1.,atol=1e-10)
        np.testing.assert_allclose(p@costs,policy['expected_objective'],atol=1e-9)
        np.testing.assert_allclose(p[optimum].sum(),policy['optimum_probability'],atol=1e-10)
        for shots, value in policy['probability_find_optimum'].items():
            expected = -np.expm1(int(shots)*np.log1p(-min(p[optimum].sum(),1-1e-15)))
            np.testing.assert_allclose(value,expected,atol=1e-10)
    for row in cohort['samples']:
        assert sum(row['counts'].values())==row['shots']
        assert all(isinstance(v,int) and v>0 for v in row['counts'].values())
        indices = np.array(sorted(lookup[int(state)] for state in row['counts']))
        best = indices[np.argmin(costs[indices])]
        assert row['selected_indices']==np.flatnonzero(bits[best]).tolist()
        np.testing.assert_allclose(row['objective'],costs[best],atol=1e-9)
        np.testing.assert_allclose(row['gap'],costs[best]-costs.min(),atol=1e-9)
        assert row['optimum_found']==bool(optimum[best])
    actual = {(r['policy'],r['shots'],r['replicate']) for r in cohort['samples']}
    expected = {(name,shots,replicate) for name in cohort['policies']
                for shots in plan['shot_budgets'] for replicate in range(plan['sampling_replicates'])}
    assert actual==expected and len(actual)==len(cohort['samples'])
    for name, record in cohort['representative'].items():
        expected = next(r for r in cohort['samples'] if r['policy']==name and r['replicate']==0
                        and r['shots']==max(plan['shot_budgets']))
        assert expected['counts']==record['counts']
        assert cohort['choices'][name]==record['selected_indices']
        np.testing.assert_allclose(cohort['policies'][name]['sqd']['sqd_energy'],record['objective'],atol=1e-8)
    return len(cohort['samples'])


def audit(root, evidence):
    intent, cohorts = evidence['intent'], evidence['cohorts']
    plan = intent['plan']
    assert digest(root/plan['dataset'])==intent['dataset_sha256']
    table = pd.read_csv(root/plan['dataset'])
    assert table.year.tolist()==list(range(1988,2019))
    assert table.year.tolist()==list(range(1988,2019))
    assert len(cohorts)==len(plan['folds'])*len(plan['pool_sizes'])
    fits, pairs, samples = 0, 0, 0
    for cohort in cohorts:
        first,last,vfirst,vlast = cohort['fold']
        assert cohort['fold'] in plan['folds']
        train = table[table.year.between(first,last)]
        valid = table[table.year.between(vfirst,vlast)]
        columns = cohort['features']
        assert columns == plan['features'][:cohort['logical_selector_qubits']]
        p = cohort['selector_preprocessing']
        check_preprocessing(train[columns].to_numpy(), valid[columns].to_numpy(),
                            train.mean_reported_size_ha.to_numpy(),
                            dict(preprocessing=p,scaled_train=cohort['selector_train'],
                                 scaled_cross=(np.where(np.isnan(valid[columns].to_numpy()),p['median'],valid[columns].to_numpy())-p['mean'])/p['scale'],
                                 scaled_targets=cohort['selector_targets']))
        samples += selection(cohort,plan)
        for name, model in cohort['models'].items():
            assert model['rows'][0]['features']==[columns[i] for i in cohort['choices'][name]]
            checked, count = check(train,valid,model,plan)
            fits += checked
            pairs += count
            for row in model['rows']:
                saved = next(r for r in evidence['rows'] if r['fold']==cohort['fold']
                             and r['pool_size']==len(columns) and r['selector']==name and r['model']==row['model'])
                np.testing.assert_allclose(saved['predicted_ha'],row['predicted_ha'],atol=1e-9)
    assert fits==plan['budget']['model_fits']==evidence['model_fits']
    assert pairs==evidence['pair_circuits']
    assert not evidence['final_test_accessed'] and evidence['hardware_jobs']==0
    assert samples==len(cohorts)*4*plan['sampling_replicates']*len(plan['shot_budgets'])
    assert not evidence['final_test_accessed'] and evidence['hardware_jobs']==0
    return dict(status='verified',predictor_equations_checked=fits,kernel_records_checked=fits//3,
                sampling_count_records_checked=samples,sqd_records_checked=len(cohorts)*4,
                saved_pair_circuits=pairs,new_predictor_fits=0,new_quantum_evaluations=0,new_draws=0,
                limitation='Checks saved costs/count minima, probability arithmetic, train-only scaling and fit equations; does not regenerate quantum states, MI objectives or kernels, rerun optimizers or establish independent validation.')


def audit_order(root, evidence):
    intent = evidence['intent']
    plan = intent['plan']
    assert digest(root/plan['dataset'])==intent['dataset_sha256']
    table = pd.read_csv(root/plan['dataset'])
    fits, pairs = 0, 0
    for fold in evidence['folds']:
        first,last,vfirst,vlast = fold['fold']
        assert fold['fold'] in plan['folds']
        train, valid = table[table.year.between(first,last)], table[table.year.between(vfirst,vlast)]
        for record in fold['conditions'].values():
            checked,count = check(train,valid,record,plan)
            fits += checked
            pairs += count
    assert fits==plan['budget']['model_fits']==evidence['model_fits']
    assert pairs==evidence['pair_circuits']
    return dict(status='verified',predictor_equations_checked=fits,kernel_records_checked=fits//3,
                new_predictor_fits=0,new_quantum_evaluations=0,new_draws=0,
                limitation='Arithmetic collection of post-hoc control equations; no independent confirmation.')

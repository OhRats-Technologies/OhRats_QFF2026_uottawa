"""Check the published ordering evidence without caches or scientific libraries."""
import math


def verify_order(read, sha, add):
    plan_path = 'experiments/context_input_order.json'
    result_path = 'docs/results/context-input-order.json'
    receipt_path = 'docs/data/context_input_order_verification.json'
    plan, result, receipt = read(plan_path), read(result_path), read(receipt_path)
    collection, formula = receipt['collection'], receipt['formula_audit']
    assert result['plan_sha256'] == collection['plan_sha256'] == sha(plan_path)
    assert collection['result_sha256'] == formula['result_sha256'] == sha(result_path)
    assert result['arrays_sha256'] == collection['arrays_sha256'] == formula['arrays_sha256']
    allowed = {'docs/data/annual_training.csv', 'scripts/context/ordering.py',
               'scripts/context/ordering_math.py', 'scripts/context/ordering_collect.py',
               'pyproject.toml', 'uv.lock'}
    assert set(plan['source_sha256']) == allowed
    assert plan['source_sha256'] == result['source_sha256']
    environment = {'pyproject.toml', 'uv.lock'}
    assert all(sha(path) == expected for path, expected in plan['source_sha256'].items()
               if path not in environment)
    environment_changes = {path: dict(original=expected, current=sha(path))
                           for path, expected in plan['source_sha256'].items()
                           if path in environment and sha(path) != expected}
    assert formula['audit_code_sha256'] == sha('scripts/context/ordering_audit.py')
    figure = receipt['figure']
    assert figure['path'] == 'docs/figures/context-input-order.png'
    assert figure['sha256'] == sha(figure['path'])
    assert figure['code_sha256'] == sha('scripts/context/ordering_figure.py')
    assert result['years'] == list(range(1988, 2019)) and plan['years'] == [1988, 2018]
    assert result['kernel_matrices'] == 16 and result['statevector_preparations'] == 496
    assert result['gram_entries'] == 16 * 31 ** 2
    assert [result['untranspiled_gate_counts'][g]['cx'] for g in ['linear', 'full']] == [6, 12]
    assert all(result[name] == 0 for name in ['predictor_fits', 'sampler_pair_circuits', 'shots', 'hardware_jobs'])
    expected = {f'{graph}_d{scale}_{order['name']}' for graph in plan['graphs']
                for scale in plan['amplitude_pi_denominators'] for order in plan['orders']}
    assert len(expected) == len(result['rows']) == len(collection['checked']) == len(formula['rows']) == 16
    assert all({r['key'] for r in rows} == expected for rows in
               [result['rows'], collection['checked'], formula['rows']])
    assert collection['status'] == formula['status'] == 'passed'
    assert formula['classical_amplitude_reconstructions'] == 496 and formula['new_qiskit_calls'] == 0
    assert all(r['metrics_and_state_relabelling_match'] for r in collection['checked'])
    for row in result['rows']:
        assert row['expected_symmetry'] == (row['graph'] == 'full' or row['order']['name'] in ['identity', 'reverse'])
        assert all(math.isfinite(row[key]) for key in ['max_entry_change', 'relative_frobenius_change',
                                                     'effective_rank', 'rbf_permutation_error'])
        assert row['rbf_permutation_error'] < plan['tolerance']
        if row['expected_symmetry']:
            assert row['max_entry_change'] < plan['tolerance'] and row['state_relabelling_error'] < plan['tolerance']
    assert all(r['amplitude_residual'] < plan['tolerance'] and r['kernel_residual'] < plan['tolerance']
               for r in formula['rows'])
    add('feature_order_and_coupling_control', [plan_path, result_path, receipt_path,
        'scripts/context/ordering_public.py', 'docs/figures/context-input-order.png'],
        dict(original_state_preparations=496, matrices=16, predictor_fits=0,
             current_environment_matches_original=not environment_changes,
             environment_manifest_changes=environment_changes,
             maximum_formula_residual=max(r['amplitude_residual'] for r in formula['rows']),
             chain_cx=result['untranspiled_gate_counts']['linear']['cx'],
             full_cx=result['untranspiled_gate_counts']['full']['cx']),
        'Frozen scientific source/result hashes, resource counts and recorded symmetry/direct-formula controls. '
        'Current dependency manifest differences are reported separately; this does not certify the original environment. '
        'The ignored amplitude archive is not reconstructed by this public check; repeat arithmetic collection '
        'in the original audit checkout. Expected graph symmetries, not predictive validation or a new algorithm.')

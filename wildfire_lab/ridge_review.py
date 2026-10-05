"""Separate numerical adequacy, compression fidelity and predictive comparison."""
import numpy as np


def review(seeds,plan):
    groups={}
    numerical=plan['numerical_checks'];gate=plan['quality_gate']
    for group in ['diagnostic','sampling_check']:
        samples=[s for s in seeds if s['group']==group]
        metrics=[{r['predictor']:r['metric']['average_precision'] for r in s['rows']} for s in samples]
        rows=[r for s in samples for r in s['rows']]
        checks=dict(residuals=max(r['relative_solve_residual'] for r in rows)<=numerical['relative_solve_residual_max'],
            primal_residuals=max(r.get('primal_relative_solve_residual',0) for r in rows)<=numerical['relative_solve_residual_max'],
            representations=max(r.get('primal_dual_prediction_max_abs_difference',0) for r in rows)<=numerical['primal_dual_prediction_difference_max'],
            primary_score_spread=min(r['validation_score_std'] for r in rows if r['predictor'] in ['ZZ/dense','ZZ/ideal/16'])>=numerical['primary_validation_score_std_min'])
        delta=[m['ZZ/ideal/16']-m['ZZ/dense'] for m in metrics]
        quantum={name:float(np.mean([m['ZZ/dense']-m[f'{name}/dense'] for m in metrics])) for name in ['linear','product','rbf']}
        wins=sum(m['ZZ/dense']>m['rbf/dense'] for m in metrics)
        approximation=float(np.mean(delta))>=gate['ideal_16_mean_ap_delta_min'] and \
            sum(d>=gate['ideal_16_seed_ap_delta_min'] for d in delta)>=gate['ideal_16_seeds_within_min']
        comparison=min(quantum.values())>=gate['ZZ_mean_ap_gain_vs_each_classical_min'] and wins>=gate['ZZ_seeds_beating_rbf_min']
        groups[group]=dict(numerical_adequacy=all(checks.values()),numerical_checks=checks,
            ideal_16_paired_ap_deltas=delta,ideal_16_mean_ap_delta=float(np.mean(delta)),
            approximation_gate=approximation,ZZ_mean_ap_deltas=quantum,ZZ_rbf_win_count=wins,
            predictive_comparison_gate=comparison)
    return dict(groups=groups,numerically_adequate=all(g['numerical_adequacy'] for g in groups.values()),
        approximation_sampling_check=all(g['approximation_gate'] and g['numerical_adequacy'] for g in groups.values()),
        quantum_sampling_check=all(g['predictive_comparison_gate'] and g['numerical_adequacy'] for g in groups.values()))

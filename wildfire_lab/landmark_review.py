"""Frozen landmark quality gates; paired seeds are exploratory, not new final tests."""
import numpy as np


def review(seeds,plan):
    metrics=[{r['predictor']:r['metric']['average_precision'] for r in s['rows']} for s in seeds]
    ideal=[m['ZZ/ideal/16']-m['ZZ/dense'] for m in metrics]
    shot=[m['ZZ/4096/16']-m['ZZ/dense'] for m in metrics]
    gate=plan['quality_gate']
    checks=dict(ideal_mean=float(np.mean(ideal))>=gate['ideal_16_mean_ap_delta_min'],
        ideal_seed_count=sum(d>=gate['ideal_16_seed_ap_delta_min'] for d in ideal)>=gate['ideal_16_seeds_within_min'],
        shot_mean=float(np.mean(shot))>=gate['shot_4096_mean_ap_delta_min'],
        query_fraction=max(s['per_shot_pair_fraction'] for s in seeds)<=gate['pair_fraction_max'])
    return dict(passed=all(checks.values()),checks=checks,ideal_16_paired_ap_deltas=ideal,
        shot_4096_paired_ap_deltas=shot,ideal_16_mean_ap_delta=float(np.mean(ideal)),
        shot_4096_mean_ap_delta=float(np.mean(shot)),
        decision='eligible_for_training_only_confirmation' if all(checks.values()) else 'prune_landmark_promotion')

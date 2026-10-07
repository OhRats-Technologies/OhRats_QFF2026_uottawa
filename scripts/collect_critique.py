"""Replay saved critique diagnostics without fits, timing reruns or acquisition."""
import argparse
import json
from pathlib import Path
import sys
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from wildfire_lab.critique_diagnostics import load_sources, numeric_diagnostics, sha
from wildfire_lab.saved_shot_sweep import sector


def collect(root):
    plan_path = root/'experiments/critique_diagnostics.json'
    plan = json.loads(plan_path.read_text())
    saved = json.loads((root/'docs/results/critique-diagnostics.json').read_text())
    assert saved['plan_sha256'] == sha(plan_path)
    expected = numeric_diagnostics(load_sources(root, plan), plan)
    assert all(saved[key] == value for key, value in expected.items())
    for timing in saved['exact_classical_timing']:
        states, costs = sector(timing['objective'])
        assert len(states) == timing['feasible_states']
        assert int(states[costs.argmin()]) == timing['selected_state']
        np.testing.assert_allclose(costs.min(), timing['exact_cost'])
        times = timing['elapsed_ms']
        assert len(times) == plan['timing_repetitions'] and min(times) > 0
        np.testing.assert_allclose([np.median(times), np.quantile(times, .1), np.quantile(times, .9)],
                                  [timing['median_ms'], timing['p10_ms'], timing['p90_ms']])
    return dict(status='passed', prediction_panels=sum(map(len, saved['prediction_sensitivity'].values())),
        cached_choice_diagnostics=sum(map(len, saved['tuning_weight_sensitivity'].values())),
        measured_repair_diagnostics=len(saved['kernel_repairs']), predictor_fits=0,
        hardware_jobs=0, new_samples=0, timing_reruns=0)


if __name__ == '__main__':
    argparse.ArgumentParser(description=__doc__).parse_args()
    print(json.dumps(collect(ROOT)))

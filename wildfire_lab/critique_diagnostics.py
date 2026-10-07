"""Frozen response to peer critique using existing development evidence only."""
import argparse
import hashlib
import json
from pathlib import Path
import platform
import subprocess
from zipfile import ZipFile
from wildfire_lab.critique_stability import prediction_panels, tuning_sensitivity
from wildfire_lab.critique_geometry import exact_timing, repairs


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_sources(root, plan):
    for name, expected in plan['input_sha256'].items():
        assert sha(root/name) == expected, name
    evidence = {}
    for study in plan['prediction_studies']+['selector-multistart', 'tuned-kernel-hardware', 'shot-sweep-marrakesh']:
        with ZipFile(root/f'docs/data/{study}-evidence.zip') as archive:
            data = json.loads(archive.read('evidence.json'))
            evidence[study] = data.get('analysis', data)
    return evidence


def numeric_diagnostics(evidence, plan):
    prediction, tuning = {}, {}
    for study in plan['prediction_studies']:
        prediction[study] = prediction_panels(evidence[study])
        tuning[study] = tuning_sensitivity(evidence[study])
    alignment = []
    for cohort in evidence['selector-multistart']['cohorts']:
        policies = {}
        for name, model in cohort['models'].items():
            row = next(r for r in model['rows'] if r['model'] == 'qsvr')
            choice = cohort['choices'][name]
            state = sum(1 << i for i in choice)
            cost = cohort['sector_objectives'][cohort['sector_states'].index(state)]
            policies[name] = dict(selected_indices=choice, objective=cost,
                gap=cost-cohort['exact_objective'], mae_ha=row['mae_ha'])
        alignment.append(dict(pool=cohort['selector_qubits'], fold=cohort['fold'], policies=policies))
    return dict(prediction_sensitivity=prediction, tuning_weight_sensitivity=tuning,
                objective_alignment=alignment, kernel_repairs=repairs(evidence['tuned-kernel-hardware']))


def produce(root, output, path):
    plan = json.loads(path.read_text())
    for name in [str(path.relative_to(root)), *plan['code_paths']]:
        assert subprocess.check_output(['git', 'show', 'HEAD:'+name], cwd=root) == (root/name).read_bytes()
    evidence = load_sources(root, plan)
    output.mkdir(parents=True, exist_ok=False)
    (output/'intent.json').write_text(json.dumps(dict(plan_sha256=sha(path)))+'\n')
    result = numeric_diagnostics(evidence, plan)
    objective = {r['specification']['pool_size']: r['objective_specification']
                 for r in evidence['shot-sweep-marrakesh']['rows']}
    result.update(study=plan['study'], plan_sha256=sha(path),
        code_sha256={name: sha(root/name) for name in plan['code_paths']},
        exact_classical_timing=[exact_timing(objective[n], plan['timing_repetitions']) for n in [10, 16, 20]],
        machine=dict(system=platform.system(), processor=platform.machine(), python=platform.python_version()),
        predictor_fits=0, new_quantum_states=0, hardware_jobs=0, final_test_accessed=False,
        limitation=plan['interpretation_policy'])
    (output/'analysis.json').write_text(json.dumps(result, indent=2)+'\n')
    return result


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--plan', type=Path, default=Path('experiments/critique_diagnostics.json'))
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    result = produce(Path(__file__).resolve().parents[1], args.output, args.plan.resolve())
    print(json.dumps(dict(status='complete', timing=[{k:r[k] for k in ['pool', 'feasible_states', 'median_ms']} for r in result['exact_classical_timing']], predictor_fits=0, hardware_jobs=0)))

"""One preview/execute front door for the annual study's bounded stages."""

from pathlib import Path
import subprocess
import sys
import json
import hashlib
from zipfile import ZipFile

OPERATIONS = {
    'classical': 'run_annual_regression.py',
    'quantum': 'run_annual_quantum.py',
    'matched': 'run_annual_matched.py',
    'selectors': 'run_annual_selectors.py',
    'context': 'run_annual_context.py',
    'woodland': 'run_annual_woodland.py',
    'collect': None,
    'mitigation': 'run_pipeline_mitigation.py',
    'mitigation-collect': 'run_pipeline_mitigation.py',
    'forest': 'run_forest_expansion.py',
    'forest-orders': None,
    'selector-scaling': None,
    'forest-collect': 'collect_forest_study.py',
    'forest-orders-collect': 'collect_forest_study.py',
    'selector-scaling-collect': 'collect_forest_study.py',
    'forest-source-collect': 'context/forest_collect.py',
    'selector-hardware-collect': 'collect_selector_hardware.py',
    'selector-search': None,
    'expanded-tuning': None,
    'selector-search-collect': 'collect_search.py',
    'expanded-tuning-collect': 'collect_search.py',
}


def collect_bundle(root, output):
    from wildfire_lab.annual_final_audit import collect

    if output.exists():
        raise FileExistsError(output)
    index = json.loads((root / 'docs/data/annual_final_bundle.json').read_text())
    bundle = root / index['bundle']
    if hashlib.sha256(bundle.read_bytes()).hexdigest() != index['sha256']:
        raise ValueError('Public annual evidence bundle changed')
    with ZipFile(bundle) as archive:
        names = archive.namelist()
        if len(names) != index['members'] or any(Path(n).is_absolute() or '..' in Path(n).parts for n in names):
            raise ValueError('Unexpected annual evidence members')
        output.mkdir(parents=True)
        archive.extractall(output)
    receipt = collect(root, output, root / 'experiments/annual_final.json')
    (output / 'audit.json').write_text(json.dumps(receipt, indent=2) + '\n')
    return dict(prediction_records_checked=receipt['prediction_records_checked'],
                kernel_records_checked=receipt['kernel_records_checked'],
                predictor_fits=0, new_quantum_states=0)


def run(root, operation, output, dataset=None, qubits=4, execute=False):
    output = Path(output)
    if operation in {'selector-search', 'expanded-tuning',
                     'selector-search-collect', 'expanded-tuning-collect'}:
        if operation.endswith('-collect'):
            study = 'selector-multistart' if operation.startswith('selector') else 'expanded-tuning'
            command = [sys.executable, str(root/'scripts/collect_search.py'), study]
        else:
            module = 'selector_multistart' if operation == 'selector-search' else 'expanded_tuning'
            command = [sys.executable, '-m', 'wildfire_lab.'+module]
        command.extend(['--output', str(output)])
        if execute:
            subprocess.run(command, cwd=root, check=True)
        return dict(operation=operation, command=command, executes=execute,
                    information='New training-only search; collection replays saved arithmetic only. No hardware or final-year access.')
    if operation == 'selector-hardware-collect':
        command = [sys.executable,str(root/'scripts/collect_selector_hardware.py'),
                   '--output',str(output)]
        if execute:
            subprocess.run(command,cwd=root,check=True)
        return dict(operation=operation,command=command,executes=execute,
                    information='Published hardware counts and prediction-equation replay only; no hardware, fits, quantum states, draws or credentials.')
    if operation.startswith('forest') or operation.startswith('selector-scaling'):
        command = [sys.executable]
        if operation in {'forest-orders','selector-scaling'}:
            module = 'forest_order_controls' if operation=='forest-orders' else 'selector_scaling'
            command.extend(['-m','wildfire_lab.'+module])
        else:
            command.append(str(root/'scripts'/OPERATIONS[operation]))
            if operation.endswith('-collect') and operation!='forest-source-collect':
                study = {'forest-collect':'forest-expansion',
                         'forest-orders-collect':'forest-order-controls',
                         'selector-scaling-collect':'selector-scaling'}[operation]
                command.append(study)
            elif operation=='forest':
                command.append('run')
        command.extend(['--output',str(output)])
        if execute:
            subprocess.run(command,cwd=root,check=True)
        return dict(operation=operation,command=command,executes=execute,
                    information='Separately frozen training-only development; saved collection has no fits/states/draws/downloads. Source collection needs existing42-layer caches; public study collection needs only committed assets.')
    if operation in {'mitigation', 'mitigation-collect'}:
        command = [sys.executable, str(root / 'scripts/run_pipeline_mitigation.py'),
                   'run' if operation == 'mitigation' else 'collect', '--output', str(output)]
        if dataset is not None and operation == 'mitigation':
            command.extend(['--dataset', str(dataset)])
        if execute:
            subprocess.run(command, cwd=root, check=True)
        return dict(operation=operation, command=command, executes=execute,
                    information='Separate training-only local mitigation; collection never fits or samples; no hardware')
    if operation == 'collect':
        command = [sys.executable, str(root / 'scripts/pipeline.py'), 'annual', 'collect',
                   '--output', str(output), '--execute']
        result = dict(operation=operation, command=command, executes=execute,
                      information='Frozen public evidence collection; reused-year predictions, no fitting or quantum execution')
        if execute:
            result.update(collect_bundle(root, output))
        return result
    command = [sys.executable, str(root / 'scripts' / OPERATIONS[operation]),
               '--output', str(output)]
    if operation != 'classical' or dataset is not None:
        command.extend(['--dataset', str(dataset or root / 'docs/data/annual_training.csv')])
    if operation == 'quantum':
        command.extend(['--qubits', str(qubits)])
    if execute:
        if output.exists():
            raise FileExistsError(output)
        subprocess.run(command, cwd=root, check=True)
    return dict(study='annual-qsvr', operation=operation, command=command,
                executes=execute, output=str(output),
                source_requirement='Classical accepts public CSV or raw NFDB/weather; context needs cached weather; woodland needs rasters/boundary',
                information='Training-only annual development; no test opening or hardware')

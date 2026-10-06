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

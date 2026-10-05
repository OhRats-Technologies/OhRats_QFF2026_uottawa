"""One preview/execute front door for the annual study's bounded stages."""

from pathlib import Path
import subprocess
import sys

OPERATIONS = {
    'classical': 'run_annual_regression.py',
    'quantum': 'run_annual_quantum.py',
    'matched': 'run_annual_matched.py',
    'selectors': 'run_annual_selectors.py',
    'context': 'run_annual_context.py',
    'woodland': 'run_annual_woodland.py',
}


def run(root, operation, output, dataset=None, qubits=4, execute=False):
    output = Path(output)
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
                source_requirement='Raw NFDB/weather required for classical; cached weather for context',
                information='Training-only annual development; no test opening or hardware')

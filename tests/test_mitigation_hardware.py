"""IBM budget, client-side shot expansion and submission-intent safety."""
from pathlib import Path
import json
import tempfile
import unittest
from unittest.mock import Mock,patch
from qiskit import QuantumCircuit,qpy
from qiskit.providers.fake_provider import GenericBackendV2
from qiskit.transpiler import generate_preset_pass_manager
from qiskit_ibm_runtime.executor_sampler.prepare import prepare
from qiskit_ibm_runtime.options_models.sampler import SamplerOptions
from wildfire_lab.mitigation_hardware import submit,sha
ROOT=Path(__file__).resolve().parents[1]

class HardwareTests(unittest.TestCase):
    def test_total_caps_and_shots(self):
        plan=json.loads((ROOT/'experiments/annual_mitigation_ibm.json').read_text())
        self.assertEqual(plan['jobs']*plan['max_execution_time_per_job_seconds'],120)
        self.assertEqual(plan['kernel_shots'],plan['randomizations']*plan['shots_per_randomization'])
        self.assertEqual(plan['kernel_shots'],plan['calibration_shots'])

    def test_cross_device_caps_and_credentials(self):
        plans=[json.loads((ROOT/f'experiments/annual_mitigation_{name}.json').read_text())
               for name in ['marrakesh','quebec']]
        original=json.loads((ROOT/'experiments/annual_mitigation_ibm.json').read_text())
        self.assertLessEqual(25+sum(p['jobs']*p['max_execution_time_per_job_seconds'] for p in plans),120)
        self.assertEqual([p['credential_env'] for p in plans],['IBM_QUANTUM_API_TOKEN','PINQ_API_TOKEN'])
        self.assertEqual(len({p['public_result_path'] for p in plans}),2)
        for p in plans:
            for key in ['parent_evidence_sha256','arms','kernel_shots','selector_shots',
                        'calibration_shots','randomizations','shots_per_randomization',
                        'train_years','validation_years']:
                self.assertEqual(p[key],original[key])

    def test_client_program_expands_shots_without_qpu(self):
        backend=GenericBackendV2(4,coupling_map=[[0,1],[1,0],[1,2],[2,1],[2,3],[3,2]],seed=7)
        qc=QuantumCircuit(4)
        qc.h(0)
        qc.cx(0,1)
        qc.measure_all()
        compiled=generate_preset_pass_manager(backend=backend,optimization_level=1).run(qc)
        for enabled in [False,True]:
            options=SamplerOptions(max_execution_time=60,
                dynamical_decoupling={'enable':enabled,'sequence_type':'XpXm','skip_reset_qubits':True},
                twirling={'enable_gates':enabled,'enable_measure':enabled,
                          'num_randomizations':4 if enabled else 1,
                          'shots_per_randomization':128 if enabled else 512})
            program,executor=prepare([(compiled,None,512)],options,backend=backend)
            self.assertEqual(program.shots,128 if enabled else 512)
            self.assertEqual(executor.max_execution_time,60)
            if enabled:
                self.assertEqual(program.items[0].shape,(4,))

    def fixture(self,temp):
        plan=json.loads((ROOT/'experiments/annual_mitigation_ibm.json').read_text())
        qc=QuantumCircuit(4);qc.measure_all()
        with (temp/'circuits.qpy').open('wb') as stream:
            qpy.dump([qc],stream)
        receipt=dict(plan=plan,plan_sha256=sha(ROOT/'experiments/annual_mitigation_ibm.json'),
                     circuits_sha256=sha(temp/'circuits.qpy'),shots_per_pub=[512],
                     code_sha256={'wildfire_lab/mitigation_hardware.py':sha(ROOT/'wildfire_lab/mitigation_hardware.py')})
        (temp/'prepared.json').write_text(json.dumps(receipt))

    def test_ambiguous_submission_is_not_retried(self):
        with tempfile.TemporaryDirectory() as path:
            temp=Path(path);self.fixture(temp)
            with patch('wildfire_lab.mitigation_hardware.service') as connection, \
                 patch('wildfire_lab.mitigation_hardware.Sampler') as sampler:
                sampler.return_value.run.side_effect=TimeoutError()
                with self.assertRaises(TimeoutError):
                    submit(ROOT,temp)
                self.assertTrue((temp/'raw_intent.json').exists())
                with self.assertRaises(FileExistsError):
                    submit(ROOT,temp)
                self.assertEqual(sampler.return_value.run.call_count,1)

if __name__=='__main__':
    unittest.main()

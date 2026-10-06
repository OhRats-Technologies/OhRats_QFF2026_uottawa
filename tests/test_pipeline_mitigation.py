"""Mechanism and safety checks for bounded research-pipeline mitigation."""
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import numpy as np
from qiskit import QuantumCircuit, transpile
from qiskit.quantum_info import Operator, Statevector
from wildfire_lab.annual_workflow import run
from wildfire_lab.mitigation_noise import (
    suppressed_circuit, assignment, invert_readout, repair_kernel, sample)
from wildfire_lab.mitigation_run import run as execute

ZERO = dict(cx_target_z_radians=0., spectator_idle_z_radians=0.,
            amplitude_damping=0., phase_damping=0., readout_0_to_1=0., readout_1_to_0=0.)

class MitigationTests(unittest.TestCase):
    def base(self):
        qc = QuantumCircuit(4)
        qc.h(range(4))
        qc.ry(.4, 0)
        qc.cx(0, 1)
        qc.rz(.2, 1)
        qc.cx(1, 2)
        return transpile(qc,basis_gates=['rz','sx','x','cx'],optimization_level=0)

    def test_gate_twirl_preserves_ideal_operator(self):
        base = self.base()
        for seed in range(12):
            self.assertTrue(Operator(base).equiv(Operator(suppressed_circuit(base,ZERO,True,seed))))

    def test_dd_refocuses_declared_idle_drift(self):
        base = self.base()
        noise = dict(ZERO, spectator_idle_z_radians=.31)
        self.assertTrue(Operator(base).equiv(Operator(suppressed_circuit(base,noise,True))))
        self.assertFalse(Operator(base).equiv(Operator(suppressed_circuit(base,noise))))

    def test_tensor_assignment_and_inverse_little_endian(self):
        for n in [4,10]:
            rng = np.random.default_rng(17)
            channels = np.repeat(np.array([[[.92,.03],[.08,.97]]]),n,axis=0)
            p = rng.dirichlet(np.ones(2**n))
            frames = (0,2**n-1)
            observed = assignment(p,channels,frames)
            corrected, diagnostic = invert_readout(observed,channels,frames)
            np.testing.assert_allclose(corrected,p,atol=1e-9)
            self.assertLess(diagnostic['residual'],1e-9)

    def test_asymmetric_readout_calibration_and_frame_decode(self):
        qc = QuantumCircuit(4)
        qc.x(0)
        counts, logical = sample([qc],256,7)
        self.assertEqual(counts[0,1],256)
        self.assertAlmostEqual(logical[0,1],1.)
        counts, logical = sample([qc],256,7,frames=[15])
        self.assertEqual(counts[0,1],256)
        self.assertAlmostEqual(logical[0,1],1.)

    def test_repair_projects_cross_using_training_modes(self):
        gram = np.diag([-1.,.1,2.,3.])
        cross = np.array([[7.,8.,9.,10.]])
        repaired, projected = repair_kernel(gram,cross,rank=2)
        np.testing.assert_array_equal(repaired,np.diag([0.,0.,2.,3.]))
        np.testing.assert_array_equal(projected,[[0.,0.,9.,10.]])

    def test_preview_calls_no_runner(self):
        with patch('wildfire_lab.annual_workflow.subprocess.run') as launch:
            result = run(Path('/repo'),'mitigation',Path('/new'))
            collected = run(Path('/repo'),'mitigation-collect',Path('/existing'))
        launch.assert_not_called()
        self.assertIn('run',result['command'])
        self.assertIn('collect',collected['command'])

    def test_exclusive_output_fails_before_sampling(self):
        root = Path(__file__).resolve().parents[1]
        with tempfile.TemporaryDirectory() as temp, patch('wildfire_lab.mitigation_run.calibrate') as sampler:
            with self.assertRaises(FileExistsError):
                execute(root,root/'docs/data/annual_training.csv',Path(temp),
                        root/'experiments/pipeline_mitigation.json')
        sampler.assert_not_called()

if __name__=='__main__':
    unittest.main()


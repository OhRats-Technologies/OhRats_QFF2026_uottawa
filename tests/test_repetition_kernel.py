"""Mechanism checks independent of measured IBM hardware outcomes."""
import unittest
import numpy as np
from qiskit_aer import AerSimulator
from wildfire_lab.repetition_kernel import circuit


class RepetitionKernelTest(unittest.TestCase):
    def test_decoded_full_register_overlap(self):
        simulator = AerSimulator()
        for fault in ["none", "X0", "X1", "X2", "Z0"]:
            qc = circuit(0., "corrected", fault)
            result = simulator.run(qc, shots=32, seed_simulator=3).result().get_counts()
            expected = "001" if fault == "Z0" else "000"
            self.assertTrue(all(key.split()[-1] == expected for key in result))

    def test_corrects_every_single_x_but_not_phase_flip(self):
        simulator = AerSimulator(method="density_matrix")
        for delta in [0., np.pi/2]:
            for fault in ["none", "X0", "X1", "X2", "Z0"]:
                qc = circuit(delta, "corrected", fault)
                qc.remove_final_measurements(inplace=True)
                qc.save_density_matrix([0], label="decoded")
                rho = simulator.run(qc, shots=1024, seed_simulator=12).result().data(0)["decoded"]
                expected = np.cos(delta/2)**2 if fault != "Z0" else np.sin(delta/2)**2
                self.assertAlmostEqual(float(np.real(np.asarray(rho)[0, 0])), expected, places=10)

    def test_unencoded_and_encoded_no_fault_match(self):
        simulator = AerSimulator(method="density_matrix")
        for arm in ["physical", "encoded"]:
            qc = circuit(np.pi/4, arm)
            qc.remove_final_measurements(inplace=True)
            qc.save_density_matrix([0], label="decoded")
            rho = simulator.run(qc).result().data(0)["decoded"]
            self.assertAlmostEqual(float(np.real(np.asarray(rho)[0, 0])), np.cos(np.pi/8)**2)

"""Independent physical and numerical checks for the small track experiments."""

import unittest
import numpy as np
from qiskit import QuantumCircuit
from qiskit.quantum_info import Statevector
from tracklab import scheduling as grid
from tracklab.chemistry import molecule, measurement_circuits, energy_from_counts
from tracklab.budgetbond import allocate
from flybrain.noise import readout_distribution


class TrackChecks(unittest.TestCase):
    def test_readout_channel_known_state(self):
        # Independent two-bit channel for |00>, with 10% bit flips.
        np.testing.assert_allclose(
            readout_distribution(np.array([1.0, 0, 0, 0]), 0.1),
            [0.81, 0.09, 0.09, 0.01],
        )
        np.testing.assert_allclose(
            readout_distribution(np.ones(4) / 4, 0.2), np.ones(4) / 4
        )

    def test_schedule_hamiltonian_all_bitstrings(self):
        constant, z, zz = grid.ising_coefficients(True)
        for bits in range(16):
            signs = np.array([1 - 2 * ((bits >> i) & 1) for i in range(4)])
            energy = (
                constant
                + z @ signs
                + sum(c * signs[i] * signs[j] for (i, j), c in zz.items())
            )
            self.assertAlmostEqual(energy, grid.objective(bits), places=10)
            if bits.bit_count() == 2:
                self.assertAlmostEqual(
                    energy, grid.schedule(bits)["carbon_proxy"], places=10
                )
        self.assertEqual(sum(grid.schedule(b)["feasible"] for b in range(16)), 6)
        self.assertAlmostEqual(grid.schedule(9)["carbon_proxy"], 0.73)

    def test_xy_conservation_untrained_angles(self):
        rng = np.random.default_rng(99)
        forbidden = [i for i in range(16) if i.bit_count() != 2]
        for depth in [1, 2, 3]:
            for _ in range(4):
                p = Statevector.from_instruction(
                    grid.circuit(rng.normal(size=2 * depth), "xy")
                ).probabilities()
                self.assertLess(p[forbidden].sum(), 1e-12)

    def test_bell_mapping_singlet(self):
        qc = QuantumCircuit(2)
        qc.x(1)
        qc.h(0)
        qc.cx(0, 1)
        qc.z(0)
        z, bell = measurement_circuits(qc)
        pz = Statevector.from_instruction(
            z.remove_final_measurements(inplace=False)
        ).probabilities()
        pb = Statevector.from_instruction(
            bell.remove_final_measurements(inplace=False)
        ).probabilities()
        np.testing.assert_allclose(pz, [0, 0.5, 0.5, 0], atol=1e-12)
        np.testing.assert_allclose(pb, [0, 0, 0, 1], atol=1e-12)
        model = {
            "coefficients": {"XX": 1.0, "YY": 1.0, "ZZ": 1.0},
            "nuclear_energy": 0.0,
            "parity": 1,
        }
        estimate = energy_from_counts(model, {"01": 500, "10": 500}, {"11": 1000}, True)
        self.assertAlmostEqual(estimate["energy"], -3.0)

    def test_h2_independent_fci_and_measurement(self):
        model = molecule(0.735)
        self.assertAlmostEqual(model["exact_total"], model["fci_total"], places=7)
        self.assertAlmostEqual(model["exact_total"], -1.1373060358, places=6)
        counts = []
        for qc in measurement_circuits(model["circuit"]):
            p = Statevector.from_instruction(
                qc.remove_final_measurements(inplace=False)
            ).probabilities()
            counts.append(
                {
                    format(i, "02b"): int(round(value * 10_000_000))
                    for i, value in enumerate(p)
                    if value > 1e-10
                }
            )
        self.assertAlmostEqual(
            energy_from_counts(model, *counts, True)["energy"],
            model["exact_total"],
            places=6,
        )

    def test_allocation_charges_pilot_and_bounds(self):
        model = {"coefficients": {"IZ": 1.0, "XX": 0.1}, "parity": 1}
        counts = [{"01": 64, "10": 64}, {"10": 64, "11": 64}]
        shots = allocate(counts, model, 1792)
        self.assertEqual(sum(shots) + 256, 2048)
        self.assertGreater(shots[0], shots[1])
        self.assertGreaterEqual(min(shots), 128)
        with self.assertRaises(ValueError):
            allocate(counts, model, 100)

    def test_spin_ring_known_limits_and_separable_bound(self):
        from tracklab.spinweave import (
            hamiltonian,
            preparation,
            measurement_circuits,
            measured_energy,
        )

        h0, _ = hamiltonian(0.0)
        h1, j = hamiltonian(1.0)
        self.assertAlmostEqual(np.linalg.eigvalsh(h0.to_matrix()).min(), -2.0)
        self.assertAlmostEqual(np.linalg.eigvalsh(h1.to_matrix()).min(), -3.0)
        qc = preparation(np.zeros(8))
        state = Statevector.from_instruction(qc)
        self.assertAlmostEqual(state.expectation_value(h1).real, -3.0)
        neel = QuantumCircuit(4)
        neel.x(0)
        neel.x(2)
        self.assertAlmostEqual(
            Statevector.from_instruction(neel).expectation_value(h0).real, -1.0
        )
        counts = []
        for m in measurement_circuits(qc):
            p = Statevector.from_instruction(
                m.remove_final_measurements(inplace=False)
            ).probabilities()
            counts.append(
                {
                    format(i, "04b"): int(round(v * 10000))
                    for i, v in enumerate(p)
                    if v > 1e-10
                }
            )
        self.assertAlmostEqual(measured_energy(j, counts)["energy"], -3.0)

    def test_projected_quantum_features_known_zero_state(self):
        from tracklab.kernelforge import feature_map, bloch_features, sampled_bloch

        features = bloch_features([feature_map(np.zeros(3), "product", 1)])
        np.testing.assert_allclose(features, [[0, 0, 1, 0, 0, 1, 0, 0, 1]], atol=1e-12)
        sampled = sampled_bloch(features, 128, np.random.default_rng(3))
        np.testing.assert_allclose(sampled[0, [2, 5, 8]], [1, 1, 1])

    def test_two_group_eigenstate_variance_identity(self):
        rng = np.random.default_rng(11)
        for size in [2, 4, 8]:
            a = rng.normal(size=(size, size)) + 1j * rng.normal(size=(size, size))
            a = (a + a.conj().T) / 2
            b = rng.normal(size=(size, size)) + 1j * rng.normal(size=(size, size))
            b = (b + b.conj().T) / 2
            _, vectors = np.linalg.eigh(a + b)
            for psi in vectors.T:

                def variance(operator):
                    mean = np.vdot(psi, operator @ psi).real
                    return np.vdot(psi, operator @ operator @ psi).real - mean**2

                self.assertAlmostEqual(variance(a), variance(b), places=10)

    def test_regularized_pilot_handles_unseen_outcomes(self):
        from tracklab.budgetbond import regularized_allocate

        model = {"coefficients": {"IZ": 1.0, "XX": 1.0}, "parity": 1}
        shots = regularized_allocate([{"01": 64}, {"10": 64}], model, 8064)
        self.assertEqual(shots, [4032, 4032])

    def test_phase_pair_same_probabilities_different_state(self):
        a = Statevector.from_instruction(grid.circuit([], preparation="pair"))
        b = Statevector.from_instruction(grid.circuit([], preparation="phase_pair"))
        np.testing.assert_allclose(a.probabilities(), b.probabilities(), atol=1e-12)
        supported = np.flatnonzero(b.probabilities() > 1e-10)
        normalized = b.data[supported] / b.data[supported[0]]
        np.testing.assert_allclose(normalized, np.ones(4), atol=1e-12)
        self.assertFalse(a.equiv(b))

    def test_gibbs_state_and_dimer_entanglement_limits(self):
        from tracklab.spinweave import hamiltonian
        from tracklab.spintherm import gibbs, negativity

        matrix = hamiltonian(1.0)[0].to_matrix()
        rho = gibbs(matrix, 0.0)
        self.assertAlmostEqual(negativity(rho, [0]), 0.5)
        self.assertAlmostEqual(negativity(rho, [0, 1]), 0.0)
        np.testing.assert_allclose(gibbs(matrix, 1e8), np.eye(16) / 16, atol=1e-8)
        critical = gibbs(matrix, 2 / np.log(3))
        self.assertAlmostEqual(np.trace(critical @ matrix).real, -1.0)
        self.assertLess(negativity(critical, [0]), 1e-10)

    def test_fixed_angle_phase_sweep_equivalence(self):
        from tracklab.phasesweep import phase_circuit

        params = [0.4, 0.2]
        self.assertTrue(
            Statevector.from_instruction(phase_circuit(params, 0)).equiv(
                Statevector.from_instruction(grid.circuit(params, preparation="pair"))
            )
        )
        self.assertTrue(
            Statevector.from_instruction(phase_circuit(params, np.pi / 2)).equiv(
                Statevector.from_instruction(
                    grid.circuit(params, preparation="phase_pair")
                )
            )
        )

    def test_qwc_measurements_complex_state_and_covariance(self):
        from tracklab.activebudget import groups, probabilities, allocation
        from qiskit.quantum_info import SparsePauliOp

        terms = [
            ("II", 0.2),
            ("IY", 0.3),
            ("YY", -0.7),
            ("ZI", 0.4),
            ("ZX", 0.1),
            ("XX", 0.6),
        ]
        state = Statevector(np.array([1, 2j, 3 + 1j, -2j]) / np.sqrt(19))
        grouped = groups(terms)
        reconstructed = 0.2 + sum(
            probabilities(state, g["basis"]) @ g["values"] for g in grouped
        )
        self.assertAlmostEqual(
            reconstructed, state.expectation_value(SparsePauliOp.from_list(terms)).real
        )
        for g in grouped:
            operator = SparsePauliOp.from_list(g["terms"]).to_matrix()
            p = probabilities(state, g["basis"])
            v = g["values"]
            variance = (
                state.expectation_value(operator @ operator).real
                - state.expectation_value(operator).real ** 2
            )
            self.assertAlmostEqual(p @ (v * v) - (p @ v) ** 2, variance)
        n = allocation([1.0, 2.0, 0.0, 0.5], 1792)
        self.assertEqual(sum(n) + 256, 2048)
        self.assertGreaterEqual(min(n), 128)
        with self.assertRaises(ValueError):
            allocation([1, 1, 1, 1], 500)

    def test_lih_active_space_independent_reference(self):
        from tracklab.activebudget import model

        energy, _, grouped, _ = model()
        self.assertAlmostEqual(energy, -7.8621288334, places=6)
        self.assertEqual(len(grouped), 4)

    def test_fixed_decision_confidence_and_readout_operator_bound(self):
        from tracklab.spinshield import hoeffding_margin, readout_bias_bound
        from tracklab.spinweave import hamiltonian
        from qiskit.quantum_info import SparsePauliOp

        self.assertAlmostEqual(
            hoeffding_margin([1024] * 3, [2] * 3), np.sqrt(6 * np.log(20) / 1024)
        )
        self.assertAlmostEqual(
            hoeffding_margin([4096] * 3, [2] * 3),
            hoeffding_margin([1024] * 3, [2] * 3) / 2,
        )
        self.assertAlmostEqual(readout_bias_bound([1, 1, 1, 1], 0.02), 0.2352)
        rng = np.random.default_rng(84)
        for delta in [0.0, 0.5, 1.0]:
            operator, couplings = hamiltonian(delta)
            for _ in range(10):
                flips = rng.uniform(0, 0.05, (3, 4))
                modified = []
                for label, c in operator.to_list():
                    axis = next(a for a in label if a != "I")
                    a = "XYZ".index(axis)
                    scale = np.prod(
                        [
                            1 - 2 * flips[a, q]
                            for q, p in enumerate(label[::-1])
                            if p != "I"
                        ]
                    )
                    modified.append((label, c * scale))
                difference = (
                    operator.to_matrix() - SparsePauliOp.from_list(modified).to_matrix()
                )
                norm = max(abs(np.linalg.eigvalsh(difference)))
                self.assertLessEqual(norm, readout_bias_bound(couplings, 0.05) + 1e-12)
        for n in [0, -1, 1.5, np.nan]:
            with self.assertRaises(ValueError):
                hoeffding_margin([n], [2])
        with self.assertRaises(ValueError):
            readout_bias_bound([np.nan], 0.02)

    def test_shot_planner_power_margin_and_impossible_witness(self):
        from tracklab.spinshield import planned_shots, hoeffding_margin

        n = planned_shots(-2.0, 0.0)
        self.assertLess(2 * hoeffding_margin([n] * 3, [2] * 3), 1.0)
        self.assertGreaterEqual(2 * hoeffding_margin([n - 1] * 3, [2] * 3), 1.0)
        self.assertGreater(planned_shots(-2.0, 0.2), n)
        self.assertGreater(planned_shots(-2.0, 0.0, alpha=0.01), n)
        self.assertIsNone(planned_shots(-1.0, 0.0))
        self.assertIsNone(planned_shots(-1.1, 0.2))
        with self.assertRaises(ValueError):
            planned_shots(-2.0, np.nan)

    def test_finite_count_convolution_against_brute_enumeration(self):
        from tracklab.spinaudit import distribution
        from itertools import product

        probabilities = [
            np.array([0.2, 0.3, 0.5]),
            np.array([0.1, 0.7, 0.2]),
            np.array([0.4, 0.5, 0.1]),
        ]
        energies, p = distribution(probabilities, np.array([-1.0, 0.0, 1.0]), 2)
        brute = np.zeros(13)
        for outcomes in product(range(3), repeat=6):
            probability = np.prod(
                [probabilities[k // 2][i] for k, i in enumerate(outcomes)]
            )
            brute[sum(outcomes)] += probability
        np.testing.assert_allclose(p, brute, atol=1e-12)
        np.testing.assert_allclose(energies, (np.arange(13) - 6) / 2)
        with self.assertRaises(ValueError):
            distribution(probabilities, np.array([-0.5, 0, 1]), 2)

    def test_hardware_count_export_removes_private_service_fields(self):
        from tracklab.export import public_hardware_counts
        import json

        record = {
            "evidence": "real_ibm_hardware",
            "backend": "ibm_quebec",
            "collected_utc": "2026-10-03T09:00:00Z",
            "job_id": "PRIVATE_JOB",
            "token": "PRIVATE_SECRET",
            "instance": "PRIVATE_INSTANCE",
            "cases": [
                {
                    "name": "control",
                    "expected": [0.5, 0.5, 0, 0],
                    "counts": {"00": 5, "01": 5},
                    "actual_shots": 10,
                    "token": "PRIVATE_CASE",
                    "model": {"token": "PRIVATE_MODEL"},
                }
            ],
        }
        public = public_hardware_counts(record)
        self.assertEqual(public["cases"][0]["counts"], {"00": 5, "01": 5})
        self.assertNotIn("PRIVATE_", json.dumps(public))
        record["cases"][0]["counts"] = {"000": 10}
        with self.assertRaises(ValueError):
            public_hardware_counts(record)

    def test_fly_control_metrics_retain_count_origin(self):
        from tracklab.evidence import analyze

        case = {
            "name": "zero_time_control",
            "expected": [1.0, 0, 0, 0, 0, 0, 0, 0],
            "observed": [0.9, 0.1, 0, 0, 0, 0, 0, 0],
            "actual_shots": 100,
        }
        result = analyze([case], "LOCAL_CALIBRATION_FORECAST")[0]
        self.assertEqual(result["origin"], "LOCAL_CALIBRATION_FORECAST")
        self.assertAlmostEqual(result["total_variation_from_ideal"], 0.1)
        self.assertAlmostEqual(result["source_return_probability"], 0.9)

    def test_shot_matched_forecast_analytic_one_shot_limit(self):
        from tracklab.forecastaudit import compare

        actual = {
            "case": "one_shot",
            "expected": [0.5, 0.5],
            "observed": [1.0, 0.0],
            "actual_shots": 1,
        }
        forecast = {"observed": [0.5, 0.5], "actual_shots": 8192}
        row, draws = compare(actual, forecast, repeats=100)
        np.testing.assert_allclose(draws, 0.5)
        self.assertEqual(row["conditional_predictive_95"], [0.5, 0.5])
        self.assertEqual(row["forecast_probability_tv_from_ideal"], 0)
        self.assertEqual(row["hardware_tv_from_ideal"], 0.5)


if __name__ == "__main__":
    unittest.main()

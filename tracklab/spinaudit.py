"""Independent finite-count convolution audit of the SpinShield sampling decisions."""

import csv, json
import numpy as np
from scipy.signal import fftconvolve
from qiskit import QuantumCircuit
from qiskit.quantum_info import DensityMatrix
from flybrain.data import REPO
from flybrain.noise import readout_distribution
from flybrain.progress import timed_stage
from .spinweave import hamiltonian, measurement_circuits
from .spintherm import gibbs
from .spinshield import values, hoeffding_margin


def convolve(a, b):
    result = np.convolve(a, b) if len(a) + len(b) < 64 else fftconvolve(a, b)
    if np.min(result) < -1e-10:
        raise ValueError("Convolution has excessive negative roundoff")
    result = np.maximum(result, 0)
    result /= result.sum()
    return result


def power(p, n):
    if not isinstance(n, int) or n < 0:
        raise ValueError("Nonnegative integer exponent required")
    result = np.array([1.0])
    base = np.asarray(p, dtype=float)
    while n:
        if n & 1:
            result = convolve(result, base)
        n //= 2
        if n:
            base = convolve(base, base)
    return result


def distribution(probabilities, basis_values, n):
    """Three bases, integer outcomes {-1,0,1}; energy=(index-3*n)/n."""
    if n <= 0 or len(probabilities) != 3:
        raise ValueError("Positive shots and three bases required")
    if not all(any(abs(v - x) < 1e-12 for x in [-1, 0, 1]) for v in basis_values):
        raise ValueError("This audit supports only integer basis outcomes")
    result = np.array([1.0])
    expected = 0.0
    variance = 0.0
    for p in probabilities:
        p = np.asarray(p, dtype=float)
        if np.min(p) < -1e-12 or not np.isclose(p.sum(), 1):
            raise ValueError("Invalid probability vector")
        p = np.maximum(p, 0)
        p /= p.sum()
        one = np.array(
            [p[np.isclose(basis_values, x, atol=1e-12)].sum() for x in [-1, 0, 1]]
        )
        result = convolve(result, power(one, n))
        mean = p @ basis_values
        expected += mean
        variance += (p @ (basis_values**2) - mean**2) / n
    energies = (np.arange(len(result)) - 3 * n) / n
    mean = float(energies @ result)
    var = float(((energies - mean) ** 2) @ result)
    if not np.isclose(mean, expected, atol=1e-8) or not np.isclose(
        var, variance, atol=1e-8
    ):
        raise ValueError("Convolution moments fail independent one-shot reference")
    return energies, result


def main():
    shield = json.loads((REPO / "results/spinshield/metrics.json").read_text())
    rows = []
    with timed_stage("spinshield", "finite_count_convolution_audit") as evidence:
        rotations = [
            c.remove_final_measurements(inplace=False)
            for c in measurement_circuits(QuantumCircuit(4))
        ]
        for case in shield["cases"]:
            operator, j = hamiltonian(case["delta"])
            if case["temperature"] is not None:
                rho = gibbs(operator.to_matrix(), case["temperature"])
            elif case["name"] == "Neel product":
                rho = np.diag([float(i == 5) for i in range(16)])
            elif case["name"] == "Maximally mixed":
                rho = np.eye(16) / 16
            else:
                raise ValueError("Unknown reference state")
            ideal = [DensityMatrix(rho).evolve(c).probabilities() for c in rotations]
            v = values(j)
            for plan in [r for r in shield["plans"] if r["case"] == case["name"]]:
                ps = [readout_distribution(p, plan["readout"]) for p in ideal]
                budgets = {64, 256, 1024}
                if plan["shots_per_basis_sufficient"] is not None:
                    budgets.add(plan["shots_per_basis_sufficient"])
                for n in sorted(budgets):
                    energies, p = distribution(ps, v, int(n))
                    margin = hoeffding_margin([n] * 3, [2] * 3, shield["alpha"])
                    threshold = -1 - margin - plan["bias_allowance"]
                    detected = float(p[energies < threshold].sum())
                    covered = float(
                        p[
                            energies + margin + plan["bias_allowance"]
                            >= case["exact_energy"]
                        ].sum()
                    )
                    if covered < 1 - shield["alpha"] - 1e-8:
                        raise ValueError("Audit contradicts fixed-decision coverage")
                    is_plan = n == plan["shots_per_basis_sufficient"]
                    if is_plan and detected < plan["target_power"] - 1e-8:
                        raise ValueError("Shot plan fails sufficient power bound")
                    monte = next(
                        (
                            r["hoeffding_with_bias"]
                            for r in shield["summaries"]
                            if r["case"] == case["name"]
                            and r["readout"] == plan["readout"]
                            and r["shots_per_basis"] == n
                        ),
                        None,
                    )
                    rows.append(
                        {
                            "case": case["name"],
                            "readout": plan["readout"],
                            "shots_per_basis": n,
                            "numerical_detection_probability": detected,
                            "numerical_energy_coverage": covered,
                            "monte_carlo_detection_fraction": monte,
                            "is_sufficient_shot_plan": is_plan,
                        }
                    )
        evidence.update(
            audits=len(rows),
            independent_moment_checks=True,
            coverage_bounds_passed=True,
            power_bounds_passed=True,
        )
    report = {
        "origin": "CLASSICAL_NUMERICAL_FINITE_COUNT_CONVOLUTION",
        "rows": rows,
        "method": "Collapse each basis to outcomes -1,0,1, raise its probability polynomial to n, and convolve three independent bases. Small products use direct convolution; large products use FFT. Recomputed mean and variance are checked against independent one-shot moments.",
        "limitations": "Numerical convolution is exact for the stated finite-count model up to floating-point roundoff, not a symbolic proof or hardware distribution. Only delta=0 or 1 integer-outcome cases are supported. Tiny tails may be below numerical resolution. Independent fixed counts and the declared symmetric-readout assumptions remain essential.",
    }
    out = REPO / "results/spinaudit"
    out.mkdir(parents=True, exist_ok=True)
    (out / "metrics.json").write_text(json.dumps(report, indent=2) + "\n")
    with (out / "audit.csv").open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=rows[0])
        w.writeheader()
        w.writerows(rows)
    print(
        json.dumps(
            {
                "audits": len(rows),
                "minimum_numerical_coverage": min(
                    r["numerical_energy_coverage"] for r in rows
                ),
                "minimum_planned_detection_probability": min(
                    r["numerical_detection_probability"]
                    for r in rows
                    if r["is_sufficient_shot_plan"]
                ),
            }
        )
    )


if __name__ == "__main__":
    main()

"""BondBench: H2 bond energies and symmetry-filtered noisy measurement."""

import argparse
import csv
import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from pyscf import gto, scf, fci
from qiskit import transpile
from qiskit.quantum_info import Statevector
from qiskit_aer import AerSimulator
from qiskit_nature.second_q.circuit.library import HartreeFock
from qiskit_nature.second_q.drivers import PySCFDriver
from qiskit_nature.second_q.mappers import ParityMapper
from qiskit_nature.units import DistanceUnit
from scipy.optimize import minimize_scalar

from flybrain.data import REPO
from flybrain.noise import noise_model
from flybrain.progress import timed_stage

DISTANCES = [0.4, 0.55, 0.735, 0.9, 1.1, 1.4, 1.8, 2.2]


def molecule(distance):
    if not np.isfinite(distance) or not 0.2 <= distance <= 4:
        raise ValueError("H2 distance must be 0.2–4 angstrom")
    atom = f"H 0 0 0; H 0 0 {distance}"
    problem = PySCFDriver(atom=atom, basis="sto3g", unit=DistanceUnit.ANGSTROM).run()
    mapper = ParityMapper(num_particles=problem.num_particles)
    operator = mapper.map(problem.hamiltonian.second_q_op())
    coefficients = {
        label: float(coefficient.real) for label, coefficient in operator.to_list()
    }
    if not set(coefficients) <= {"II", "IZ", "ZI", "ZZ", "XX", "YY"}:
        raise ValueError("Unsupported terms in two-qubit H2 Hamiltonian")
    hf = HartreeFock(problem.num_spatial_orbitals, problem.num_particles, mapper)
    probabilities = Statevector.from_instruction(hf).probabilities()
    hf_index = int(np.argmax(probabilities))
    sector = [hf_index, hf_index ^ 3]
    matrix = operator.to_matrix()
    exact_electronic = float(np.linalg.eigvalsh(matrix[np.ix_(sector, sector)]).min())

    def ansatz(theta):
        circuit = hf.copy()
        circuit.cx(0, 1)
        circuit.ry(float(theta), 0)
        circuit.cx(0, 1)
        return circuit

    def energy(theta):
        state = Statevector.from_instruction(ansatz(theta))
        return float(state.expectation_value(operator).real)

    optimized = minimize_scalar(
        energy, method="bounded", bounds=(-np.pi, np.pi), options={"xatol": 1e-12}
    )
    if not optimized.success or abs(optimized.fun - exact_electronic) > 1e-7:
        raise ValueError(
            "Variational ansatz did not reproduce the exact symmetry-sector energy"
        )
    # Independent direct PySCF FCI route, not another diagonalization of the qubit operator.
    mol = gto.M(atom=atom, basis="sto3g", unit="Angstrom", verbose=0)
    mean_field = scf.RHF(mol).run()
    fci_total = float(fci.FCI(mean_field).kernel()[0])
    exact_total = exact_electronic + problem.nuclear_repulsion_energy
    if abs(exact_total - fci_total) > 1e-7:
        raise ValueError("Mapped energy disagrees with independent PySCF FCI")
    return {
        "distance": distance,
        "coefficients": coefficients,
        "nuclear_energy": float(problem.nuclear_repulsion_energy),
        "hartree_fock_total": float(problem.reference_energy),
        "fci_total": fci_total,
        "exact_total": exact_total,
        "vqe_total": float(optimized.fun + problem.nuclear_repulsion_energy),
        "theta": float(optimized.x),
        "evaluations": int(optimized.nfev),
        "parity": hf_index.bit_count() % 2,
        "circuit": ansatz(optimized.x),
    }


def measurement_circuits(preparation):
    z = preparation.copy()
    z.measure_all()
    bell = preparation.copy()
    bell.cx(0, 1)
    bell.h(0)
    bell.measure_all()
    return z, bell


def mean_and_se(counts, value, accept=lambda bits: True):
    total = sum(count for bits, count in counts.items() if accept(int(bits, 2)))
    if total < 2:
        raise ValueError("Too few accepted shots for uncertainty estimate")
    mean = (
        sum(
            value(int(bits, 2)) * count
            for bits, count in counts.items()
            if accept(int(bits, 2))
        )
        / total
    )
    variance = sum(
        (value(int(bits, 2)) - mean) ** 2 * count
        for bits, count in counts.items()
        if accept(int(bits, 2))
    ) / (total - 1)
    return mean, np.sqrt(variance / total), total


def energy_from_counts(model, z_counts, bell_counts, postselect=False):
    c, parity = model["coefficients"], model["parity"]

    def z_value(bits):
        z0, z1 = 1 - 2 * (bits & 1), 1 - 2 * ((bits >> 1) & 1)
        return c.get("IZ", 0) * z0 + c.get("ZI", 0) * z1 + c.get("ZZ", 0) * z0 * z1

    def bell_value(bits):
        xx, zz = 1 - 2 * (bits & 1), 1 - 2 * ((bits >> 1) & 1)
        return c.get("XX", 0) * xx - c.get("YY", 0) * xx * zz

    accept_z = lambda bits: not postselect or bits.bit_count() % 2 == parity
    accept_bell = lambda bits: not postselect or ((bits >> 1) & 1) == parity
    mz, sez, nz = mean_and_se(z_counts, z_value, accept_z)
    mb, seb, nb = mean_and_se(bell_counts, bell_value, accept_bell)
    return {
        "energy": c.get("II", 0) + mz + mb + model["nuclear_energy"],
        "standard_error": float(np.hypot(sez, seb)),
        "accepted_z": nz,
        "accepted_bell": nb,
        "acceptance_fraction": (nz + nb)
        / (sum(z_counts.values()) + sum(bell_counts.values())),
    }


def run(args):
    models, curve, rows = [], [], []
    with timed_stage("bondbench", "physical_curve_and_fci_reference") as evidence:
        for distance in DISTANCES:
            model = molecule(distance)
            models.append(model)
            curve.append(
                {key: value for key, value in model.items() if key != "circuit"}
            )
        evidence.update(
            molecules=len(models),
            independent_fci=True,
            max_vqe_fci_error=max(abs(m["vqe_total"] - m["fci_total"]) for m in models),
        )
    with timed_stage("bondbench", "noise_and_symmetry_filtering") as evidence:
        for model in [models[2], models[5], models[7]]:
            circuits = transpile(
                list(measurement_circuits(model["circuit"])),
                basis_gates=["rz", "sx", "x", "cx"],
                optimization_level=1,
                seed_transpiler=args.seed,
            )
            for noise_name, gate, readout in [
                ("ideal_sampling", 0.0, 0.0),
                ("noisy", 0.01, 0.02),
            ]:
                simulator = AerSimulator(
                    method="density_matrix",
                    noise_model=noise_model(gate, readout),
                    max_parallel_threads=2,
                )
                for repeat in range(args.repeats):
                    counts = (
                        simulator.run(
                            circuits,
                            shots=args.shots,
                            seed_simulator=args.seed + repeat,
                        )
                        .result()
                        .get_counts()
                    )
                    raw = energy_from_counts(model, counts[0], counts[1])
                    filtered = energy_from_counts(
                        model, counts[0], counts[1], postselect=True
                    )
                    rows.append(
                        {
                            "distance": model["distance"],
                            "noise": noise_name,
                            "repeat": repeat,
                            "seed": args.seed + repeat,
                            "shots_per_basis": args.shots,
                            "exact_total": model["exact_total"],
                            "raw_energy": raw["energy"],
                            "filtered_energy": filtered["energy"],
                            "raw_se": raw["standard_error"],
                            "filtered_se": filtered["standard_error"],
                            "acceptance": filtered["acceptance_fraction"],
                        }
                    )
        evidence.update(
            samples=len(rows),
            exact_and_noisy_controls=True,
            parity_checked_in_both_bases=True,
        )
    args.output.mkdir(parents=True, exist_ok=True)
    with (args.output / "samples.csv").open("w", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    summary = []
    for distance in [0.735, 1.4, 2.2]:
        selected = [
            r for r in rows if r["distance"] == distance and r["noise"] == "noisy"
        ]
        summary.append(
            {
                "distance": distance,
                "raw_mean_absolute_error_hartree": float(
                    np.mean([abs(r["raw_energy"] - r["exact_total"]) for r in selected])
                ),
                "filtered_mean_absolute_error_hartree": float(
                    np.mean(
                        [abs(r["filtered_energy"] - r["exact_total"]) for r in selected]
                    )
                ),
                "mean_acceptance": float(np.mean([r["acceptance"] for r in selected])),
            }
        )
    metrics = {
        "evidence": "statevector_curve_and_synthetic_aer_noise",
        "molecule": "H2",
        "basis": "STO-3G",
        "mapping": "parity with two-qubit reduction for (1,1) electrons",
        "ansatz": "one-parameter rotation within the Hartree-Fock/double-excitation determinant subspace",
        "qubits": 2,
        "repeats": args.repeats,
        "seed": args.seed,
        "shots_per_basis": args.shots,
        "curve": curve,
        "symmetry_filter_summary": summary,
        "limitations": "Minimal basis, fixed ideal optimized parameters; noise study measures energy, not noisy VQE training. No reaction barrier or quantum-speedup claim.",
    }
    (args.output / "metrics.json").write_text(json.dumps(metrics, indent=2) + "\n")
    fig, axes = plt.subplots(1, 2, figsize=(13, 5), constrained_layout=True)
    x = [m["distance"] for m in models]
    axes[0].plot(
        x,
        [m["hartree_fock_total"] for m in models],
        "o--",
        label="Hartree–Fock",
        color="#16817a",
    )
    axes[0].plot(
        x,
        [m["fci_total"] for m in models],
        "o-",
        label="Independent PySCF FCI",
        color="#272b35",
    )
    axes[0].scatter(
        x,
        [m["vqe_total"] for m in models],
        marker="x",
        s=70,
        label="Two-qubit variational",
        color="#784ec2",
    )
    axes[0].set(
        xlabel="H–H distance (angstrom)",
        ylabel="Total energy (hartree)",
        title="A real molecular Hamiltonian, independently checked",
    )
    axes[0].legend()
    labels = [str(s["distance"]) for s in summary]
    xpos = np.arange(len(summary))
    axes[1].bar(
        xpos - 0.2,
        [s["raw_mean_absolute_error_hartree"] for s in summary],
        width=0.4,
        label="Raw noisy",
        color="#c94747",
    )
    axes[1].bar(
        xpos + 0.2,
        [s["filtered_mean_absolute_error_hartree"] for s in summary],
        width=0.4,
        label="Parity filtered",
        color="#16817a",
    )
    axes[1].set(
        xticks=xpos,
        xticklabels=labels,
        xlabel="H–H distance (angstrom)",
        ylabel="Mean absolute energy error (hartree)",
        title="Can physical symmetry reject inconsistent samples?",
    )
    axes[1].legend()
    fig.suptitle(
        "BondBench | Two qubits · H₂ in STO-3G · synthetic gate/readout errors",
        fontsize=14,
    )
    fig.savefig(args.output / "bondbench.png", dpi=160)
    plt.close(fig)
    print(
        json.dumps(
            {
                "curve_points": len(curve),
                "sampling_runs": len(rows),
                "symmetry_results": summary,
            }
        )
    )


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=REPO / "results/chemistry")
    parser.add_argument("--shots", type=int, default=2048)
    parser.add_argument("--repeats", type=int, default=12)
    parser.add_argument("--seed", type=int, default=2026)
    args = parser.parse_args()
    if not 128 <= args.shots <= 100000 or not 2 <= args.repeats <= 100 or args.seed < 0:
        parser.error("Shots 128–100000, repeats 2–100, and nonnegative seed required")
    run(args)


if __name__ == "__main__":
    main()

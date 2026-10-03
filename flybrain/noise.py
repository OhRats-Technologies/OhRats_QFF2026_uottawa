"""Separate finite-shot error, gate noise, and readout noise in FlyWalk."""

import argparse
import csv
import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from qiskit import transpile
from qiskit.quantum_info import Statevector
from qiskit_aer import AerSimulator
from qiskit_aer.noise import NoiseModel, ReadoutError, depolarizing_error
from scipy.stats import t as student_t

from .data import REPO, load_graph
from .progress import timed_stage
from .walks import circuit_at, laplacian, undirected

CASES = [
    ("ideal", 0.0, 0.0),
    ("gate_0.002", 0.002, 0.0),
    ("gate_0.01", 0.01, 0.0),
    ("gate_0.03", 0.03, 0.0),
    ("readout_0.02", 0.0, 0.02),
    ("combined", 0.01, 0.02),
]


def noise_model(gate_error, readout_error):
    if not 0 <= gate_error <= 1 or not 0 <= readout_error <= 0.5:
        raise ValueError("Invalid noise probability")
    model = NoiseModel()
    if gate_error:
        # Synthetic illustrative errors, not measured IBM calibrations.
        model.add_all_qubit_quantum_error(depolarizing_error(gate_error, 2), ["cx"])
        model.add_all_qubit_quantum_error(
            depolarizing_error(gate_error / 10, 1), ["sx", "x"]
        )
    if readout_error:
        model.add_all_qubit_readout_error(
            ReadoutError(
                [[1 - readout_error, readout_error], [readout_error, 1 - readout_error]]
            )
        )
    return model


def readout_distribution(probabilities, error):
    n = len(probabilities)
    bits = n.bit_length() - 1
    channel = np.zeros((n, n))
    for observed in range(n):
        for actual in range(n):
            differing = (observed ^ actual).bit_count()
            channel[observed, actual] = error**differing * (1 - error) ** (
                bits - differing
            )
    return channel @ probabilities


def counts_distribution(counts, n):
    shots = sum(counts.values())
    result = np.zeros(n)
    for bits, count in counts.items():
        result[int(bits, 2)] = count / shots
    return result


def mean_interval(values):
    values = np.asarray(values)
    mean = float(values.mean())
    half = float(
        student_t.ppf(0.975, len(values) - 1)
        * values.std(ddof=1)
        / np.sqrt(len(values))
    )
    return mean, half


def run(args):
    nodes, adjacency, provenance = load_graph()
    generator = laplacian(undirected(adjacency))
    circuits, ideal = [], []
    for time_value in [4.0, 8.0]:
        circuit = circuit_at(generator, 0, time_value)
        ideal.append(Statevector.from_instruction(circuit).probabilities())
        circuit.measure_all()
        compiled = transpile(
            circuit,
            basis_gates=["rz", "sx", "x", "cx"],
            optimization_level=1,
            seed_transpiler=args.seed,
        )
        circuits.append(compiled)
    rows, summaries, references = [], [], []
    with timed_stage("noise-interference", "simulation_sweep") as log:
        for name, gate_error, readout_error in CASES:
            simulator = AerSimulator(
                method="density_matrix",
                noise_model=noise_model(gate_error, readout_error),
                max_parallel_threads=2,
            )
            for j, (circuit, time_value) in enumerate(zip(circuits, [4.0, 8.0])):
                exact_circuit = circuit.remove_final_measurements(inplace=False)
                exact_circuit.save_density_matrix()
                rho = np.asarray(
                    simulator.run(exact_circuit, shots=1)
                    .result()
                    .data(0)["density_matrix"]
                )
                if (
                    not np.isclose(np.trace(rho), 1)
                    or np.linalg.eigvalsh(rho).min() < -1e-10
                ):
                    raise ValueError("Invalid noisy density matrix")
                noisy_reference = readout_distribution(
                    np.real(np.diag(rho)), readout_error
                )
                coherence = float(np.abs(rho).sum() - np.abs(np.diag(rho)).sum())
                references.append(
                    {
                        "case": name,
                        "time": time_value,
                        "gate_error": gate_error,
                        "readout_error": readout_error,
                        "probabilities": noisy_reference.tolist(),
                        "l1_coherence_before_readout": coherence,
                        "exact_tv_from_ideal": float(
                            np.abs(noisy_reference - ideal[j]).sum() / 2
                        ),
                    }
                )
                for shots in [256, 1024, 4096]:
                    errors = []
                    for repeat in range(args.repeats):
                        seed = args.seed + 100000 * j + shots + repeat
                        counts = (
                            simulator.run(circuit, shots=shots, seed_simulator=seed)
                            .result()
                            .get_counts()
                        )
                        probabilities = counts_distribution(counts, len(nodes))
                        tv_ideal = float(np.abs(probabilities - ideal[j]).sum() / 2)
                        tv_noisy = float(
                            np.abs(probabilities - noisy_reference).sum() / 2
                        )
                        errors.append(tv_ideal)
                        rows.append(
                            {
                                "case": name,
                                "time": time_value,
                                "shots": shots,
                                "repeat": repeat,
                                "seed": seed,
                                "gate_error": gate_error,
                                "readout_error": readout_error,
                                "tv_from_ideal": tv_ideal,
                                "tv_from_noisy_exact": tv_noisy,
                            }
                        )
                    mean, half = mean_interval(errors)
                    summaries.append(
                        {
                            "case": name,
                            "time": time_value,
                            "shots": shots,
                            "mean_tv": mean,
                            "mc_mean_ci95_halfwidth": half,
                        }
                    )
        log.update(
            runs=len(rows),
            repeats=args.repeats,
            evidence="results/noise/raw.csv",
            gates={
                "probability_conservation": True,
                "positive_density_matrix": True,
                "separate_readout_and_gate_controls": True,
            },
        )
    args.output.mkdir(parents=True, exist_ok=True)
    with (args.output / "raw.csv").open("w", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    report = {
        "evidence": "synthetic_aer_noise_model",
        "dataset": provenance["dataset"],
        "source_commit": provenance["source_commit"],
        "repeats": args.repeats,
        "seed": args.seed,
        "nodes": nodes,
        "summaries": summaries,
        "noisy_exact_references": references,
        "noise_definition": "CX depolarizing p; sx/x depolarizing p/10; rz ideal; symmetric readout flip r",
        "uncertainty": "95% t interval of Monte Carlo mean across repeated sampling seeds, not hardware or biological uncertainty",
        "circuit_costs": [
            {"time": t, "depth": c.depth(), "operations": dict(c.count_ops())}
            for t, c in zip([4.0, 8.0], circuits)
        ],
    }
    (args.output / "metrics.json").write_text(json.dumps(report, indent=2) + "\n")
    fig, axes = plt.subplots(1, 2, figsize=(13, 5), constrained_layout=True)
    colors = ["#16817a", "#b76636", "#c94747", "#784ec2", "#3874a2", "#272b35"]
    for (name, _, _), color in zip(CASES, colors):
        selected = [s for s in summaries if s["case"] == name and s["time"] == 8]
        axes[0].errorbar(
            [s["shots"] for s in selected],
            [s["mean_tv"] for s in selected],
            yerr=[s["mc_mean_ci95_halfwidth"] for s in selected],
            marker="o",
            label=name,
            color=color,
            capsize=3,
        )
    axes[0].set(
        xscale="log",
        xlabel="Shots per run",
        ylabel="Mean total variation from ideal",
        title="More shots reduce sampling error; gate noise remains",
    )
    axes[0].legend(fontsize=8)
    selected = [r for r in references if r["time"] == 8]
    x = np.arange(len(selected))
    axes[1].bar(x, [r["l1_coherence_before_readout"] for r in selected], color=colors)
    axes[1].set(
        xticks=x,
        xticklabels=[r["case"] for r in selected],
        ylabel="L1 coherence before readout",
        title="Readout error changes counts, not the pre-readout state",
    )
    axes[1].tick_params(axis="x", rotation=35)
    fig.suptitle(
        "FlyWalk noise lab | Synthetic gate and readout errors · t = 8", fontsize=14
    )
    fig.savefig(args.output / "noise.png", dpi=160)
    plt.close(fig)
    print(f"Validated {len(rows)} sampling runs; results in {args.output}")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=REPO / "results/noise")
    parser.add_argument("--repeats", type=int, default=12)
    parser.add_argument("--seed", type=int, default=2026)
    args = parser.parse_args()
    if not 2 <= args.repeats <= 100 or args.seed < 0:
        parser.error("--repeats must be 2–100 and --seed nonnegative")
    run(args)


if __name__ == "__main__":
    main()

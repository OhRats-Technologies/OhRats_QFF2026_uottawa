"""FlyFlux: magnetic-Laplacian-style direction encoding, not biological quantum phases."""

import argparse, csv, json
from pathlib import Path
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from qiskit.quantum_info import Statevector
from .data import REPO, load_graph
from .walks import undirected, laplacian, circuit_at, sampled_walk
from .progress import timed_stage


def magnetic_laplacian(adjacency, charge):
    if not np.isfinite(charge) or not 0 <= charge <= 1:
        raise ValueError("Charge must be in [0,1]")
    adjacency = np.asarray(adjacency, dtype=float)
    weights = undirected(adjacency)
    imbalance = np.divide(
        adjacency - adjacency.T,
        adjacency + adjacency.T,
        out=np.zeros_like(adjacency),
        where=adjacency + adjacency.T > 0,
    )
    phases = (np.pi / 2) * charge * imbalance
    np.fill_diagonal(phases, 0)
    degree = weights.sum(axis=1)
    scale = degree.max()
    if scale <= 0:
        raise ValueError("Graph must have an edge")
    generator = (np.diag(degree) - weights * np.exp(1j * phases)) / scale
    if (
        not np.allclose(generator, generator.conj().T)
        or np.linalg.eigvalsh(generator).min() < -1e-10
    ):
        raise ValueError("Magnetic generator failed Hermiticity or positivity")
    return generator, phases


def quantum_probabilities(generator, times):
    eigenvalues, vectors = np.linalg.eigh(generator)
    probabilities = np.array(
        [
            np.abs((vectors * np.exp(-1j * t * eigenvalues)) @ vectors.conj().T) ** 2
            for t in times
        ]
    )
    if not np.allclose(probabilities.sum(axis=1), 1) or not np.allclose(
        probabilities.sum(axis=2), 1
    ):
        raise ValueError("Unitary probabilities are not doubly stochastic")
    return probabilities


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--output", type=Path, default=REPO / "results/flyflux")
    args = p.parse_args()
    nodes, adjacency, provenance = load_graph()
    times = np.linspace(0, 8, 81)
    comparisons = []
    arrays = {}
    rows = []
    with timed_stage("flyflux", "direction_phase_ablation") as evidence:
        for charge in [0.0, 0.5, 1.0]:
            generator, phases = magnetic_laplacian(adjacency, charge)
            reverse, _ = magnetic_laplacian(adjacency.T, charge)
            np.testing.assert_allclose(reverse, generator.conj(), atol=1e-12)
            forward_p = quantum_probabilities(generator, times)
            reverse_p = quantum_probabilities(reverse, times)
            np.testing.assert_allclose(
                reverse_p, forward_p.transpose(0, 2, 1), atol=1e-10
            )
            if charge == 0:
                np.testing.assert_allclose(
                    generator, laplacian(undirected(adjacency)), atol=1e-12
                )
            for time_index in [0, 20, 40, 60, 80]:
                check = Statevector.from_instruction(
                    circuit_at(generator, 0, times[time_index])
                ).probabilities()
                np.testing.assert_allclose(
                    check, forward_p[time_index, :, 0], atol=1e-10
                )
            distance = np.abs(forward_p - reverse_p).sum(axis=1) / 2
            source_averages = np.trapezoid(distance, x=times, axis=0) / times[-1]
            comparisons.append(
                {
                    "charge": charge,
                    "all_source_time_mean_reverse_tv": float(source_averages.mean()),
                    "per_source_time_mean_reverse_tv": source_averages.tolist(),
                    "source0_final_reverse_tv": float(distance[-1, 0]),
                    "phase_matrix_radians": phases.tolist(),
                    "forward_source0_final": forward_p[-1, :, 0].tolist(),
                    "reverse_source0_final": reverse_p[-1, :, 0].tolist(),
                }
            )
            arrays[str(charge)] = {
                "forward": np.round(forward_p, 8).tolist(),
                "reverse": np.round(reverse_p, 8).tolist(),
            }
            for t, d in zip(times, distance):
                for i, node in enumerate(nodes):
                    rows.append(
                        {
                            "charge": charge,
                            "time": t,
                            "source": node,
                            "forward_reverse_tv": float(d[i]),
                        }
                    )
        measured, cost = sampled_walk(
            magnetic_laplacian(adjacency, 1.0)[0], 0, 8.0, 4096, 2026
        )
        expected = np.array(comparisons[-1]["forward_source0_final"])
        evidence.update(
            charges=3,
            sources=8,
            time_steps=81,
            independent_qiskit_checks=True,
            reverse_transpose_identity=True,
            charge0_equals_flywalk=True,
            synthetic_sampling_tv=float(np.abs(measured - expected).sum() / 2),
        )
    args.output.mkdir(parents=True, exist_ok=True)
    with (args.output / "comparisons.csv").open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)
    report = {
        "evidence": "IDEAL_MAGNETIC_GRAPH_PHASE_MODEL_AND_LOCAL_SAMPLING",
        "nodes": nodes,
        "times": times.tolist(),
        "dataset": provenance["dataset"],
        "source_commit": provenance["source_commit"],
        "comparisons": comparisons,
        "phase_rule": "theta_ij=(pi/2)*charge*(A_ij-A_ji)/(A_ij+A_ji), zero when both contacts absent; diagonal zero",
        "hamiltonian": "[D(W)-W*exp(i theta)]/max(degree(W)), W=(A+A.T)/2 without self loops",
        "sampled_charge1_source0_final": measured.tolist(),
        "compiled_circuit": cost,
        "references": [
            "https://arxiv.org/abs/2102.11391",
            "https://arxiv.org/abs/1208.4049",
        ],
        "limitations": "Defined direction-imbalance encoding inspired by magnetic graph models, not a measured quantum phase or neuronal Hamiltonian. Unitary dynamics remain reversible; encoding direction does not make biological signaling reversible. This is not a new quantum-walk algorithm, a speedup, or population inference. Phase gauge choices on a tree can be invisible to transition probabilities; cycles matter.",
    }
    (args.output / "metrics.json").write_text(json.dumps(report, indent=2) + "\n")
    (args.output / "demo_trajectories.json").write_text(
        json.dumps(arrays, separators=(",", ":")) + "\n"
    )
    fig, axes = plt.subplots(2, 2, figsize=(12, 8), constrained_layout=True)
    for c, color in zip(comparisons, ["#72767e", "#16817a", "#7044bd"]):
        selected = [
            r for r in rows if r["charge"] == c["charge"] and r["source"] == nodes[0]
        ]
        axes[0, 0].plot(
            [r["time"] for r in selected],
            [r["forward_reverse_tv"] for r in selected],
            label=f"charge={c['charge']}",
            color=color,
        )
    axes[0, 0].set(
        xlabel="Dimensionless model time",
        ylabel="TV: forward vs reversed contacts",
        title="Symmetrization hides this difference",
    )
    axes[0, 0].legend()
    x = np.arange(8)
    last = comparisons[-1]
    axes[0, 1].bar(
        x - 0.18,
        last["forward_source0_final"],
        width=0.36,
        label="Forward encoding",
        color="#16817a",
    )
    axes[0, 1].bar(
        x + 0.18,
        last["reverse_source0_final"],
        width=0.36,
        label="Reversed encoding",
        color="#7044bd",
    )
    axes[0, 1].set(
        xticks=x,
        xticklabels=nodes,
        ylabel="Probability",
        title="Mi1_R start, t=8, charge=1",
    )
    axes[0, 1].tick_params(axis="x", rotation=40)
    axes[0, 1].legend(fontsize=8)
    axes[1, 0].bar(x, last["per_source_time_mean_reverse_tv"], color="#7044bd")
    axes[1, 0].set(
        xticks=x,
        xticklabels=nodes,
        ylabel="Time-mean forward/reverse TV",
        title="Check all starting populations",
    )
    axes[1, 0].tick_params(axis="x", rotation=40)
    image = axes[1, 1].imshow(
        last["phase_matrix_radians"], vmin=-np.pi / 2, vmax=np.pi / 2, cmap="coolwarm"
    )
    axes[1, 1].set(
        xticks=x,
        yticks=x,
        xticklabels=nodes,
        yticklabels=nodes,
        title="Chosen phase encoding: contact imbalance",
    )
    axes[1, 1].tick_params(axis="x", rotation=40)
    fig.colorbar(image, ax=axes[1, 1], label="Phase (radians)")
    fig.suptitle(
        "FlyFlux | Same contact magnitudes · directed imbalance in mathematical phases"
    )
    fig.savefig(args.output / "flyflux.png", dpi=160)
    plt.close(fig)
    print(
        json.dumps(
            {
                "comparisons": [
                    {
                        k: v
                        for k, v in c.items()
                        if k
                        in [
                            "charge",
                            "all_source_time_mean_reverse_tv",
                            "source0_final_reverse_tv",
                        ]
                    }
                    for c in comparisons
                ],
                "circuit": cost,
            }
        )
    )


if __name__ == "__main__":
    main()

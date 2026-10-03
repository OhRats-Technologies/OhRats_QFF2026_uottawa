"""All-source lesion atlas and predeclared shuffled-weight controls."""

import argparse
import csv
import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

from .data import REPO, load_graph
from .progress import timed_stage
from .walks import laplacian, trajectories, undirected


def all_source_trajectories(generator, times):
    """Spectral solution, shape (time, target, source); cross-checked with Qiskit."""
    eigenvalues, vectors = np.linalg.eigh(generator)
    classical = np.array(
        [(vectors * np.exp(-t * eigenvalues)) @ vectors.T for t in times]
    )
    quantum = np.array(
        [
            np.abs((vectors * np.exp(-1j * t * eigenvalues)) @ vectors.T) ** 2
            for t in times
        ]
    )
    if not np.allclose(classical.sum(axis=1), 1) or not np.allclose(
        quantum.sum(axis=1), 1
    ):
        raise ValueError("Probability conservation failed in spectral propagation")
    return np.maximum(classical, 0), quantum


def average_distance(a, b, times):
    tv = np.abs(a - b).sum(axis=1) / 2
    return np.trapezoid(tv, x=times, axis=0) / times[-1]


def shuffled_weights(weights, rng):
    upper = np.triu_indices(len(weights), 1)
    shuffled = np.zeros_like(weights)
    shuffled[upper] = rng.permutation(weights[upper])
    return shuffled + shuffled.T


def run(args):
    nodes, adjacency, provenance = load_graph()
    weights = undirected(adjacency)
    scale = weights.sum(axis=1).max()
    generator = laplacian(weights, scale)
    times = np.linspace(0, args.time, 41)
    classical, quantum = all_source_trajectories(generator, times)
    # Separate numerical route: a Qiskit circuit plus matrix exponential.
    check_c, check_q = trajectories(generator, 0, times[::10])
    np.testing.assert_allclose(check_c, classical[::10, :, 0], atol=1e-10)
    np.testing.assert_allclose(check_q, quantum[::10, :, 0], atol=1e-10)
    lesion_c = np.full((len(nodes), len(nodes)), np.nan)
    lesion_q = lesion_c.copy()
    rows = []
    with timed_stage("flywalk-atlas", "all_source_lesions") as evidence:
        for lesion in range(len(nodes)):
            damaged = weights.copy()
            damaged[lesion, :] = damaged[:, lesion] = 0
            dc, dq = all_source_trajectories(laplacian(damaged, scale), times)
            distances_c = average_distance(classical, dc, times)
            distances_q = average_distance(quantum, dq, times)
            for source in range(len(nodes)):
                if source == lesion:
                    continue
                lesion_c[source, lesion], lesion_q[source, lesion] = (
                    distances_c[source],
                    distances_q[source],
                )
                rows.append(
                    {
                        "source": nodes[source],
                        "lesion": nodes[lesion],
                        "classical_mean_tv": distances_c[source],
                        "quantum_mean_tv": distances_q[source],
                    }
                )
        evidence.update(
            interventions=len(rows),
            independent_qiskit_check=True,
            same_scale_all_lesions=True,
            evidence="results/atlas/lesions.csv",
        )
    observed = float(average_distance(classical, quantum, times).mean())
    rng = np.random.default_rng(args.seed)
    null = []
    with timed_stage("flywalk-null", "weight_permutation_controls") as evidence:
        for i in range(args.null_samples):
            shuffled = shuffled_weights(weights, rng)
            # Each graph gets its own normalized time scale, as in the intact model.
            nc, nq = all_source_trajectories(laplacian(shuffled), times)
            null.append(float(average_distance(nc, nq, times).mean()))
        evidence.update(
            samples=len(null),
            seed=args.seed,
            evidence="results/atlas/null.csv",
            statistic="mean across all sources of time-averaged classical/quantum TV",
        )
    args.output.mkdir(parents=True, exist_ok=True)
    with (args.output / "lesions.csv").open("w", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    with (args.output / "null.csv").open("w", newline="") as stream:
        writer = csv.writer(stream)
        writer.writerow(["replicate", "mean_classical_quantum_tv"])
        writer.writerows(enumerate(null))
    ranking_c, ranking_q = np.nanmean(lesion_c, axis=0), np.nanmean(lesion_q, axis=0)
    metrics = {
        "dataset": provenance["dataset"],
        "source_commit": provenance["source_commit"],
        "evidence": "exact_small_graph_simulation",
        "nodes": nodes,
        "time_end": args.time,
        "time_steps": len(times),
        "lesions": len(rows),
        "null_samples": args.null_samples,
        "seed": args.seed,
        "observed_mean_tv": observed,
        "null_mean_tv": float(np.mean(null)),
        "null_sd": float(np.std(null, ddof=1)),
        "descriptive_null_percentile": float(100 * np.mean(np.array(null) <= observed)),
        "classical_sensitivity": dict(zip(nodes, ranking_c.tolist())),
        "quantum_sensitivity": dict(zip(nodes, ranking_q.tolist())),
        "null_preserves": "symmetric complete topology and edge-weight multiset",
        "null_does_not_preserve": "node strengths, populations, spatial organization, or biological cell identity",
        "interpretation": "Selected graph descriptive controls; not population inference or evidence of quantum benefit",
    }
    (args.output / "metrics.json").write_text(json.dumps(metrics, indent=2) + "\n")
    fig, axes = plt.subplots(2, 2, figsize=(12, 9), constrained_layout=True)
    limit = max(np.nanmax(lesion_c), np.nanmax(lesion_q))
    for axis, matrix, title in [
        (axes[0, 0], lesion_c, "Classical lesion sensitivity"),
        (axes[0, 1], lesion_q, "Quantum lesion sensitivity"),
    ]:
        im = axis.imshow(
            np.ma.masked_invalid(matrix), cmap="viridis", vmin=0, vmax=limit
        )
        axis.set(
            xticks=range(len(nodes)),
            yticks=range(len(nodes)),
            xticklabels=nodes,
            yticklabels=nodes,
            xlabel="Disconnected cell type",
            ylabel="Starting cell type",
            title=title,
        )
        axis.tick_params(axis="x", rotation=45)
        fig.colorbar(im, ax=axis, shrink=0.8, label="Time-averaged TV")
    x = np.arange(len(nodes))
    axes[1, 0].bar(x - 0.2, ranking_c, width=0.4, label="Classical", color="#16817a")
    axes[1, 0].bar(x + 0.2, ranking_q, width=0.4, label="Quantum", color="#784ec2")
    axes[1, 0].set(
        xticks=x,
        xticklabels=nodes,
        ylabel="Mean across eligible starts",
        title="Which disconnections matter most?",
    )
    axes[1, 0].tick_params(axis="x", rotation=45)
    axes[1, 0].legend()
    axes[1, 1].hist(null, bins=15, color="#a7b9ca", edgecolor="white")
    axes[1, 1].axvline(
        observed, color="#c94747", linewidth=2, label="Observed fly graph"
    )
    axes[1, 1].set(
        xlabel="Mean classical/quantum TV",
        ylabel="Shuffled graphs",
        title="Weight-permutation controls",
    )
    axes[1, 1].legend()
    fig.suptitle(
        "FlyWalk atlas | 56 interventions · all eight starts · descriptive null controls",
        fontsize=14,
    )
    fig.savefig(args.output / "atlas.png", dpi=160)
    plt.close(fig)
    print(
        json.dumps(
            {
                "lesions": len(rows),
                "null_samples": len(null),
                "observed_mean_tv": observed,
                "null_mean": np.mean(null),
            }
        )
    )


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=REPO / "results/atlas")
    parser.add_argument("--time", type=float, default=8.0)
    parser.add_argument("--null-samples", type=int, default=99)
    parser.add_argument("--seed", type=int, default=2026)
    args = parser.parse_args()
    if (
        not np.isfinite(args.time)
        or args.time <= 0
        or not 2 <= args.null_samples <= 1000
        or args.seed < 0
    ):
        parser.error(
            "Positive finite time, 2–1000 null samples, and nonnegative seed required"
        )
    run(args)


if __name__ == "__main__":
    main()

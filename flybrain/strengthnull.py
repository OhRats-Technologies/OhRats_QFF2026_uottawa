"""Exploratory weighted controls preserving all node strengths and the time scale."""

import csv
import itertools
import json

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

from .atlas import all_source_trajectories, average_distance
from .data import REPO, load_graph
from .progress import timed_stage
from .walks import laplacian, undirected, trajectories


def four_edge_move(weights, rng):
    """Add delta to ab,cd and subtract it from ac,bd, preserving each row sum."""
    a, b, c, d = rng.choice(len(weights), 4, replace=False)
    lower = -min(weights[a, b], weights[c, d])
    upper = min(weights[a, c], weights[b, d])
    if upper <= lower:
        return
    delta = rng.uniform(lower, upper)
    for i, j, change in [(a, b, delta), (c, d, delta), (a, c, -delta), (b, d, -delta)]:
        weights[i, j] += change
        weights[j, i] += change


def move_span_rank(n):
    edges = list(itertools.combinations(range(n), 2))
    columns = {edge: i for i, edge in enumerate(edges)}
    directions = []
    for a, b, c, d in itertools.permutations(range(n), 4):
        row = np.zeros(len(edges))
        for i, j, sign in [(a, b, 1), (c, d, 1), (a, c, -1), (b, d, -1)]:
            row[columns[tuple(sorted((i, j)))]] += sign
        directions.append(row)
    return int(np.linalg.matrix_rank(directions))


def main():
    nodes, adjacency, provenance = load_graph()
    original = undirected(adjacency)
    strength = original.sum(axis=1)
    scale = strength.max()
    normalization = original.max()
    times = np.linspace(0, 8, 41)
    classical, quantum = all_source_trajectories(laplacian(original, scale), times)
    observed = float(average_distance(classical, quantum, times).mean())
    rows = []
    span = move_span_rank(len(nodes))
    if span != len(nodes) * (len(nodes) - 1) // 2 - len(nodes):
        raise ValueError("Four-edge moves do not span the fixed-strength subspace")
    maximum_strength_error = 0.0
    with timed_stage("flywalk-null", "fixed_strength_followup") as evidence:
        for seed in [2026, 2027, 2028]:
            rng = np.random.default_rng(seed)
            weights = original.copy() / normalization
            for _ in range(5000):
                four_edge_move(weights, rng)
            for sample in range(33):
                for _ in range(500):
                    four_edge_move(weights, rng)
                graph = weights * normalization
                error = float(np.max(np.abs(graph.sum(axis=1) - strength)))
                maximum_strength_error = max(maximum_strength_error, error)
                if error > 1e-6 or graph.min() < 0 or not np.allclose(graph, graph.T):
                    raise ValueError(
                        "Weighted control lost its strength or positivity invariant"
                    )
                if np.any(graph[np.triu_indices(len(nodes), 1)] <= 0):
                    raise ValueError(
                        "Control unexpectedly changed the complete topology"
                    )
                generator = laplacian(graph, scale)
                c, q = all_source_trajectories(generator, times)
                if sample == 0:
                    independent_c, independent_q = trajectories(
                        generator, 0, times[::20]
                    )
                    np.testing.assert_allclose(c[::20, :, 0], independent_c, atol=1e-10)
                    np.testing.assert_allclose(q[::20, :, 0], independent_q, atol=1e-10)
                rows.append(
                    {
                        "chain_seed": seed,
                        "sample": sample,
                        "mean_classical_quantum_tv": float(
                            average_distance(c, q, times).mean()
                        ),
                        "strength_error_contacts": error,
                        "relative_weight_displacement": float(
                            np.linalg.norm(graph - original) / np.linalg.norm(original)
                        ),
                    }
                )
        evidence.update(
            controls=len(rows),
            chains=3,
            move_span_rank=span,
            maximum_strength_error_contacts=maximum_strength_error,
            same_degree_matrix=True,
            same_time_scale=True,
            independent_qiskit_checks=True,
        )
    controls = np.array([r["mean_classical_quantum_tv"] for r in rows])
    chains = []
    for seed in [2026, 2027, 2028]:
        values = np.array(
            [r["mean_classical_quantum_tv"] for r in rows if r["chain_seed"] == seed]
        )
        lag1 = (
            float(np.corrcoef(values[:-1], values[1:])[0, 1])
            if values.std() > 1e-14
            else 0.0
        )
        chains.append(
            {
                "seed": seed,
                "mean": float(values.mean()),
                "std": float(values.std(ddof=1)),
                "lag1_statistic_correlation": lag1,
            }
        )
    report = {
        "origin": "CLASSICAL_STRENGTH_PRESERVING_WEIGHTED_GRAPH_CONTROLS",
        "source_commit": provenance["source_commit"],
        "nodes": nodes,
        "observed_mean_classical_quantum_tv": observed,
        "control_mean": float(controls.mean()),
        "control_standard_deviation": float(controls.std(ddof=1)),
        "fraction_controls_below_observed_descriptive": float(
            np.mean(controls < observed)
        ),
        "chains": chains,
        "burn_in_moves": 5000,
        "moves_between_samples": 500,
        "samples_per_chain": 33,
        "move_span_rank": span,
        "maximum_strength_error_contacts": maximum_strength_error,
        "node_strengths_contacts": strength.tolist(),
        "intact_degree_scale": float(scale),
        "time_grid": times.tolist(),
        "method": "Four-edge balanced continuous-weight moves on the complete graph; positive weights, fixed row sums, unchanged degree matrix and intact scale. Delta is uniform on its positivity interval. Three finite chains start at the observed graph.",
        "limitations": "Exploratory follow-up after viewing the shuffled-weight results, not preregistered. Finite Markov-chain samples are dependent; span and invariant checks are not proof of convergence or independent uniform samples. The descriptive ordering is not a biological p-value. Continuous weighted alternatives are mathematical controls, not newly measured synapse counts. Edge-weight multiset is not preserved; this complements the original multiset-preserving shuffle. No population inference or quantum advantage is claimed.",
    }
    out = REPO / "results/strengthnull"
    out.mkdir(parents=True, exist_ok=True)
    (out / "metrics.json").write_text(json.dumps(report, indent=2) + "\n")
    with (out / "controls.csv").open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=rows[0])
        writer.writeheader()
        writer.writerows(rows)
    fig, axes = plt.subplots(1, 2, figsize=(12, 4), constrained_layout=True)
    axes[0].hist(
        controls, bins=16, color="#16817a", alpha=0.8, label="Fixed-strength controls"
    )
    axes[0].axvline(observed, color="#7044bd", linewidth=2, label="Selected real graph")
    axes[0].set(
        xlabel="All-source / time-mean classical-quantum TV",
        ylabel="Control count",
        title="Does the comparison survive a stricter control?",
    )
    axes[0].legend(fontsize=8)
    for seed, color in zip([2026, 2027, 2028], ["#16817a", "#7044bd", "#3874a2"]):
        selected = [r for r in rows if r["chain_seed"] == seed]
        axes[1].plot(
            [r["sample"] for r in selected],
            [r["mean_classical_quantum_tv"] for r in selected],
            label=str(seed),
            color=color,
        )
    axes[1].axhline(observed, color="#ba5144", ls="--", label="Observed")
    axes[1].set(
        xlabel="Thinned sample within a finite chain",
        ylabel="Classical-quantum TV",
        title="Check separate chains; do not assume independence",
    )
    axes[1].legend(fontsize=8)
    fig.suptitle("FlyWalk | Preserve every node strength and the intact time scale")
    fig.savefig(out / "strengthnull.png", dpi=160)
    plt.close(fig)
    print(
        json.dumps(
            {
                "observed": observed,
                "control_mean": report["control_mean"],
                "descriptive_fraction_below": report[
                    "fraction_controls_below_observed_descriptive"
                ],
                "maximum_strength_error": maximum_strength_error,
                "chains": chains,
            }
        )
    )


if __name__ == "__main__":
    main()

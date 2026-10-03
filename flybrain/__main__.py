"""Run with uv run python -m flybrain; no external services or hardware required."""

import argparse
import csv
import json
from pathlib import Path
import time

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

from .data import DEFAULT_DATA, REPO, fetch_snapshot, load_graph
from .walks import laplacian, sampled_walk, trajectories, undirected


def run(args):
    start = time.perf_counter()
    nodes, directed, manifest = load_graph(args.data)
    if args.source not in nodes:
        raise ValueError(f"Unknown source; choose from {', '.join(nodes)}")
    source = nodes.index(args.source)
    weights = undirected(directed)
    scale = weights.sum(axis=1).max()
    generator = laplacian(weights, scale)
    if args.lesion == "auto":
        lesion = max(
            (i for i in range(len(nodes)) if i != source),
            key=lambda i: (weights[i].sum(), -i),
        )
    elif args.lesion in nodes:
        lesion = nodes.index(args.lesion)
    else:
        raise ValueError("Lesion must be auto or a node ID in the snapshot")
    if lesion == source:
        raise ValueError("Choose a lesion different from the starting node")
    damaged = weights.copy()
    damaged[lesion, :] = damaged[:, lesion] = 0
    # Keep original scale so lesion comparisons use the same model time units.
    damaged_generator = laplacian(damaged, scale)
    times = np.linspace(0, args.time, args.steps)
    classical, quantum = trajectories(generator, source, times)
    lesion_classical, lesion_quantum = trajectories(damaged_generator, source, times)
    sampled, cost = sampled_walk(generator, source, args.time, args.shots, args.seed)
    tv = lambda a, b: 0.5 * np.abs(a - b).sum(axis=-1)
    metrics = {
        "dataset": manifest["dataset"],
        "source_commit": manifest["source_commit"],
        "snapshot_files": manifest["files"],
        "source": args.source,
        "lesion": nodes[lesion],
        "nodes": len(nodes),
        "qubits": len(nodes).bit_length() - 1,
        "directed_edges_including_self": int(np.count_nonzero(directed)),
        "model_edges": int(np.count_nonzero(np.triu(weights, 1))),
        "time_end": args.time,
        "time_steps": args.steps,
        "time_unit": "dimensionless, not biological time",
        "degree_scale": float(scale),
        "shots": args.shots,
        "seed": args.seed,
        "final_classical_quantum_tv": float(tv(classical[-1], quantum[-1])),
        "final_classical_lesion_tv": float(tv(classical[-1], lesion_classical[-1])),
        "final_quantum_lesion_tv": float(tv(quantum[-1], lesion_quantum[-1])),
        "final_sampling_tv": float(tv(sampled, quantum[-1])),
        "circuit": cost,
        "elapsed_seconds": time.perf_counter() - start,
        "interpretation": "Descriptive model comparison on one selected cell-type subgraph; no biological or quantum-advantage claim",
    }
    out = args.output
    out.mkdir(parents=True, exist_ok=True)
    (out / "metrics.json").write_text(json.dumps(metrics, indent=2) + "\n")
    with (out / "probabilities.csv").open("w", newline="") as stream:
        writer = csv.writer(stream)
        writer.writerow(
            [
                "time",
                "node",
                "classical",
                "quantum",
                "lesion_classical",
                "lesion_quantum",
            ]
        )
        for t, time_value in enumerate(times):
            for i, node in enumerate(nodes):
                writer.writerow(
                    [
                        time_value,
                        node,
                        classical[t, i],
                        quantum[t, i],
                        lesion_classical[t, i],
                        lesion_quantum[t, i],
                    ]
                )
    with (out / "sampled_probabilities.csv").open("w", newline="") as stream:
        writer = csv.writer(stream)
        writer.writerow(["node", "exact", "sampled"])
        writer.writerows(zip(nodes, quantum[-1], sampled))

    plt.rcParams.update(
        {"font.size": 10, "axes.spines.top": False, "axes.spines.right": False}
    )
    fig, axes = plt.subplots(2, 2, figsize=(13, 9), constrained_layout=True)
    im = axes[0, 0].imshow(np.log1p(directed), cmap="magma")
    axes[0, 0].set(
        xticks=range(len(nodes)),
        yticks=range(len(nodes)),
        xticklabels=nodes,
        yticklabels=nodes,
        xlabel="Target cell type",
        ylabel="Source cell type",
        title="Observed directed contacts (log1p count)",
    )
    axes[0, 0].tick_params(axis="x", rotation=45)
    fig.colorbar(im, ax=axes[0, 0], shrink=0.8)
    axes[0, 1].plot(times, classical[:, source], label="Classical", color="#16817a")
    axes[0, 1].plot(times, quantum[:, source], label="Quantum", color="#784ec2")
    axes[0, 1].set(
        xlabel="Dimensionless model time",
        ylabel="Probability at starting node",
        title=f"Return to {args.source}",
        ylim=(0, 1.02),
    )
    axes[0, 1].legend()
    x = np.arange(len(nodes))
    axes[1, 0].bar(
        x - 0.2, classical[-1], width=0.4, label="Classical", color="#16817a"
    )
    axes[1, 0].bar(x + 0.2, quantum[-1], width=0.4, label="Quantum", color="#784ec2")
    axes[1, 0].set(
        xticks=x,
        xticklabels=nodes,
        ylabel="Probability",
        title=f"Distribution at t = {args.time:g}",
    )
    axes[1, 0].tick_params(axis="x", rotation=45)
    axes[1, 0].legend()
    axes[1, 1].plot(
        times, tv(classical, lesion_classical), label="Classical", color="#16817a"
    )
    axes[1, 1].plot(
        times, tv(quantum, lesion_quantum), label="Quantum", color="#784ec2"
    )
    axes[1, 1].set(
        xlabel="Dimensionless model time",
        ylabel="Total variation from intact model",
        title=f"Disconnect {nodes[lesion]} (same time scale)",
        ylim=(0, 1.02),
    )
    axes[1, 1].legend()
    fig.suptitle(
        "FlyWalk | Eight visual-system cell types, three qubits\n"
        "MaleCNS v1.0 · structural graph experiment · local simulation",
        fontsize=15,
    )
    fig.savefig(out / "experiment.png", dpi=160)
    plt.close(fig)
    print(json.dumps(metrics, indent=2))
    print(f"Results: {out}")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    fetch = sub.add_parser(
        "fetch", help="Recreate snapshot from pinned public source pages"
    )
    fetch.add_argument("--data", type=Path, default=DEFAULT_DATA)
    experiment = sub.add_parser(
        "run", help="Run the included real-data experiment offline"
    )
    experiment.add_argument("--data", type=Path, default=DEFAULT_DATA)
    experiment.add_argument("--output", type=Path, default=REPO / "results/flywalk")
    experiment.add_argument("--source", default="Mi1_R")
    experiment.add_argument(
        "--lesion", default="auto", help="Node ID, or strongest non-source node"
    )
    experiment.add_argument("--time", type=float, default=8.0)
    experiment.add_argument("--steps", type=int, default=81)
    experiment.add_argument("--shots", type=int, default=4096)
    experiment.add_argument("--seed", type=int, default=2026)
    channel = sub.add_parser(
        "channel", help="Run connectome spectral dynamics and quantum channel mixing"
    )
    channel.add_argument("--steps", type=int, default=16)
    channel.add_argument("--gamma", type=float, default=0.6)
    channel.add_argument("--output", type=Path, default=REPO / "results/spectral_channel")
    channel.add_argument("--seed", type=int, default=2026)
    args = parser.parse_args()
    try:
        if args.command == "fetch":
            manifest = fetch_snapshot(args.data)
            print(
                f"Saved {len(manifest['sources'])} cell-type pages as a graph snapshot in {args.data}"
            )
        elif args.command == "channel":
            from .channel_cli import run as run_channel
            run_channel(
                [
                    "--steps", str(args.steps),
                    "--gamma", str(args.gamma),
                    "--output", str(args.output),
                    "--seed", str(args.seed),
                ]
            )
        else:
            if (
                not np.isfinite(args.time)
                or args.time <= 0
                or not 2 <= args.steps <= 1001
            ):
                parser.error(
                    "--time must be positive and finite; --steps must be 2–1001"
                )
            if not 1 <= args.shots <= 1000000 or args.seed < 0:
                parser.error("--shots must be 1–1000000 and --seed nonnegative")
            run(args)
    except (ValueError, OSError, KeyError) as error:
        parser.exit(1, f"Error: {error}\n")


if __name__ == "__main__":
    main()

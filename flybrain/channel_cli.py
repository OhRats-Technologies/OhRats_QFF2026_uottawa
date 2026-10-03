"""Command-line runner for connectome spectral dynamics and quantum channel mixing."""

import argparse
import json
from pathlib import Path
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

from .data import REPO, load_graph
from .progress import timed_stage
from .quantum_channel import (
    ConnectomeQuantumChannel,
    choi_density_matrix,
    compare_classical_and_quantum_mixing,
    compute_ppt_negativity,
    construct_entanglement_witness,
    run_witness_aer,
)
from .spectral import (
    SynapseFlowChain,
    certified_mixing_bounds,
    dobrushin_coefficient,
    pruning_sweep,
    signed_influence_map,
)

DEFAULT_OUTPUT = REPO / "results/spectral_channel"


def plot_forgetting_and_entanglement(profile, output_dir: Path):
    """Plot dual comparison of classical Dobrushin forgetting vs quantum entanglement decay."""
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(11, 4.5), dpi=200)

    steps = profile.steps

    # Left plot: Classical Dobrushin bounds
    ax1.plot(
        steps,
        profile.classical_lower_bound,
        label="Certified Lower Bound",
        color="#2563eb",
        linewidth=2,
    )
    ax1.plot(
        steps,
        profile.classical_upper_bound,
        label="Certified Upper Bound",
        color="#2563eb",
        linestyle="--",
        linewidth=1.5,
    )
    ax1.plot(
        steps,
        profile.classical_dobrushin,
        label="Exact Dobrushin $\\tau(P^r)$",
        color="#1d4ed8",
        marker="o",
        markersize=4,
    )
    ax1.set_xlabel("Synaptic / Channel Steps $r$", fontsize=11)
    ax1.set_ylabel("Dobrushin Ergodicity Coefficient $\\tau(P^r)$", fontsize=11)
    ax1.set_title("Classical Mixing: Forgetting Initial State", fontsize=12, fontweight="bold")
    ax1.set_ylim(-0.05, 1.05)
    ax1.grid(True, linestyle=":", alpha=0.6)
    ax1.legend(loc="upper right", frameon=True)

    # Right plot: Quantum Entanglement-Breaking
    ax2.plot(
        steps,
        profile.choi_negativity,
        label="Choi Negativity $\\mathcal{N}(J(\\mathcal{E}^r))$",
        color="#dc2626",
        marker="s",
        markersize=4,
        linewidth=2,
    )
    ax2.plot(
        steps,
        profile.trace_distance_to_stationary,
        label="Trace Dist to Stationary $\\rho_\\infty$",
        color="#9333ea",
        linestyle="-.",
        linewidth=1.5,
    )
    if profile.entanglement_breaking_index is not None:
        ax2.axvline(
            profile.entanglement_breaking_index,
            color="#059669",
            linestyle=":",
            linewidth=2,
            label=f"EB Index $n_{{EB}} = {profile.entanglement_breaking_index}$",
        )
    ax2.set_xlabel("Synaptic / Channel Steps $r$", fontsize=11)
    ax2.set_ylabel("Negativity / Trace Distance", fontsize=11)
    ax2.set_title(
        "Quantum Channel: Entanglement Breaking", fontsize=12, fontweight="bold"
    )
    ax2.set_ylim(-0.05, max(1.1, max(profile.choi_negativity) * 1.15))
    ax2.grid(True, linestyle=":", alpha=0.6)
    ax2.legend(loc="upper right", frameon=True)

    plt.tight_layout()
    plot_path = output_dir / "forgetting_vs_entanglement.png"
    plt.savefig(plot_path)
    plt.close()
    return plot_path


def plot_pruning_traps(pruning_results: list, output_dir: Path):
    """Plot lambda_2 and conductance across pruning thresholds."""
    valid_res = [r for r in pruning_results if "error" not in r]
    if not valid_res:
        return None

    thresh = [r["threshold"] for r in valid_res]
    lam2 = [r["lambda2_modulus"] for r in valid_res]
    cond = [r["conductance"] for r in valid_res]
    escape = [r["escape_probability"] for r in valid_res]

    fig, ax1 = plt.subplots(figsize=(6.5, 4.5), dpi=200)

    color = "#dc2626"
    ax1.set_xlabel("Pruning Threshold $\\theta$ (synapses dropped if $w < \\theta$)", fontsize=11)
    ax1.set_ylabel("Second Eigenvalue Modulus $|\\lambda_2|$", color=color, fontsize=11)
    line1 = ax1.plot(thresh, lam2, color=color, marker="o", linewidth=2, label="$|\\lambda_2|$ (Slow mode)")
    ax1.tick_params(axis="y", labelcolor=color)
    ax1.set_ylim(0.0, 1.05)

    ax2 = ax1.twinx()
    color2 = "#2563eb"
    ax2.set_ylabel("Conductance $\\phi(S)$ / Escape Prob", color=color2, fontsize=11)
    line2 = ax2.plot(thresh, cond, color=color2, marker="s", linestyle="--", linewidth=1.8, label="Conductance $\\phi$")
    line3 = ax2.plot(thresh, escape, color="#059669", marker="^", linestyle=":", linewidth=1.8, label="Escape Prob")
    ax2.tick_params(axis="y", labelcolor=color2)
    ax2.set_ylim(-0.05, max(0.5, max(cond + escape) * 1.2))

    lines = line1 + line2 + line3
    labels = [l.get_label() for l in lines]
    ax1.legend(lines, labels, loc="center right", frameon=True)

    plt.title("Boundary Trap Formation Under Weak Edge Pruning", fontsize=12, fontweight="bold")
    plt.tight_layout()
    plot_path = output_dir / "pruning_boundary_traps.png"
    plt.savefig(plot_path)
    plt.close()
    return plot_path


def run(args=None):
    parser = argparse.ArgumentParser(
        description="Connectome spectral dynamics and quantum channel mixing analysis"
    )
    parser.add_argument(
        "--steps", type=int, default=16, help="Maximum steps for mixing/channel comparison"
    )
    parser.add_argument(
        "--gamma", type=float, default=0.6, help="Coherence retention parameter for quantum channel"
    )
    parser.add_argument(
        "--output", type=Path, default=DEFAULT_OUTPUT, help="Output directory for results"
    )
    parser.add_argument(
        "--seed", type=int, default=2026, help="Deterministic random seed"
    )
    opts = parser.parse_args(args)

    opts.output.mkdir(parents=True, exist_ok=True)
    nodes, adjacency, manifest = load_graph()

    print(f"Loaded MaleCNS graph: {len(nodes)} nodes, {np.count_nonzero(adjacency)} directed edges.")

    with timed_stage("spectral-connectome", "classical_analysis") as log:
        chain = SynapseFlowChain(adjacency, node_names=nodes, extract_giant_scc=True)
        sweep = chain.sweep_cut()

        # Pruning sweep demonstrating boundary trap formation
        thresholds = [0, 20, 50, 200, 500, 1000, 5000]
        prune_res = pruning_sweep(adjacency, thresholds, node_names=nodes)

        # Signed map analysis (using excitatory for Mi1/Tm3 and inhibitory for others as illustration)
        # Signs: +1 for Mi1_R, Tm3_R; -1 for GABAergic Pm neurons; -1 for others
        signs = [1, -1, -1, -1, -1, 1, -1, -1]
        evals_raw, _, pr_raw = signed_influence_map(adjacency, signs, floor=None)
        median_input = float(np.median(adjacency.sum(axis=0)))
        evals_floor, _, pr_floor = signed_influence_map(adjacency, signs, floor=median_input)

    with timed_stage("quantum-channel", "entanglement_breaking_profile") as log:
        profile = compare_classical_and_quantum_mixing(
            chain.P, gamma=opts.gamma, max_steps=opts.steps
        )

        # Witness check on initial Choi state
        base_channel = ConnectomeQuantumChannel(chain.P, gamma=opts.gamma)
        choi1 = choi_density_matrix(base_channel)
        witness1, min_val1 = construct_entanglement_witness(choi1, chain.n)
        witness_sim = run_witness_aer(choi1, witness1, base_channel.num_qubits, seed=opts.seed)

    # Save plots
    plot1 = plot_forgetting_and_entanglement(profile, opts.output)
    plot2 = plot_pruning_traps(prune_res, opts.output)

    summary = {
        "dataset": manifest.get("dataset", "male-cns:v1.0"),
        "nodes": chain.node_names,
        "spectral_properties": {
            "lambda1": 1.0,
            "lambda2_modulus": float(np.abs(chain.lambda2)),
            "spectral_gap": chain.spectral_gap,
            "stationary_distribution": chain.pi.tolist(),
            "sweep_cut": {
                "nodes": [chain.node_names[i] for i in sweep.cut_nodes],
                "conductance": sweep.conductance,
                "stationary_mass": sweep.stationary_mass,
                "escape_probability": sweep.escape_probability,
                "two_block_estimate": sweep.two_block_estimate,
            },
        },
        "pruning_sweep": prune_res,
        "signed_influence_map": {
            "unfloored": {
                "spectral_radius": float(np.abs(evals_raw[0])),
                "leading_eigenvalue": float(np.real(evals_raw[0])),
                "leading_participation_ratio": float(pr_raw[0]),
            },
            "floored_median": {
                "floor_threshold": median_input,
                "spectral_radius": float(np.abs(evals_floor[0])),
                "leading_eigenvalue": float(np.real(evals_floor[0])),
                "leading_participation_ratio": float(pr_floor[0]),
            },
        },
        "quantum_channel": {
            "gamma": opts.gamma,
            "entanglement_breaking_index": profile.entanglement_breaking_index,
            "choi_negativity": profile.choi_negativity,
            "classical_dobrushin": profile.classical_dobrushin,
            "witness_r1": witness_sim,
        },
        "artifacts": {
            "forgetting_vs_entanglement_plot": str(plot1),
            "pruning_boundary_traps_plot": str(plot2),
        },
    }

    out_file = opts.output / "results.json"
    out_file.write_text(json.dumps(summary, indent=2) + "\n")
    print(f"Results successfully saved to {out_file}")
    print(f"Spectral gap: {chain.spectral_gap:.4f}, |lambda2|: {float(np.abs(chain.lambda2)):.4f}")
    print(f"Sweep cut of lowest conductance: {[chain.node_names[i] for i in sweep.cut_nodes]} (escape prob: {sweep.escape_probability:.4f})")
    print(f"Quantum Entanglement-Breaking Index n_EB: {profile.entanglement_breaking_index}")
    return summary


if __name__ == "__main__":
    run()

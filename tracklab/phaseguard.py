"""PhaseGuard: same warm-start probabilities, corrected phases, matched gate cost."""

import json, csv
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from qiskit import transpile
from qiskit.quantum_info import Statevector
from qiskit_aer import AerSimulator
from flybrain.data import REPO
from flybrain.noise import noise_model
from flybrain.progress import timed_stage
from .scheduling import circuit, distribution_metrics


def main():
    search = json.loads((REPO / "results/mixerbench/metrics.json").read_text())["rows"]
    references = []
    samples = []
    with timed_stage("phaseguard", "same_probability_phase_noise_ablation") as evidence:
        for preparation in ["pair", "phase_pair", "dicke"]:
            row = next(
                r
                for r in search
                if r["preparation"] == preparation
                and r["depth"] == 1
                and r["seed"] == 2026
            )
            qc = circuit(row["parameters"], "xy", preparation)
            ideal = Statevector.from_instruction(qc).probabilities()
            initial = Statevector.from_instruction(circuit([], "xy", preparation))
            references.append(
                {
                    **row,
                    "initial_probabilities": initial.probabilities().tolist(),
                    "initial_phases_radians": np.angle(initial.data).tolist(),
                    "final_probabilities": ideal.tolist(),
                }
            )
            qc.measure_all()
            compiled = transpile(
                qc,
                basis_gates=["rz", "sx", "x", "cx"],
                optimization_level=1,
                seed_transpiler=2026,
            )
            for p in [0.0, 0.002, 0.005, 0.01, 0.03]:
                sim = AerSimulator(
                    method="density_matrix",
                    noise_model=noise_model(p, 0.01 if p else 0),
                    max_parallel_threads=2,
                )
                for repeat in range(24):
                    counts = (
                        sim.run(compiled, shots=1024, seed_simulator=2026 + repeat)
                        .result()
                        .get_counts()
                    )
                    probabilities = np.array(
                        [counts.get(format(i, "04b"), 0) / 1024 for i in range(16)]
                    )
                    samples.append(
                        {
                            "preparation": preparation,
                            "gate_error": p,
                            "readout_error": 0.01 if p else 0,
                            "repeat": repeat,
                            **distribution_metrics(probabilities),
                        }
                    )
        np.testing.assert_allclose(
            references[0]["initial_probabilities"],
            references[1]["initial_probabilities"],
            atol=1e-12,
        )
        if references[0]["cx"] != references[1]["cx"]:
            raise ValueError("CX costs differ")
        evidence.update(
            runs=len(samples),
            same_initial_probabilities=True,
            matched_optimizer=True,
            same_cx_pair_variants=True,
            shots=1024,
            repeats=24,
        )
    out = REPO / "results/phaseguard"
    out.mkdir(parents=True, exist_ok=True)
    with (out / "samples.csv").open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(samples[0]))
        w.writeheader()
        w.writerows(samples)
    report = {
        "evidence": "ideal_and_synthetic_noise_phase_ablation",
        "references": references,
        "samples": samples,
        "discovery": "Two RZ(pi/2) corrections undo the paired warm start exchange phases. Initial probabilities and compiled CX count are unchanged; later interference changes.",
        "limitations": "Adaptive follow-up on one easy scheduling instance; no novel algorithm or practical quantum advantage claim. The corrected circuit was not in the three previously submitted IBM jobs. Noise here is illustrative, not calibrated.",
    }
    (out / "metrics.json").write_text(json.dumps(report, indent=2) + "\n")
    fig, axes = plt.subplots(1, 2, figsize=(13, 5), constrained_layout=True)
    for prep, color in [
        ("pair", "#16817a"),
        ("phase_pair", "#b76636"),
        ("dicke", "#784ec2"),
    ]:
        means = []
        halves = []
        for p in [0, 0.002, 0.005, 0.01, 0.03]:
            values = [
                r["optimal_probability"]
                for r in samples
                if r["preparation"] == prep and r["gate_error"] == p
            ]
            means.append(np.mean(values))
            halves.append(1.96 * np.std(values, ddof=1) / np.sqrt(len(values)))
        axes[0].errorbar(
            [0, 0.002, 0.005, 0.01, 0.03],
            means,
            yerr=halves,
            marker="o",
            label=prep,
            color=color,
            capsize=3,
        )
    axes[0].set(
        xlabel="Synthetic CX depolarizing probability",
        ylabel="Unconditional optimal-schedule probability",
        title="One layer; matched optimizer and sampling budget",
        ylim=(0, 1.05),
    )
    axes[0].legend()
    x = np.arange(16)
    for r, color in zip(references[:2], ["#16817a", "#b76636"]):
        axes[1].plot(
            x, r["final_probabilities"], "o-", color=color, label=r["preparation"]
        )
    axes[1].set(
        xticks=[3, 5, 6, 9, 10, 12],
        xticklabels=[format(i, "04b") for i in [3, 5, 6, 9, 10, 12]],
        xlabel="Valid schedule bitstring (optimum 1001)",
        ylabel="Final probability",
        title="Identical initial histograms; different final outcomes",
    )
    axes[1].legend()
    fig.suptitle("PhaseGuard | Two local phase corrections · no additional CX gates")
    fig.savefig(out / "phaseguard.png", dpi=160)
    plt.close(fig)
    print(
        json.dumps(
            {
                "runs": len(samples),
                "ideal_optimal_probabilities": {
                    r["preparation"]: r["optimal_probability"] for r in references
                },
            }
        )
    )


if __name__ == "__main__":
    main()

"""SpinWeave: four-spin dimerization and an energy-based entanglement witness."""

import argparse, csv, json
from pathlib import Path
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from qiskit import QuantumCircuit, transpile
from qiskit.quantum_info import SparsePauliOp, Statevector, partial_trace, entropy
from qiskit_aer import AerSimulator
from scipy.optimize import minimize
from flybrain.data import REPO
from flybrain.noise import noise_model
from flybrain.progress import timed_stage
from .chemistry import mean_and_se

BONDS = [(0, 1), (1, 2), (2, 3), (3, 0)]


def hamiltonian(delta):
    if not 0 <= delta <= 1:
        raise ValueError("Dimerization must lie in [0,1]")
    couplings = [1 + delta, 1 - delta, 1 + delta, 1 - delta]
    terms = []
    for (a, b), j in zip(BONDS, couplings):
        for axis in "XYZ":
            label = ["I"] * 4
            label[3 - a] = axis
            label[3 - b] = axis
            terms.append(("".join(label), j / 4))
    return SparsePauliOp.from_list(terms), couplings


def preparation(params):
    # Product of singlets on strong bonds, with number-conserving exchanges and Z phases.
    if len(params) != 8:
        raise ValueError("Eight bounded parameters expected")
    qc = QuantumCircuit(4)
    for a, b in [(0, 1), (2, 3)]:
        qc.x(b)
        qc.h(a)
        qc.cx(a, b)
        qc.z(a)
    for layer in range(2):
        weak, strong, phase0, phase1 = params[layer * 4 : layer * 4 + 4]
        for angle, pairs in [(weak, [(1, 2), (3, 0)]), (strong, [(0, 1), (2, 3)])]:
            for a, b in pairs:
                qc.rxx(angle, a, b)
                qc.ryy(angle, a, b)
                qc.rzz(angle, a, b)
        qc.rz(phase0, 0)
        qc.rz(phase1, 1)
        qc.rz(-phase0, 2)
        qc.rz(-phase1, 3)
    return qc


def solve(delta, seed=2026):
    operator, couplings = hamiltonian(delta)
    matrix = operator.to_matrix()
    exact = float(np.linalg.eigvalsh(matrix).min())
    rng = np.random.default_rng(seed)
    trials = []
    for start in range(4):
        x0 = np.zeros(8) if start == 0 else rng.normal(scale=0.7, size=8)
        result = minimize(
            lambda p: float(
                Statevector.from_instruction(preparation(p))
                .expectation_value(operator)
                .real
            ),
            x0,
            method="BFGS",
            options={"maxiter": 180, "gtol": 1e-7},
        )
        trials.append(
            {
                "parameters": result.x.tolist(),
                "energy": float(result.fun),
                "evaluations": int(result.nfev),
                "converged": bool(result.success),
            }
        )
    best = min(trials, key=lambda t: t["energy"])
    qc = preparation(best["parameters"])
    sv = Statevector.from_instruction(qc)
    if best["energy"] < exact - 1e-8:
        raise ValueError("Variational energy below exact minimum")
    if sum(sv.probabilities()[i] for i in range(16) if i.bit_count() != 2) > 1e-10:
        raise ValueError("Spin preparation lost magnetization conservation")
    return {
        "delta": delta,
        "couplings": couplings,
        "exact_energy": exact,
        "variational_energy": best["energy"],
        "variational_error": best["energy"] - exact,
        "parameters": best["parameters"],
        "trials": trials,
        "half_chain_entropy_bits": float(entropy(partial_trace(sv, [2, 3]), base=2)),
        "separable_energy_bound": -sum(couplings) / 4,
        "circuit": qc,
    }


def measurement_circuits(qc):
    circuits = []
    for axis in "XYZ":
        m = qc.copy()
        for i in range(4):
            if axis == "X":
                m.h(i)
            if axis == "Y":
                m.sdg(i)
                m.h(i)
        m.measure_all()
        circuits.append(m)
    return circuits


def measured_energy(couplings, counts):
    def value(bits):
        signs = [1 - 2 * ((bits >> i) & 1) for i in range(4)]
        return sum(j * signs[a] * signs[b] / 4 for (a, b), j in zip(BONDS, couplings))

    estimates = [mean_and_se(c, value) for c in counts]
    return {
        "energy": sum(e[0] for e in estimates),
        "standard_error": float(np.sqrt(sum(e[1] ** 2 for e in estimates))),
    }


def run(args):
    models = []
    with timed_stage("spinweave", "physical_model_variational_validation") as evidence:
        for delta in [0.0, 0.25, 0.5, 0.75, 1.0]:
            models.append(solve(delta, args.seed))
        evidence.update(
            models=len(models),
            exact_oracle=True,
            magnetization_checked=True,
            max_variational_error=max(m["variational_error"] for m in models),
        )
    rows = []
    with timed_stage("spinweave", "noise_witness_validation") as evidence:
        for model in [models[0], models[2], models[4]]:
            compiled = transpile(
                measurement_circuits(model["circuit"]),
                basis_gates=["rz", "sx", "x", "cx"],
                optimization_level=1,
                seed_transpiler=args.seed,
            )
            for gate in [0.0, 0.005, 0.01, 0.03, 0.1]:
                sim = AerSimulator(
                    method="density_matrix",
                    noise_model=noise_model(gate, 0.02 if gate else 0),
                    max_parallel_threads=2,
                )
                for repeat in range(12):
                    counts = (
                        sim.run(compiled, shots=1024, seed_simulator=args.seed + repeat)
                        .result()
                        .get_counts()
                    )
                    est = measured_energy(model["couplings"], counts)
                    # Sufficient evidence under this sampling model, not a device-independent certificate.
                    certified = (
                        est["energy"] + 1.96 * est["standard_error"]
                        < model["separable_energy_bound"]
                    )
                    rows.append(
                        {
                            "delta": model["delta"],
                            "gate_error": gate,
                            "readout_error": 0.02 if gate else 0,
                            "repeat": repeat,
                            "energy": est["energy"],
                            "standard_error": est["standard_error"],
                            "witness_detected_approx95": bool(certified),
                        }
                    )
        evidence.update(
            estimates=len(rows),
            measurement_groups=3,
            witness="E < -sum(J)/4 detects nonseparability; finite-shot normal approximation",
        )
    args.output.mkdir(parents=True, exist_ok=True)
    with (args.output / "samples.csv").open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)
    curve = [{k: v for k, v in m.items() if k != "circuit"} for m in models]
    report = {
        "evidence": "four_spin_Heisenberg_ring_variational_and_synthetic_noise",
        "hamiltonian": "sum_i J_i (X_i X_j + Y_i Y_j + Z_i Z_j)/4, J=1±delta",
        "qubits": 4,
        "curve": curve,
        "samples": rows,
        "seed": args.seed,
        "separable_bound_proof": "For every product state, each local Bloch vector has norm <=1, so <S_i.S_j> >= -1/4. Positive J implies E >= -sum(J)/4 for all convex mixtures of product states; Neel product states attain this bound on the bipartite ring.",
        "source": "https://arxiv.org/abs/quant-ph/0408086",
        "limitations": "Toy magnetic model, not a prediction for a named material. Witness certifies some entanglement, not necessarily four-partite entanglement. Sampling intervals assume independent counts and do not cover unknown measurement-systematic bias. Parameters optimized on a classical statevector.",
    }
    (args.output / "metrics.json").write_text(json.dumps(report, indent=2) + "\n")
    fig, axes = plt.subplots(1, 2, figsize=(13, 5), constrained_layout=True)
    axes[0].plot(
        [m["delta"] for m in models],
        [m["exact_energy"] for m in models],
        "o-",
        label="Exact ground energy",
        color="#272b35",
    )
    axes[0].scatter(
        [m["delta"] for m in models],
        [m["variational_energy"] for m in models],
        marker="x",
        s=65,
        label="Variational circuit",
        color="#784ec2",
    )
    axes[0].axhline(-1, color="#c94747", ls="--", label="Fully separable bound")
    axes[0].set(
        xlabel="Bond dimerization δ",
        ylabel="Energy (J units)",
        title="Energy below the bound witnesses entanglement",
    )
    axes[0].legend(fontsize=8)
    for delta, color in [(0.0, "#16817a"), (0.5, "#784ec2"), (1.0, "#3874a2")]:
        means = []
        ses = []
        for p in [0.0, 0.005, 0.01, 0.03, 0.1]:
            selected = [
                r["energy"]
                for r in rows
                if r["delta"] == delta and r["gate_error"] == p
            ]
            means.append(np.mean(selected))
            ses.append(np.std(selected, ddof=1) / np.sqrt(len(selected)) * 1.96)
        axes[1].errorbar(
            [0, 0.005, 0.01, 0.03, 0.1],
            means,
            yerr=ses,
            marker="o",
            label=f"δ={delta}",
            color=color,
            capsize=3,
        )
    axes[1].axhline(-1, color="#c94747", ls="--")
    axes[1].set(
        xlabel="Synthetic CX depolarizing probability",
        ylabel="Mean measured energy",
        title="How much noise erases the energy witness?",
    )
    axes[1].legend()
    fig.suptitle(
        "SpinWeave | Four-spin toy magnet · dimerization · noise and entanglement"
    )
    fig.savefig(args.output / "spinweave.png", dpi=160)
    plt.close(fig)
    print(
        json.dumps(
            {
                "max_variational_error": max(m["variational_error"] for m in models),
                "energy_estimates": len(rows),
            }
        )
    )


def hardware_cases():
    report = json.loads((REPO / "results/spinweave/metrics.json").read_text())
    model = next(m for m in report["curve"] if m["delta"] == 0.0)
    cases = []
    for axis, qc in zip("xyz", measurement_circuits(preparation(model["parameters"]))):
        expected = (
            Statevector.from_instruction(qc.remove_final_measurements(inplace=False))
            .probabilities()
            .tolist()
        )
        cases.append(
            (
                qc,
                {
                    "name": f"spinweave_delta0_{axis}",
                    "basis": axis,
                    "expected": expected,
                    "spin_model": {k: v for k, v in model.items() if k != "trials"},
                },
            )
        )
    return cases


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--seed", type=int, default=2026)
    p.add_argument("--output", type=Path, default=REPO / "results/spinweave")
    run(p.parse_args())


if __name__ == "__main__":
    main()

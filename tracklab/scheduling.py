"""GridGuard: conservation-aware QAOA for a tiny carbon-aware batch schedule."""

import argparse
import csv
import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from qiskit import QuantumCircuit, transpile
from qiskit.quantum_info import Statevector
from qiskit_aer import AerSimulator
from scipy.optimize import minimize, differential_evolution

from flybrain.data import REPO
from flybrain.noise import noise_model
from flybrain.progress import timed_stage

ENERGY = np.array([2.0, 1.0, 1.0, 2.0])
RENEWABLE = np.array([1.0, 3.0])
CARBON = np.array([0.55, 0.18])
TASKS = ["batch-A", "batch-B", "batch-C", "batch-D"]
PENALTY = 4.0


def schedule(bits):
    x = np.array([(bits >> i) & 1 for i in range(4)])
    load = np.array([np.sum(ENERGY * (1 - x)), np.sum(ENERGY * x)])
    grid = np.maximum(load - RENEWABLE, 0)
    feasible = bits.bit_count() == 2 and np.max(load) <= 4
    return {
        "bits": format(bits, "04b"),
        "slot_loads": load.tolist(),
        "grid_draw": grid.tolist(),
        "carbon_proxy": float(grid @ CARBON),
        "feasible": bool(feasible),
        "slots": {task: "late" if x[i] else "early" for i, task in enumerate(TASKS)},
    }


def objective(bits):
    late_load = sum(ENERGY[i] for i in range(4) if (bits >> i) & 1)
    # Exact carbon proxy on the feasible sector L_late in {2,3,4}; extension outside
    # that sector is an optimization surrogate and never reported as real emissions.
    surrogate = 3.29 - late_load + 0.09 * late_load**2
    return surrogate + PENALTY * (bits.bit_count() - 2) ** 2


def ising_coefficients(penalized):
    # For f(L)=c+aL+bL², L=sum w_i(1-Z_i)/2.
    z = ENERGY * 0.23
    zz = {
        (i, j): 0.09 * ENERGY[i] * ENERGY[j] / 2
        for i in range(4)
        for j in range(i + 1, 4)
    }
    constant = 1.325
    if penalized:
        constant += PENALTY
        zz = {pair: value + PENALTY / 2 for pair, value in zz.items()}
    return constant, z, zz


def circuit(parameters, mixer="xy", preparation="pair"):
    parameters = np.asarray(parameters)
    if (
        len(parameters) % 2
        or not np.isfinite(parameters).all()
        or mixer not in {"xy", "rx"}
    ):
        raise ValueError("Expected finite gamma/beta pairs and xy/rx mixer")
    depth = len(parameters) // 2
    qc = QuantumCircuit(4)
    if preparation == "dicke":
        qc.prepare_state(
            [1 / np.sqrt(6) if i.bit_count() == 2 else 0 for i in range(16)]
        )
    elif preparation in {"pair", "phase_pair"}:
        qc.x(0)
        qc.x(2)
        # Cheap paired start; its restricted phases are an explicit ablation.
        for a, b in [(0, 1), (2, 3)]:
            qc.rxx(np.pi / 4, a, b)
            qc.ryy(np.pi / 4, a, b)
        if preparation == "phase_pair":
            # Undo the -i exchange phase: identical initial probabilities,
            # different interference, with no extra two-qubit gates.
            qc.rz(np.pi / 2, 1)
            qc.rz(np.pi / 2, 3)
    else:
        raise ValueError("Expected pair, phase_pair or dicke preparation")
    _, z, zz = ising_coefficients(penalized=mixer == "rx")
    for layer in range(depth):
        gamma, beta = parameters[2 * layer : 2 * layer + 2]
        for i in range(4):
            qc.rz(2 * gamma * z[i], i)
        for (i, j), value in zz.items():
            qc.rzz(2 * gamma * value, i, j)
        if mixer == "xy":
            for i, j in [(0, 1), (2, 3), (1, 2), (3, 0)]:
                qc.rxx(beta, i, j)
                qc.ryy(beta, i, j)
        else:
            for i in range(4):
                qc.rx(2 * beta, i)
    return qc


def optimize(mixer, depth, starts, seed):
    costs = np.array([objective(bits) for bits in range(16)])
    rng = np.random.default_rng(seed)
    trials = []
    for start in range(starts):
        x0 = rng.uniform(-np.pi, np.pi, 2 * depth)

        def expectation(params):
            return float(
                Statevector.from_instruction(circuit(params, mixer)).probabilities()
                @ costs
            )

        result = minimize(
            expectation, x0, method="COBYLA", options={"maxiter": 160, "tol": 1e-6}
        )
        trials.append(
            {
                "start": start,
                "parameters": result.x.tolist(),
                "expected_objective": float(result.fun),
                "evaluations": int(result.nfev),
                "converged": bool(result.success),
            }
        )
    return min(trials, key=lambda r: r["expected_objective"]), trials


def distribution_metrics(probabilities):
    schedules = [schedule(bits) for bits in range(16)]
    feasible = np.array([s["feasible"] for s in schedules])
    carbon = np.array([s["carbon_proxy"] for s in schedules])
    optimum = carbon[feasible].min()
    optimal = feasible & np.isclose(carbon, optimum)
    mass = float(np.sum(probabilities[feasible]))
    return {
        "feasible_probability": mass,
        "optimal_probability": float(probabilities[optimal].sum()),
        "conditional_carbon_proxy": float(
            probabilities[feasible] @ carbon[feasible] / mass
        )
        if mass
        else None,
        "optimal_carbon_proxy": float(optimum),
    }


def run(args):
    table = [schedule(bits) for bits in range(16)]
    feasible = [s for s in table if s["feasible"]]
    optimum = min(feasible, key=lambda s: s["carbon_proxy"])
    for bits in range(16):
        c, z, zz = ising_coefficients(True)
        signs = np.array([1 - 2 * ((bits >> i) & 1) for i in range(4)])
        encoded = (
            c
            + z @ signs
            + sum(value * signs[i] * signs[j] for (i, j), value in zz.items())
        )
        if not np.isclose(encoded, objective(bits)):
            raise ValueError("Ising cost does not match enumerated objective")
        if schedule(bits)["feasible"] and not np.isclose(
            objective(bits), schedule(bits)["carbon_proxy"]
        ):
            raise ValueError("Feasible carbon cost mismatch")
    variants = []
    with timed_stage("gridguard", "bounded_architecture_search") as evidence:
        for mixer, depth in [("xy", 1), ("xy", 2), ("rx", 1), ("rx", 2)]:
            best, trials = optimize(mixer, depth, args.starts, args.seed)
            probabilities = Statevector.from_instruction(
                circuit(best["parameters"], mixer)
            ).probabilities()
            summary = {
                "mixer": mixer,
                "preparation": "pair",
                "depth": depth,
                "parameters": best["parameters"],
                "metrics": distribution_metrics(probabilities),
                "probabilities": probabilities.tolist(),
                "trials": trials,
                "evaluations": sum(t["evaluations"] for t in trials),
            }
            if mixer == "xy" and not np.isclose(
                summary["metrics"]["feasible_probability"], 1
            ):
                raise ValueError(
                    "Conservation-aware mixer leaked out of the balanced sector"
                )
            variants.append(summary)
        # A recorded follow-up to the weak paired-start results; this is adaptive
        # architecture exploration on a toy instance, not a held-out benchmark.
        for depth in [1, 2]:
            costs = np.array([objective(bits) for bits in range(16)])
            result = differential_evolution(
                lambda params: float(
                    Statevector.from_instruction(
                        circuit(params, "xy", "dicke")
                    ).probabilities()
                    @ costs
                ),
                [(-6, 6)] * (2 * depth),
                seed=args.seed,
                maxiter=80,
                popsize=8,
            )
            probabilities = Statevector.from_instruction(
                circuit(result.x, "xy", "dicke")
            ).probabilities()
            variants.append(
                {
                    "mixer": "xy",
                    "preparation": "dicke",
                    "depth": depth,
                    "parameters": result.x.tolist(),
                    "metrics": distribution_metrics(probabilities),
                    "probabilities": probabilities.tolist(),
                    "trials": [],
                    "evaluations": int(result.nfev),
                    "search": "differential_evolution, [-6,6], maxiter=80, popsize=8; adaptive follow-up",
                    "converged": bool(result.success),
                }
            )
        evidence.update(
            variants=len(variants),
            exact_oracle=True,
            objective_encoding_checked=True,
            xy_feasibility=1.0,
            quantum_advantage_claim=False,
        )
    best = max(
        (v for v in variants if v["mixer"] == "xy"),
        key=lambda v: v["metrics"]["optimal_probability"],
    )
    measured = circuit(best["parameters"], "xy", best["preparation"])
    measured.measure_all()
    compiled = transpile(
        measured,
        basis_gates=["rz", "sx", "x", "cx"],
        optimization_level=1,
        seed_transpiler=args.seed,
    )
    samples = []
    with timed_stage("gridguard", "finite_shot_noise_validation") as evidence:
        for name, model in [
            ("ideal", noise_model(0, 0)),
            ("synthetic_noise", noise_model(0.005, 0.01)),
        ]:
            simulator = AerSimulator(
                method="density_matrix", noise_model=model, max_parallel_threads=2
            )
            for repeat in range(12):
                counts = (
                    simulator.run(
                        compiled, shots=1024, seed_simulator=args.seed + repeat
                    )
                    .result()
                    .get_counts()
                )
                p = np.zeros(16)
                for bits, count in counts.items():
                    p[int(bits, 2)] = count / 1024
                samples.append(
                    {"case": name, "repeat": repeat, **distribution_metrics(p)}
                )
        evidence.update(runs=len(samples), evidence="results/scheduling/samples.csv")
    args.output.mkdir(parents=True, exist_ok=True)
    with (args.output / "samples.csv").open("w", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(samples[0]))
        writer.writeheader()
        writer.writerows(samples)
    uniform = np.array([1 / len(feasible) if s["feasible"] else 0 for s in table])
    greedy_bits = sum(
        1 << i for i in sorted(range(4), key=lambda i: (-ENERGY[i], i))[:2]
    )
    metrics = {
        "evidence": "synthetic_scheduling_instance_and_local_qaoa",
        "units": "illustrative energy and carbon-proxy units, not measured emissions",
        "tasks": TASKS,
        "energy": ENERGY.tolist(),
        "renewable": RENEWABLE.tolist(),
        "carbon_factors": CARBON.tolist(),
        "capacity_per_slot": 4,
        "required_late_jobs": 2,
        "enumerated_schedules": table,
        "exact_optimum": optimum,
        "greedy_schedule": schedule(greedy_bits),
        "uniform_balanced": distribution_metrics(uniform),
        "variants": variants,
        "selected": {k: v for k, v in best.items() if k != "trials"},
        "circuit": {
            "depth": compiled.depth(),
            "operations": dict(compiled.count_ops()),
        },
        "limitations": "Small synthetic instance; exact enumeration and greedy solve it cheaply. No practical quantum speedup or real carbon-saving claim.",
    }
    (args.output / "metrics.json").write_text(json.dumps(metrics, indent=2) + "\n")
    fig, axes = plt.subplots(1, 2, figsize=(13, 5), constrained_layout=True)
    labels = [
        f"{v['mixer'].upper()} p={v['depth']}\n{v['preparation']}" for v in variants
    ]
    x = np.arange(len(variants))
    axes[0].bar(
        x - 0.18,
        [v["metrics"]["feasible_probability"] for v in variants],
        width=0.36,
        label="Feasible probability",
        color="#16817a",
    )
    axes[0].bar(
        x + 0.18,
        [v["metrics"]["optimal_probability"] for v in variants],
        width=0.36,
        label="Optimal probability",
        color="#784ec2",
    )
    axes[0].set(
        xticks=x,
        xticklabels=labels,
        ylim=(0, 1.08),
        ylabel="Probability",
        title="Preserve the scheduling rule in the circuit",
    )
    axes[0].legend()
    bits = [int(s["bits"], 2) for s in feasible]
    axes[1].bar(
        np.arange(len(bits)), np.array(best["probabilities"])[bits], color="#784ec2"
    )
    axes[1].axhline(
        1 / len(bits), color="#16817a", linestyle="--", label="Uniform balanced"
    )
    axes[1].set(
        xticks=np.arange(len(bits)),
        xticklabels=[s["bits"] for s in feasible],
        xlabel="Schedule bitstring (rightmost = batch-A)",
        ylabel="Probability",
        title=f"Selected XY circuit · optimum {optimum['bits']}",
    )
    axes[1].legend()
    fig.suptitle(
        "GridGuard | Four qubits · carbon-aware toy scheduling · exact and greedy controls",
        fontsize=14,
    )
    fig.savefig(args.output / "gridguard.png", dpi=160)
    plt.close(fig)
    print(
        json.dumps(
            {
                "exact_optimum": optimum,
                "selected": best["metrics"],
                "greedy_matches_exact": bool(
                    np.isclose(
                        schedule(greedy_bits)["carbon_proxy"], optimum["carbon_proxy"]
                    )
                ),
            }
        )
    )


def hardware_cases():
    metrics = json.loads((REPO / "results/scheduling/metrics.json").read_text())
    variants = metrics["variants"]
    selected = [
        next(v for v in variants if v["preparation"] == "dicke" and v["depth"] == 1),
        metrics["selected"],
        next(v for v in variants if v["mixer"] == "rx" and v["depth"] == 1),
    ]
    cases = []
    for variant in selected:
        qc = circuit(variant["parameters"], variant["mixer"], variant["preparation"])
        expected = Statevector.from_instruction(qc).probabilities().tolist()
        qc.measure_all()
        cases.append(
            (
                qc,
                {
                    "name": f"gridguard_{variant['mixer']}_{variant['preparation']}_p{variant['depth']}",
                    "expected": expected,
                    "mixer": variant["mixer"],
                    "preparation": variant["preparation"],
                    "depth_p": variant["depth"],
                },
            )
        )
    return cases, [format(i, "04b") for i in range(16)]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=REPO / "results/scheduling")
    parser.add_argument("--starts", type=int, default=4)
    parser.add_argument("--seed", type=int, default=2026)
    args = parser.parse_args()
    if not 1 <= args.starts <= 12 or args.seed < 0:
        parser.error("Starts must be 1–12 and seed nonnegative")
    run(args)


if __name__ == "__main__":
    main()

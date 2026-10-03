"""KernelForge: bounded architecture search for inexpensive projected quantum features."""

import argparse
import csv
import json
from pathlib import Path
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from qiskit import QuantumCircuit, transpile
from qiskit.quantum_info import Statevector, Pauli
from qiskit_aer import AerSimulator
from sklearn.datasets import load_wine
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.decomposition import PCA
from sklearn.svm import SVC
from sklearn.metrics import accuracy_score
from flybrain.noise import noise_model
from flybrain.data import REPO
from flybrain.progress import timed_stage

ARCHITECTURES = [("product", 1), ("line", 1), ("ring", 1), ("line", 2), ("ring", 2)]


def feature_map(x, topology="line", layers=1):
    if (
        len(x) != 3
        or topology not in {"product", "line", "ring"}
        or layers not in {1, 2}
    ):
        raise ValueError("Expected three features and a bounded architecture")
    qc = QuantumCircuit(3)
    for _ in range(layers):
        for i, value in enumerate(x):
            qc.ry(float(value), i)
            qc.rz(float(value**2 / np.pi), i)
        pairs = [] if topology == "product" else [(0, 1), (1, 2)]
        if topology == "ring":
            pairs.append((2, 0))
        for a, b in pairs:
            qc.cx(a, b)
    return qc


def bloch_features(circuits, gate_error=0):
    operators = []
    for qubit in range(3):
        for axis in "XYZ":
            label = ["I"] * 3
            label[2 - qubit] = axis
            operators.append(Pauli("".join(label)))
    if gate_error == 0:
        return np.array(
            [
                [
                    float(Statevector.from_instruction(q).expectation_value(p).real)
                    for p in operators
                ]
                for q in circuits
            ]
        )
    sim = AerSimulator(
        method="density_matrix",
        noise_model=noise_model(gate_error, 0),
        max_parallel_threads=2,
    )
    compiled = transpile(
        circuits,
        basis_gates=["rz", "sx", "x", "cx"],
        optimization_level=1,
        seed_transpiler=2026,
    )
    for qc in compiled:
        qc.save_density_matrix()
    result = sim.run(compiled, shots=1).result()
    features = []
    for i in range(len(compiled)):
        rho = np.asarray(result.data(i)["density_matrix"])
        features.append([float(np.trace(rho @ p.to_matrix()).real) for p in operators])
    return np.clip(features, -1, 1)


def tune(train, val, ytrain, yval, kernel="rbf"):
    trials = []
    for c in [0.1, 1.0, 10.0]:
        for gamma in [0.1, 1.0, 10.0] if kernel == "rbf" else ["scale"]:
            model = SVC(C=c, gamma=gamma, kernel=kernel).fit(train, ytrain)
            accuracy = accuracy_score(yval, model.predict(val))
            trials.append(
                {"C": c, "gamma": gamma, "validation_accuracy": float(accuracy)}
            )
    best = max(trials, key=lambda t: t["validation_accuracy"])
    return best, trials


def sampled_bloch(features, shots, rng):
    # Each observable measured independently on a fresh preparation: 9*shots paid per datum.
    return 2 * rng.binomial(shots, np.clip((features + 1) / 2, 0, 1)) / shots - 1


def run(args):
    data = load_wine()
    X, y = data.data, data.target
    indices = np.arange(len(y))
    develop, test = train_test_split(
        indices, test_size=0.25, stratify=y, random_state=args.seed
    )
    train, val = train_test_split(
        develop, test_size=0.25, stratify=y[develop], random_state=args.seed + 1
    )
    scale = StandardScaler().fit(X[train])
    full = scale.transform(X)
    pca = PCA(n_components=3).fit(full[train])
    reduced = pca.transform(full)
    # Training-only spread fixes angles; no labels or test rows set the encoding range.
    spread = np.std(reduced[train], axis=0)
    angles = np.clip(reduced / spread, -3, 3) * np.pi / 3
    candidates = []
    feature_cache = {}
    with timed_stage("kernelforge", "train_validation_architecture_search") as evidence:
        for topology, layers in ARCHITECTURES:
            name = f"{topology}_{layers}"
            circuits = [feature_map(x, topology, layers) for x in angles]
            compiled = transpile(
                circuits[0], basis_gates=["rz", "sx", "x", "cx"], optimization_level=1
            )
            for noise in [0.0, 0.02]:
                features = bloch_features(circuits, noise)
                feature_cache[(name, noise)] = features
                best, trials = tune(features[train], features[val], y[train], y[val])
                candidates.append(
                    {
                        "name": name,
                        "topology": topology,
                        "layers": layers,
                        "gate_error": noise,
                        "cx": int(compiled.count_ops().get("cx", 0)),
                        "depth": compiled.depth(),
                        "best": best,
                        "trials": trials,
                    }
                )
        # Freeze a noise-aware candidate before any test scores are computed.
        noisy = [c for c in candidates if c["gate_error"] == 0.02]
        threshold = max(c["best"]["validation_accuracy"] for c in noisy) - 0.03
        selected = min(
            (c for c in noisy if c["best"]["validation_accuracy"] >= threshold),
            key=lambda c: (c["cx"], c["depth"], -c["best"]["validation_accuracy"]),
        )
        evidence.update(
            candidates=len(candidates),
            training_only_preprocessing=True,
            selection="lowest circuit cost within 3 percentage points of best noisy validation accuracy",
            test_set_used_in_selection=False,
            selected=selected["name"],
        )
    rows = []
    predictions = {}
    with timed_stage("kernelforge", "frozen_holdout_evaluation") as evidence:
        # Each baseline gets the same tuning grid and validation partition.
        for name, features, kernel in [
            ("classical_PCA3_linear", reduced, "linear"),
            ("classical_PCA3_RBF", reduced, "rbf"),
            ("classical_full13_RBF", full, "rbf"),
        ]:
            best, _ = tune(features[train], features[val], y[train], y[val], kernel)
            clf = SVC(C=best["C"], gamma=best["gamma"], kernel=kernel).fit(
                features[train], y[train]
            )
            pred = clf.predict(features[test])
            predictions[name] = pred.tolist()
            rows.append(
                {
                    "model": name,
                    "repeat": 0,
                    "test_accuracy": float(accuracy_score(y[test], pred)),
                    "validation_accuracy": best["validation_accuracy"],
                    "shots_per_observable": 0,
                }
            )
        name = selected["name"]
        best = selected["best"]
        for noise, label in [(0.0, "ideal_exact"), (0.02, "synthetic_noise_exact")]:
            features = feature_cache[(name, noise)]
            # Fixed noisy-selected hyperparameters also used on the ideal ablation.
            clf = SVC(C=best["C"], gamma=best["gamma"]).fit(features[train], y[train])
            pred = clf.predict(features[test])
            predictions[label] = pred.tolist()
            rows.append(
                {
                    "model": label,
                    "repeat": 0,
                    "test_accuracy": float(accuracy_score(y[test], pred)),
                    "validation_accuracy": float(
                        accuracy_score(y[val], clf.predict(features[val]))
                    ),
                    "shots_per_observable": 0,
                }
            )
        for shots in [128, 1024]:
            for repeat in range(20):
                sampled = sampled_bloch(
                    feature_cache[(name, 0.02)],
                    shots,
                    np.random.default_rng(args.seed + repeat),
                )
                clf = SVC(C=best["C"], gamma=best["gamma"]).fit(
                    sampled[train], y[train]
                )
                pred = clf.predict(sampled[test])
                rows.append(
                    {
                        "model": "synthetic_noise_finite_shots",
                        "repeat": repeat,
                        "test_accuracy": float(accuracy_score(y[test], pred)),
                        "validation_accuracy": None,
                        "shots_per_observable": shots,
                    }
                )
        evidence.update(
            test_examples=len(test),
            test_scores=len(rows),
            classical_controls=True,
            finite_shots_approximation="independent Pauli binomial samples of exact noisy Bloch expectations",
        )
    args.output.mkdir(parents=True, exist_ok=True)
    with (args.output / "scores.csv").open("w", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    report = {
        "evidence": "local_projected_quantum_features_and_classical_RBF_classifier",
        "dataset": "sklearn bundled Wine: 178 examples, 13 chemical features, 3 cultivars",
        "source": "https://scikit-learn.org/stable/modules/generated/sklearn.datasets.load_wine.html",
        "seed": args.seed,
        "qubits": 3,
        "split": {
            "train": train.tolist(),
            "validation": val.tolist(),
            "test": test.tolist(),
        },
        "pca_explained_variance": pca.explained_variance_ratio_.tolist(),
        "candidates": candidates,
        "selected": selected,
        "scores": rows,
        "test_labels": y[test].tolist(),
        "predictions": predictions,
        "measurement_cost": "9 independent Pauli observables per datum; paid shots = 9 * shots_per_observable * examples. Three grouped measurement settings can measure each qubit concurrently in a future implementation.",
        "limitations": "One fixed dataset split; small test set; established projected-kernel method. Full feature state simulation is classically easy. Sampling is local binomial measurement simulation, not IBM results; no speedup or accuracy advantage assumed.",
    }
    (args.output / "metrics.json").write_text(json.dumps(report, indent=2) + "\n")
    fig, axes = plt.subplots(1, 2, figsize=(13, 5), constrained_layout=True)
    for noise, color in [(0.0, "#16817a"), (0.02, "#784ec2")]:
        subset = [c for c in candidates if c["gate_error"] == noise]
        axes[0].plot(
            [c["cx"] for c in subset],
            [c["best"]["validation_accuracy"] for c in subset],
            "o",
            label=f"gate p={noise}",
            color=color,
        )
        for c in subset:
            axes[0].annotate(
                c["name"],
                (c["cx"], c["best"]["validation_accuracy"]),
                xytext=(4, 5),
                textcoords="offset points",
                fontsize=7,
            )
    axes[0].set(
        xlabel="CX gates per feature preparation",
        ylabel="Validation accuracy",
        title="Architecture choice sees validation data only",
    )
    axes[0].legend()
    groups = [(r["model"], r["shots_per_observable"]) for r in rows[:5]] + [
        ("synthetic_noise_finite_shots", s) for s in [128, 1024]
    ]
    means = []
    errors = []
    for model, shots in groups:
        values = [
            r["test_accuracy"]
            for r in rows
            if r["model"] == model and r["shots_per_observable"] == shots
        ]
        means.append(np.mean(values))
        errors.append(np.std(values, ddof=1) if len(values) > 1 else 0)
    labels = [
        "PCA linear",
        "PCA RBF",
        "Full RBF",
        "Quantum ideal",
        "Quantum noisy",
        "128 shots",
        "1024 shots",
    ]
    axes[1].bar(
        np.arange(7),
        means,
        yerr=errors,
        color=["#72767e"] * 3 + ["#16817a", "#784ec2", "#784ec2", "#784ec2"],
        capsize=3,
    )
    axes[1].set(
        xticks=np.arange(7),
        xticklabels=labels,
        ylim=(0, 1.08),
        ylabel="Held-out accuracy",
        title="Controls and frozen selected architecture",
    )
    axes[1].tick_params(axis="x", rotation=30)
    fig.suptitle(
        "KernelForge | Three qubits · Wine chemical features · bounded circuit search"
    )
    fig.savefig(args.output / "kernelforge.png", dpi=160)
    plt.close(fig)
    print(json.dumps({"selected": selected["name"], "scores": rows[:5]}))


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--seed", type=int, default=2026)
    p.add_argument("--output", type=Path, default=REPO / "results/kernelforge")
    run(p.parse_args())


if __name__ == "__main__":
    main()

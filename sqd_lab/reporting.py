"""Summarize frozen runs and audit SQD against an equal-dimension control.

Run from the repository root: uv run python -m sqd_lab.reporting
The extra control is labelled post-hoc; it is not an independent replication.
"""

import hashlib, json, math, time
from pathlib import Path
import numpy as np
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from .chemistry import hydrogen_chain
from .classical import greedy_basis
from .sampling import uniform_basis, pair_circuit
from .subspace import selected_energy
from qiskit.quantum_info import Statevector


def main():
    output = Path("artifacts/sqd")
    summary = {}
    inputs = {}
    fig, axes = plt.subplots(1, 2, figsize=(10, 3.9), layout="constrained")
    colors = {
        "postselected_qsci": "#156d76",
        "uniform_dimension_matched": "#c07f35",
        "uniform_sector": "#5f7185",
        "self_consistent_sqd": "#8a5690",
        "hartree_fock": "#a8b2b5",
    }
    names = {
        "postselected_qsci": "QSCI",
        "uniform_dimension_matched": "Random basis · equal QSCI size",
        "uniform_sector": "Uniform · equal shots",
        "self_consistent_sqd": "SQD",
        "hartree_fock": "Hartree–Fock",
    }
    for ax, (label, folder) in zip(
        axes, [("H₂", "h2-matched-20261004"), ("H₄", "h4-matched-20261004")]
    ):
        path = output / folder
        records = json.loads((path / "results.json").read_text())
        manifest = json.loads((path / "manifest.json").read_text())
        config = json.loads((path / "config.json").read_text())
        inputs[folder] = {
            name: hashlib.sha256((path / name).read_bytes()).hexdigest()
            for name in ["results.json", "manifest.json", "config.json"]
        }
        groups = []
        for method in colors:
            budgets = sorted({r["shots"] for r in records if r["method"] == method})
            ys = []
            lo = []
            hi = []
            for shots in budgets:
                rows = [
                    r for r in records if r["method"] == method and r["shots"] == shots
                ]
                errors = np.array([r["error_hartree"] * 1000 for r in rows])
                dims = [r["dimension"] for r in rows]
                groups.append(
                    dict(
                        method=method,
                        shots=shots,
                        n=len(rows),
                        mean_error_mha=float(errors.mean()),
                        min_error_mha=float(errors.min()),
                        max_error_mha=float(errors.max()),
                        mean_dimension=float(np.mean(dims)),
                        dimensions=dims,
                    )
                )
                ys.append(max(0, errors.mean()))
                lo.append(max(0, errors.min()))
                hi.append(max(0, errors.max()))
            ax.plot(budgets, ys, "o-", ms=4, color=colors[method], label=names[method])
            ax.fill_between(budgets, lo, hi, color=colors[method], alpha=0.1)
        # Extra post-hoc classical control matches SQD's final Cartesian dimension.
        molecule = hydrogen_chain(config["atoms"], config["distance_angstrom"])
        controls = []
        for row in [r for r in records if r["method"] == "self_consistent_sqd"]:
            result = selected_energy(
                uniform_basis(
                    molecule.norb,
                    molecule.nelec,
                    row["dimension"],
                    row["seed"] + 400000,
                ),
                molecule.hamiltonian,
                molecule.offset,
            )
            controls.append(
                dict(
                    seed=row["seed"],
                    dimension=result["dimension"],
                    energy=result["energy"],
                    error_mha=1000 * (result["energy"] - molecule.exact_energy),
                    sqd_error_mha=row["error_hartree"] * 1000,
                )
            )
        state = Statevector.from_instruction(
            pair_circuit(molecule.norb, config["theta"])
        )
        probabilities = state.probabilities_dict()
        support = np.array(
            [[b == "1" for b in bits] for bits, p in probabilities.items() if p > 1e-12]
        )
        support_result = selected_energy(support, molecule.hamiltonian, molecule.offset)
        greedy_start = time.perf_counter()
        greedy_rows, greedy_history = greedy_basis(molecule, controls[0]["dimension"])
        greedy_seconds = time.perf_counter() - greedy_start
        greedy_result = selected_energy(
            greedy_rows, molecule.hamiltonian, molecule.offset
        )
        max_budget = max(config["shots"])
        x = max_budget
        y = np.mean([r["error_mha"] for r in controls])
        ax.scatter(
            [x],
            [max(0, y)],
            s=36,
            marker="D",
            color="#ad4558",
            label="Random basis · equal SQD size",
            zorder=3,
        )
        ax.scatter(
            [max_budget],
            [max(0, 1000 * (greedy_result["energy"] - molecule.exact_energy))],
            s=36,
            marker="s",
            color="#273f38",
            label="Greedy classical SCI · equal SQD size",
            zorder=4,
        )
        summary[folder] = dict(
            posthoc_greedy_sci=dict(
                seconds=greedy_seconds,
                **greedy_result,
                error_mha=1000 * (greedy_result["energy"] - molecule.exact_energy),
                history=greedy_history,
            ),
            manifest=manifest,
            groups=groups,
            posthoc_sqd_dimension_control=controls,
            full_sector_dimension=math.comb(molecule.norb, molecule.nelec[0])
            * math.comb(molecule.norb, molecule.nelec[1]),
            noiseless_ansatz_support=dict(
                dimension=support_result["dimension"],
                energy=support_result["energy"],
                error_mha=1000 * (support_result["energy"] - molecule.exact_energy),
            ),
        )
        ax.set_title(
            f"{label}  /  {2 * molecule.norb} qubits", loc="left", weight="bold"
        )
        ax.set_xlabel("Sample budget")
        ax.set_ylabel("Energy above FCI / mHa")
        ax.set_xscale("log", base=2)
        ax.set_yscale("symlog", linthresh=0.01)
        ax.set_ylim(bottom=0)
        ax.grid(axis="y", alpha=0.16)
        ax.spines[["top", "right"]].set_visible(False)
    handles, labels = axes[1].get_legend_handles_labels()
    fig.legend(
        handles, labels, loc="outside lower center", ncol=3, frameon=False, fontsize=8
    )
    fig.savefig(output / "energy-coverage.png", dpi=220)
    plt.close(fig)
    payload = dict(
        cases=summary,
        inputs=inputs,
        classical_source_sha256=hashlib.sha256(
            Path("sqd_lab/classical.py").read_bytes()
        ).hexdigest(),
        reporting_source_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        note="Five seeds; min/max shading is descriptive, not a confidence interval. Nested shot budgets. SQD-size random/greedy controls and noiseless support are post-hoc diagnostics; random selection is not optimized classical SCI.",
    )
    (output / "summary.json").write_text(
        json.dumps(payload, indent=2, allow_nan=False) + "\n"
    )
    for name, case in summary.items():
        controls = case["posthoc_sqd_dimension_control"]
        print(
            name,
            "equal-SQD-size random mean mHa",
            np.mean([r["error_mha"] for r in controls]),
            "paired SQD wins",
            sum(r["sqd_error_mha"] < r["error_mha"] - 1e-8 for r in controls),
            "support",
            case["noiseless_ansatz_support"],
            "greedy",
            case["posthoc_greedy_sci"],
        )


if __name__ == "__main__":
    main()

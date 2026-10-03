"""SpinTherm: thermal crossover and cut-dependent entanglement in a four-spin toy magnet."""

import json
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from scipy.linalg import expm
from scipy.optimize import brentq
from flybrain.data import REPO
from flybrain.progress import timed_stage
from .spinweave import hamiltonian


def gibbs(matrix, temperature):
    if not np.isfinite(temperature) or temperature < 0:
        raise ValueError("Nonnegative finite temperature required")
    energies, vectors = np.linalg.eigh(matrix)
    if temperature == 0:
        ground = np.isclose(energies, energies.min(), atol=1e-10)
        weights = ground / ground.sum()
    else:
        weights = np.exp(-(energies - energies.min()) / temperature)
        weights /= weights.sum()
    rho = (vectors * weights) @ vectors.conj().T
    if not np.isclose(np.trace(rho), 1) or np.linalg.eigvalsh(rho).min() < -1e-12:
        raise ValueError("Invalid Gibbs state")
    return rho


def negativity(rho, qubits):
    # Tensor axis order is q3,q2,q1,q0 for rows, followed by columns.
    tensor = rho.reshape([2] * 8)
    axes = list(range(8))
    for qubit in qubits:
        if qubit not in range(4):
            raise ValueError("Qubit index out of range")
        row = 3 - qubit
        axes[row], axes[row + 4] = axes[row + 4], axes[row]
    partial = tensor.transpose(axes).reshape(16, 16)
    values = np.linalg.eigvalsh(partial)
    return float(-np.sum(values[values < 0]))


def main():
    rows = []
    crossovers = []
    with timed_stage("spintherm", "gibbs_state_and_entanglement_controls") as evidence:
        for delta in [0.0, 0.5, 1.0]:
            operator, couplings = hamiltonian(delta)
            matrix = operator.to_matrix()
            bound = -sum(couplings) / 4
            crossing = brentq(
                lambda t: float(np.trace(gibbs(matrix, t) @ matrix).real) - bound,
                0.01,
                10.0,
            )
            crossovers.append(
                {
                    "delta": delta,
                    "energy_witness_crossover_temperature": float(crossing),
                }
            )
            for temperature in np.linspace(0, 4, 81):
                rho = gibbs(matrix, temperature)
                if temperature == 1.0:
                    independent = expm(-matrix)
                    independent /= np.trace(independent)
                    np.testing.assert_allclose(rho, independent, atol=1e-12)
                energy = float(np.trace(rho @ matrix).real)
                rows.append(
                    {
                        "delta": delta,
                        "temperature": float(temperature),
                        "energy": energy,
                        "separable_bound": bound,
                        "energy_witness": bool(energy < bound - 1e-10),
                        "negativity_one_vs_three": negativity(rho, [0]),
                        "negativity_pair_vs_pair": negativity(rho, [0, 1]),
                        "purity": float(np.trace(rho @ rho).real),
                    }
                )
        dimer = next(c for c in crossovers if c["delta"] == 1.0)
        np.testing.assert_allclose(
            dimer["energy_witness_crossover_temperature"], 2 / np.log(3), atol=1e-10
        )
        if max(r["negativity_pair_vs_pair"] for r in rows if r["delta"] == 1.0) > 1e-10:
            raise ValueError("Independent thermal dimers entangled across the pair cut")
        evidence.update(
            states=len(rows),
            analytic_dimer_threshold=True,
            independent_expm=True,
            cut_dependent_entanglement=True,
            hardware_preparation=False,
        )
    out = REPO / "results/spintherm"
    out.mkdir(parents=True, exist_ok=True)
    report = {
        "evidence": "EXACT_CLASSICAL_GIBBS_STATE_ANALYSIS_NOT_HARDWARE",
        "rows": rows,
        "crossovers": crossovers,
        "temperature_units": "k_B T / J, dimensionless; not kelvin for a named material",
        "analytic_dimer_limit": "At delta=1, two independent J=2 dimers lose their pair entanglement at T=2/ln(3). The cut between the independent dimers is separable at every temperature.",
        "limitations": "Four-spin finite-size thermal crossover, not a thermodynamic phase transition. Positive negativity certifies entanglement across the specified cut; zero negativity does not generally prove separability. An energy above the witness bound does not prove absence of entanglement. Gibbs states are computed classically, not prepared on IBM.",
    }
    (out / "metrics.json").write_text(json.dumps(report, indent=2) + "\n")
    fig, axes = plt.subplots(1, 2, figsize=(13, 5), constrained_layout=True)
    for delta, color in [(0.0, "#16817a"), (0.5, "#784ec2"), (1.0, "#3874a2")]:
        group = [r for r in rows if r["delta"] == delta]
        axes[0].plot(
            [r["temperature"] for r in group],
            [r["energy"] for r in group],
            color=color,
            label=f"δ={delta}",
        )
        axes[1].plot(
            [r["temperature"] for r in group],
            [r["negativity_one_vs_three"] for r in group],
            color=color,
            label=f"δ={delta}, one | three",
        )
        axes[1].plot(
            [r["temperature"] for r in group],
            [r["negativity_pair_vs_pair"] for r in group],
            color=color,
            ls="--",
            label=f"δ={delta}, pair | pair",
        )
    axes[0].axhline(-1, color="#c94747", ls="--", label="Fully separable energy bound")
    axes[0].set(
        xlabel="Dimensionless temperature kBT/J",
        ylabel="Thermal energy (J units)",
        title="Heat can erase the energy witness",
    )
    axes[0].legend(fontsize=8)
    axes[1].set(
        xlabel="Dimensionless temperature kBT/J",
        ylabel="Negativity",
        title="Where entanglement sits matters",
    )
    axes[1].legend(fontsize=7)
    fig.suptitle(
        "SpinTherm | Exact four-spin Gibbs states · thermal crossover, not a phase transition"
    )
    fig.savefig(out / "spintherm.png", dpi=160)
    plt.close(fig)
    print(json.dumps({"states": len(rows), "crossovers": crossovers}))


if __name__ == "__main__":
    main()

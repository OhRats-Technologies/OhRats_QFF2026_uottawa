"""Reproducible sample -> filter/recover -> diagonalize -> benchmark pipeline."""

import datetime, hashlib, json, time, platform, importlib.metadata
from pathlib import Path
import numpy as np
from qiskit import qasm3
from qiskit.primitives.containers import BitArray
from qiskit_addon_sqd.fermion import diagonalize_fermionic_hamiltonian
from .chemistry import hydrogen_chain
from .sampling import (
    pair_circuit,
    sample_circuit,
    valid_mask,
    uniform_sector,
    uniform_basis,
)
from .subspace import selected_energy


def run(config, output):
    output = Path(output)
    if output.exists():
        raise ValueError("Use a fresh output directory to preserve previous runs")
    output.mkdir(parents=True)
    started = time.perf_counter()
    molecule = hydrogen_chain(config["atoms"], config["distance_angstrom"])
    circuit = pair_circuit(molecule.norb, config["theta"])
    (output / "circuit.qasm").write_text(qasm3.dumps(circuit))
    (output / "config.json").write_text(json.dumps(config, indent=2) + "\n")
    np.savez_compressed(
        output / "integrals.npz",
        hcore=molecule.hcore,
        eri=molecule.eri,
        offset=molecule.offset,
    )
    records = []
    solver_history = []
    for seed in config["seeds"]:
        for budget in config["shots"]:
            # One maximal draw; nested shot budgets share the same seed deliberately.
            raw = sample_circuit(
                circuit, max(config["shots"]), seed, config["readout_error"]
            )[:budget]
            filtered = raw[valid_mask(raw, molecule.nelec)]
            uniform = uniform_sector(
                molecule.norb, molecule.nelec, budget, seed + 200000
            )
            hf = np.array(
                [
                    [
                        q == "1"
                        for q in format(
                            sum(1 << i for i in range(molecule.nelec[0]))
                            + sum(
                                1 << (i + molecule.norb)
                                for i in range(molecule.nelec[1])
                            ),
                            f"0{2 * molecule.norb}b",
                        )
                    ]
                ]
            )
            matched = uniform_basis(
                molecule.norb,
                molecule.nelec,
                len(np.unique(filtered, axis=0)),
                seed + 300000 + budget,
            )
            for kind, rows in [
                ("postselected_qsci", filtered),
                ("uniform_sector", uniform),
                ("uniform_dimension_matched", matched),
                ("hartree_fock", hf),
            ]:
                result = selected_energy(rows, molecule.hamiltonian, molecule.offset)
                if (
                    result["energy"] is not None
                    and result["energy"] < molecule.exact_energy - 1e-8
                ):
                    raise AssertionError("Energy violates the variational reference")
                records.append(
                    dict(
                        seed=seed,
                        shots=budget,
                        method=kind,
                        accepted_shots=len(filtered)
                        if kind == "postselected_qsci"
                        else len(rows),
                        **result,
                        error_hartree=None
                        if result["energy"] is None
                        else result["energy"] - molecule.exact_energy,
                    )
                )
            counts = {}
            for row in raw:
                string = "".join("1" if b else "0" for b in row)
                counts[string] = counts.get(string, 0) + 1
            np.savez_compressed(
                output / f"samples-{seed}-{budget}.npz",
                raw=raw,
                filtered=filtered,
                uniform=uniform,
            )
            if budget == max(config["shots"]):
                history = []

                def callback(batches):
                    history.append(
                        [
                            dict(
                                energy=float(r.energy + molecule.offset),
                                dimension=int(np.prod(r.sci_state.amplitudes.shape)),
                            )
                            for r in batches
                        ]
                    )

                recovered = diagonalize_fermionic_hamiltonian(
                    molecule.hcore,
                    molecule.eri,
                    BitArray.from_counts(counts),
                    samples_per_batch=config["samples_per_batch"],
                    norb=molecule.norb,
                    nelec=molecule.nelec,
                    max_iterations=config["recovery_iterations"],
                    symmetrize_spin=True,
                    callback=callback,
                    seed=seed,
                    max_dim=config["max_spin_strings"],
                )
                energy = float(recovered.energy + molecule.offset)
                if energy < molecule.exact_energy - 1e-8:
                    raise AssertionError("Recovery violates variational bound")
                records.append(
                    dict(
                        seed=seed,
                        shots=budget,
                        method="self_consistent_sqd",
                        energy=energy,
                        dimension=int(np.prod(recovered.sci_state.amplitudes.shape)),
                        error_hartree=energy - molecule.exact_energy,
                        accepted_shots=len(filtered),
                    )
                )
                solver_history.append(dict(seed=seed, iterations=history))
    sources = list(Path("sqd_lab").glob("*.py"))
    snapshot = output / "source_snapshot"
    snapshot.mkdir()
    for source in sources:
        (snapshot / source.name).write_bytes(source.read_bytes())
    manifest = dict(
        created_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),
        backend="Qiskit Statevector; simulated independent bit-flip readout",
        hardware_used=False,
        exact_fci_energy=molecule.exact_energy,
        hf_energy=molecule.hf_energy,
        norb=molecule.norb,
        nelec=molecule.nelec,
        energy_unit="hartree; nuclear repulsion included",
        distance_unit="angstrom",
        seconds=time.perf_counter() - started,
        versions={
            name: importlib.metadata.version(name)
            for name in (
                "qiskit",
                "qiskit-addon-sqd",
                "qiskit-nature",
                "pyscf",
                "numpy",
            )
        },
        sources={str(p): hashlib.sha256(p.read_bytes()).hexdigest() for p in sources},
        config_sha256=hashlib.sha256((output / "config.json").read_bytes()).hexdigest(),
        comparison_note="Uniform sector uses equal shots; uniform_dimension_matched uses equal unique dimension and direct classical selection, not QPU shots. Recovery uses capped Cartesian spin-sector expansion.",
        seed_note="Independent seeds within each budget; nested budgets share a maximal draw and may not be pooled as independent observations.",
    )
    for name, value in [
        ("results", records),
        ("recovery_history", solver_history),
        ("manifest", manifest),
    ]:
        (output / f"{name}.json").write_text(
            json.dumps(value, indent=2, allow_nan=False) + "\n"
        )
    (output / "completion.json").write_text(
        json.dumps(
            dict(
                comparisons=len(records),
                finished_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),
            ),
            indent=2,
        )
        + "\n"
    )
    return manifest, records

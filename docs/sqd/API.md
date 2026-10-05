# Working with the library

Run Python from the repository root after `uv sync --locked`. The supported teaching systems are H2 and H4 in STO-3G. The library is intentionally small and local.

| Function | Input | Output |
|---|---|---|
| `hydrogen_chain(atoms, distance)` | 2 or 4 atoms; spacing in angstrom | Integrals, electronic qubit Hamiltonian, energy offset, HF/FCI references |
| `pair_circuit(norb, theta)` | 2 or 4 spatial orbitals; fixed rotation angle | Unmeasured Qiskit preparation circuit |
| `sample_circuit(circuit, shots, seed, readout_error)` | Positive shots; synthetic bit-flip probability in [0, 0.5) | Boolean sample rows, most-significant bit first |
| `valid_mask(rows, nelec)` | Rows and `(N_alpha, N_beta)` | Mask of rows with both correct particle numbers |
| `selected_energy(rows, hamiltonian, offset)` | Observed or selected occupation rows | Lowest energy, distinct dimension, sorted integer basis indices |
| `greedy_basis(molecule, dimension)` | Target physical-sector dimension | Classical selected rows and nested energy history |
| `pipeline.run(config, output)` | JSON-compatible experiment config; fresh directory | Manifest and comparison records; saves all reproducibility files |

Validate the published evidence without rerunning it: `uv run python -m sqd_lab.audit`. It checks source/config hashes, shot accounting, filtering, and variational energy/error accounting.

The example notebook shows these calls in context. `python -m sqd_lab --help` exposes the command-line entry point.

## Conventions that affect correctness

**Bitstrings.** For H2, the HF occupation is `0101`, integer 5. It has alpha occupation on low-index Qiskit wires and beta occupation on high-index wires. Do not reverse strings when converting them to integer indices. `nelec` is `(alpha, beta)` even though printed beta bits appear first.

**Energy.** `molecule.hamiltonian` contains the electronic operator. Add `molecule.offset` exactly once. The official fermionic SQD return value also requires that offset for comparison with total HF/FCI energies. A millihartree is 0.001 hartree.

**Counts and amplitudes.** Repeated bitstrings contribute sampling frequency but only one basis vector. Diagonalization determines wavefunction amplitudes within the selected basis; it does not reconstruct the original sampled state or its phases.

**Filtering and recovery.** Correct particle number does not imply that a sample is error-free. SQD may recover invalid configurations and form a Cartesian product of alpha/beta strings, so final basis size may exceed observed unique determinants. Matching shot counts alone does not match diagonalization cost.

**Variational bounds.** Compare energies for the same Hamiltonian, geometry, basis, particle sector and energy offset. Empty postselection returns `energy=None`, not an invented zero. The dense matrix cross-check is for tiny examples and should not be copied into a large-molecule workflow.

**Classical controls.** Uniform random selection is a weak baseline. The greedy residual selector is stronger but explicitly enumerates our tiny sector. The report shows why neither correctness on H2 nor a win over random H4 bases establishes quantum advantage.

## Official interfaces

- [Fermionic SQD](https://qiskit.github.io/qiskit-addon-sqd/apidocs/qiskit_addon_sqd.fermion.html): use `BitArray.from_counts(counts)` with the self-consistent solver. Its `max_dim` caps a spin-string set, not the final Cartesian determinant count.
- [Qubit projection](https://qiskit.github.io/qiskit-addon-sqd/apidocs/qiskit_addon_sqd.qubit.html): the adapter validates bit order, duplicates, complex orientation and Hermiticity against Qiskit.
- [Configuration recovery](https://qiskit.github.io/qiskit-addon-sqd/apidocs/qiskit_addon_sqd.configuration_recovery.html): occupation-guided recovery is a modeling step, not a guarantee that true missing configurations are found.

## Future hardware boundary

An authorized hardware experiment would replace local sampling with measured counts from the same prepared circuit. Keep submission, collection and postprocessing separate. Counts must include the original register convention, shot budget, circuit identity and measurement provenance; do not label synthetic bit flips as real device noise. Importing this library or opening the notebook creates no Runtime service and submits no jobs.

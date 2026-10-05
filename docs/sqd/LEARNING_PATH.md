# Qiskit to SQD: a practical learning path

Run from the repository root with Python 3.12 and `uv sync --locked`. The notebook and CLI are entirely local. They do not load `.env` or submit jobs.

| Step | Learn | Do | Primary reference |
|---|---|---|---|
| 1 | Circuits, measurement registers and bit order | Prepare a Bell circuit; compare counts with probabilities | [Qiskit primitives](https://quantum.cloud.ibm.com/docs/en/guides/simulate-with-qiskit-sdk-primitives) |
| 2 | Chemistry to qubits | Build H2 integrals, Jordan-Wigner Hamiltonian and Hartree-Fock reference | [Qiskit Nature](https://github.com/qiskit-community/qiskit-nature) |
| 3 | QSCI / selected subspaces | Deduplicate measured strings and diagonalize the projected operator | [QSCI paper](https://arxiv.org/abs/2302.11320) |
| 4 | Noise and symmetry | Compare raw samples with valid alpha/beta electron-number samples | [SQD overview](https://quantum.cloud.ibm.com/docs/en/guides/qiskit-addons-sqd) |
| 5 | Self-consistent SQD | Run the official fermionic solver and inspect occupancy/recovery iterations | [Official quickstart](https://qiskit.github.io/qiskit-addon-sqd/guides/quickstart.html) |
| 6 | Honest benchmarking | Compare HF, exact FCI, equal-shot uniform samples and equal-dimension random/greedy SCI bases | [QSCI limitations](https://arxiv.org/abs/2501.07231) |

Open `notebooks/sqd_h2.ipynb` for the short worked example. Run H4 with `uv run python -m sqd_lab --config configs/sqd/h4.json --output results/sqd/h4-demo`. H2 teaches the machinery; stretched H4 exposes insufficient ansatz support.

## Outputs and conventions

- `circuit.qasm`: fixed preparation circuit, independent of the exact solution.
- `integrals.npz`: molecular integrals and nuclear offset.
- `samples-*.npz`: raw, symmetry-filtered and classical-uniform samples.
- `results.json`: energies, unique dimensions, accepted shots and errors.
- `recovery_history.json`: every SQD iteration and subspace dimension.
- `config.json`, `manifest.json`, `source_snapshot/`: parameters, versions and provenance.

Counts strings are most-significant bit first. Alpha orbitals occupy Qiskit wires `0..norb-1`, beta `norb..2*norb-1`; printed strings place beta on the left. Both halves must have their specified electron number. Total energies include nuclear repulsion and use hartree; distances use angstrom.

## Festival demonstration checklist

These are suggested demonstration goals, not a published judging rubric:

1. Explain which step uses a quantum circuit and which runs classically.
2. Show the saved circuit and actual simulated shot counts.
3. Explain the variational upper bound and exact/HF references.
4. Show energy versus unique determinant count, not shots alone.
5. Explain why postselection discards data and recovery adds configurations.
6. Show where the circuit misses important configurations and loses to greedy classical SCI.
7. State that this example establishes neither novelty nor advantage.

Hardware would replace the sampling stage with separately authorized measured counts. Keep collection and submission separate; viewing the learning resources must not trigger jobs.

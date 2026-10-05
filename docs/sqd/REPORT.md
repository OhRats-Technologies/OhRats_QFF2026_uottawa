# Samples into Chemistry

**A verified Qiskit SQD / QSCI learning pipeline**

OhRats Technologies · Qiskit Fall Fest 2026 · 4 October 2026

## The contribution

This project turns molecular circuit samples into a classically diagonalized Hamiltonian, with explicit physical constraints, independently checked energies and reproducible controls. Its deliverables are a small Python library, an executed H₂ notebook, H₂/H₄ benchmarks and a source-linked learning path. The scientific contribution is a transparent demonstration of configuration selection and recovery; this is not a new algorithm or a quantum-advantage result.

Our main finding is practical. H₂ is useful for checking correctness but too small to establish a sampling advantage. H₄ exposes limited circuit support: bounded SQD improves the selected energy, yet classical uniform sampling wins when allowed to cover the entire small sector, and a greedy classical selector is far more accurate at the same 16-determinant budget. The relevant resource is the number and quality of **distinct determinants**, not just the number of shots.

## What QSCI and SQD do

QSCI prepares an approximate electronic state, measures its occupation bitstrings and classically diagonalizes the Hamiltonian in a selected determinant basis. Its estimated energy remains variational when samples define a legitimate subspace, even if sampling is imperfect. [Kanno et al., QSCI](https://arxiv.org/abs/2302.11320).

SQD belongs to this sample-selected diagonalization family. Here “QSCI” labels our simple postselected observed basis; “SQD” labels the official add-on's occupation-guided, self-consistent configuration-recovery workflow. They are related methods, not unrelated competitors. The larger SQD chemistry study combines quantum sampling with substantial classical computation; its scale and hardware results cannot be inferred from our simulated tiny molecules. [Robledo-Moreno et al., quantum-centric chemistry](https://arxiv.org/abs/2405.05068).

The implementation uses the maintained [Qiskit SQD add-on](https://github.com/Qiskit/qiskit-addon-sqd), rather than reimplementing its recovery solver. The [official quickstart](https://qiskit.github.io/qiskit-addon-sqd/guides/quickstart.html) is particularly useful: its classical uniform-sampling example eventually recovers a full subspace. Correct energy alone therefore does not identify useful quantum sampling.

### The small mathematical core

Let S contain M distinct occupation configurations, and let P have their computational-basis vectors as columns. The projected Hamiltonian is `H_S = P† H P`; the selected energy is the smallest eigenvalue of `H_S`, plus the constant energy offset. P has orthonormal columns, so minimizing over its span cannot produce an energy below the exact ground state of the same physical sector.

Measured frequencies help choose configurations; they are **not** the final eigenvector amplitudes. Diagonalization solves for the amplitudes. Duplicate measurements consume shots without increasing M. For truly nested subspaces, the selected ground energy cannot increase as the subspace expands. Iterative recovery may replace a basis, however, so energies from successive recovery iterations are not guaranteed to be monotone.

For n spatial orbitals and fixed spin populations `(N_alpha, N_beta)`, the physical sector contains `choose(n, N_alpha) × choose(n, N_beta)` determinants. Its size is four for our H₂ case and 36 for H₄. Our independent dense projection check is deliberately limited to these small examples; constructing the full qubit matrix scales exponentially.

## Experiment and controls

We use straight hydrogen chains in STO-3G: H₂ at 0.735 Å, H₄ at 1.5 Å neighboring separation. PySCF generates molecular integrals, Hartree–Fock (HF) and an independent full configuration-interaction (FCI) reference. Qiskit Nature applies the Jordan–Wigner mapping. Every reported total energy includes nuclear repulsion; geometry is in angstrom and energy error in millihartree (mHa).

A fixed particle-number-conserving pair circuit uses angle 0.2. It is not optimized against FCI, trained with exact-state amplitudes or presented as a realistic correlated ground-state ansatz. Ideal H₂ support contains two determinants; ideal H₄ support contains four. We simulate samples locally and add independent per-bit readout flips at probability 0.08. This is an explicit synthetic corruption model, not an IBM noise calibration or hardware result.

H₂ budgets are 8/32/128 shots; H₄ budgets are 16/64/256. Each case uses five fixed seeds. Budgets are nested prefixes of the same maximal draw within a seed and must not be pooled as independent repetitions. Results are descriptive; these seeds were also used during pilot development and do not constitute an independent confirmatory study.

The official fermionic SQD solver uses 32 samples per batch, up to four recovery iterations and spin symmetrization. The spin-string cap is two for H₂ and four for H₄. Its Cartesian alpha/beta basis therefore has at most four or 16 determinants respectively. Reported SQD energies are the returned final solution, rather than a cherry-picked minimum from the iteration history. [Fermionic SQD API](https://qiskit.github.io/qiskit-addon-sqd/apidocs/qiskit_addon_sqd.fermion.html).

We compare HF, postselected QSCI, uniform classical sampling at equal shots, and uniform random selection without replacement at the same unique dimension as QSCI. Two separately labelled **post-hoc** controls match the final SQD dimension: random selection and a greedy classical selected-CI heuristic. The greedy method starts from HF and repeatedly adds the external determinant with largest squared residual coupling `|H_external,selected c|²`, recomputing the current ground eigenvector after each addition. It never uses FCI amplitudes or the reference energy. Candidate scoring enumerates the entire tiny physical sector; this is an educational baseline, not a production or scalable selected-CI implementation.

## Measured results

The table uses the largest shot budget and mean energy error over five seeds for stochastic methods; the greedy selector is deterministic. “Basis” is mean unique determinant count; it is not a qubit count. Values indistinguishable from zero at numerical precision are shown as zero.

| Method | H₂ error / mHa | H₂ basis | H₄ error / mHa | H₄ basis |
|---|---|---|---|---|
| Hartree–Fock | 20.307 | 1 | 167.013 | 1 |
| Postselected QSCI | 0 | 3.2 | 127.542 | 9.4 |
| Random basis, equal QSCI size | 4.061 | 3.2 | 272.098 | 9.4 |
| Self-consistent SQD | 0 | 4 | 66.549 | 16 |
| Random basis, equal SQD size | 0 | 4 | 203.227 | 16 |
| Greedy classical SCI, equal SQD size | 0 | 4 | 0.019 | 16 |
| Uniform sampling, equal shots | 0 | 4 | 0 | 36 |

![Energy error and determinant coverage. Lines show seed means; shaded ranges are seed minima/maxima, not confidence intervals. The diamond and square are post-hoc random and greedy classical controls at the SQD basis size. SQD is evaluated only at the largest budget. Classical basis-control markers align with that benchmark; they consume no quantum shots. The vertical scale is logarithmic above 0.01 mHa and linear near zero.](../../artifacts/sqd/energy-coverage.png)

FCI total energies are -1.137306035753 Ha for H₂ and -1.996150325519 Ha for H₄. H₂ QSCI is exact in all five largest-budget runs; exact agreement also follows from its two-determinant noiseless support. For H₄, the noiseless four-determinant support alone has 132.408 mHa error. This isolates an important limitation: more noiseless shots cannot create missing determinants.

H₄ SQD lowers error relative to the observed QSCI basis, but also expands its dimension from about nine to 16. Recovery and increased capacity are both involved. Against the same-size random basis, SQD has lower error in four of five paired seeds. That small descriptive win count does not establish statistical significance, robustness to other circuits or superiority to classical SCI. In fact, the greedy residual-selected control reaches **0.01913 mHa** error at the same 16-determinant budget, compared with SQD’s 66.5493 mHa mean. The present circuit/recovery combination is substantially worse on this geometry. Its apparent advantage over random selection does not survive a stronger classical comparison.

The equal-shot uniform control reaches all 36 determinants and is exact. It has a larger classical diagonalization budget, so it is not a size-matched algorithm comparison. Nevertheless, it decisively prevents claiming that quantum sampling is necessary for this tiny demonstration. The remaining 66.549 mHa SQD error is substantial; the present H₄ setup is an educational recovery example, not a high-accuracy chemistry result.

The fixed H₂ pipeline took 0.871 seconds and H₄ 7.956 seconds on this workstation. These recorded intervals include integral generation, sampling, comparisons, recovery and output creation, but exclude Python/module import startup. They are local timings, unrelated to IBM queue or execution time.

## Verification and reproducibility

Six focused SQD tests check spin-number conservation, deterministic sampling, empty inputs, complex projection orientation agreement between the full H₂ sector and independent FCI/HF references, and the classical selector’s physical, nested variational sequence. The complex-matrix check caught a convention mismatch; the adapter now transposes the add-on projection into the conventional matrix orientation and uses 64-bit JAX precision. Every selected Hamiltonian is also compared directly with its corresponding dense Qiskit matrix restriction, and every returned energy is checked against the variational bound.

All 96 retained repository tests pass after cleanup, the new notebook executes from top to bottom, and the existing FlyWalk smoke run passes. Frozen run directories contain configurations, integral arrays, circuit QASM, sampled bitstrings, recovery histories, package versions, source snapshots and source/configuration hashes. `artifacts/sqd/summary.json` records the derived tables and post-hoc controls, including the greedy selection history.

To reproduce H₂ from the repository root, use `uv run python -m sqd_lab --config configs/sqd/h2.json --output results/sqd/my-h2-run`. Substitute `h4.json` for H₄. Output directories must be fresh. Run `uv run python -m sqd_lab.reporting` to regenerate the published summary and figure from the frozen benchmark inputs. The reference Qiskit primitives are local simulators. [IBM reference-primitives guide](https://quantum.cloud.ibm.com/docs/en/guides/simulate-with-qiskit-sdk-primitives).

## A useful festival project

The strongest current demonstration is **how a quantum-sampled candidate basis becomes a physically constrained, variational chemical calculation**. Show the circuit, distinguish shots from determinants, reject invalid electron counts, inspect recovery iterations, and compare basis-size-matched energies. Use H₂ as the correctness demonstration and H₄ as the limitation that motivates better state preparation.

A substantive next experiment would replace the restricted circuit with a richer number-conserving preparation, then compare it against production classical selected-CI at fixed determinant dimension and measured classical time across bond distances and fresh seeds. The current post-hoc greedy control is already enough to reject an improvement claim for this setup. Repeated determinant sampling and classical compactness are known concerns, not newly discovered limitations. [Reinholdt et al., critical limitations of QSCI](https://arxiv.org/abs/2501.07231).

The learning path and proposed demonstration checklist are our recommendations, not an organizer-published grading rubric. Hardware sampling is a separate future stage requiring an explicit submission budget; this resource suite reads no credentials and submits no jobs.

## Repository organization and cleanup

The active library separates chemistry, sampling, projection, pipeline orchestration and reporting. Configuration files specify experiments, notebooks teach the workflow, tests verify physical/numerical properties and compact artifacts retain measured evidence. This follows the practical package/docs/tests and topic-notebook patterns inspected in the official [SQD](https://github.com/Qiskit/qiskit-addon-sqd), [Nature](https://github.com/qiskit-community/qiskit-nature) and [community tutorial](https://github.com/qiskit-community/qiskit-community-tutorials) repositories; historical Aqua/Ignis APIs are not copied.

Cleanup actually deleted 579 tracked abandoned or redundant files, approximately 13 MB, including the retired Q-SIGReg implementation, vendored LeJEPA, unused festival prototypes and superseded world-model pilots. No archive folder was created. That cleanup retained completed reports, validated world-model work, existing notebooks and hardware records. The unused Qiskit machine-learning dependency was removed. The subsequent owner-directed wildfire pivot is recorded in [the current cleanup inventory](../CLEANUP.json); the challenge goal is now [Ontario wildfires](../../GOAL.md).

The deletion inventory records the prior source commit. Historical reports retain their original conclusions; reproduction links into deleted experiments require that older Git revision. This makes the current tree focused without rewriting the project's negative findings.

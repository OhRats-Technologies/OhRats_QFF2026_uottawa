# Qiskit library, shot sensitivity and SQD follow-up

The API/SQD/replay studies below belong to the incident-classification branch. Macro annual selection and prediction remain unrun. [Scope correction](SCOPE_CORRECTION.md).

**The library reproduces our fidelity calculation. Finite-shot errors and PSD repair materially change the classifier. SQD contributes no extra optimization to this diagonal feature-selection objective.** This owner-requested pilot follows the completed final opening and uses training-period data only. It does not replace the frozen final comparison.

## FidelityQuantumKernel

Earlier experiments used cached Qiskit statevectors and squared overlaps. This pilot directly uses [FidelityQuantumKernel](https://qiskit-community.github.io/qiskit-machine-learning/stubs/qiskit_machine_learning.kernels.FidelityQuantumKernel.html), [ComputeUncompute](https://qiskit-community.github.io/qiskit-machine-learning/stubs/qiskit_machine_learning.state_fidelities.ComputeUncompute.html) and [QMLSampler](https://qiskit-community.github.io/qiskit-machine-learning/stubs/qiskit_machine_learning.primitives.QMLSampler.html). Exact mode uses no shots; 512/4096-shot modes simulate sampling locally. Raw matrices disable automatic PSD repair so we can compare eigenvalue clipping on the **same measurements**. Cross-kernel estimates remain noisy after training-matrix repair.

Frozen inputs: geography/season/water, robust+tanh preprocessing, four-qubit depth-two ZZ map, angle scale 0.05, C=1. Train 1988–2014; validate 2015–2018. Each seed uses the same **48 training / 96 validation fires** for all predictors. Seeds 593/601/607 have only 3/1/1 training positives and 6/11/14 validation positives. This is a small implementability diagnostic, not a reliable model ranking.

| Predictor | Mean validation AP |
| --- | ---: |
| Logistic | 0.3702 |
| RBF | 0.3052 |
| Cached exact statevectors | 0.2851 |
| FidelityQuantumKernel, exact | 0.2851 |
| 512 shots, raw / PSD repaired | 0.2345 / 0.3124 |
| 4096 shots, raw / PSD repaired | 0.2456 / 0.3077 |

Exact API matrices agree with cached overlaps to below 1e-9 and produce matching decision scores. The two paths implement the same mathematical kernel. The library's pair-circuit execution costs about 7 seconds per exact matrix pair, versus 0.04–0.06 seconds for cached states on this host; those are local implementation timings, not hardware speedups.

Every noisy training Gram matrix has **17–25 negative eigenvalues**. More shots reduce mean matrix RMSE, but do not monotonically improve AP. Repair changes rankings substantially; its small mean advantage over the ideal quantum score is not a quantum benefit or evidence that noise helps. With so few positive labels, sample variation and kernel perturbations dominate interpretation. Keep an exact reference, PSD policy and matched classical controls visible in any finite-shot study.

The productive run took **120.08 seconds**, evaluating **51,624 local pair circuits** across exact/shot conditions and **79,294,464 synthetic shots**. Two preserved failed repair attempts bring recorded runner time to **240.95 seconds**. Repeated seeds during repairs are not new replications. No IBM jobs occurred. [Audited evidence](results/library-followup.json) checks source/recipe/sample hashes and recomputes scores from saved predictions.

## SQD and feature selection

[SQD's qubit interface](https://qiskit.github.io/qiskit-addon-sqd/apidocs/qiskit_addon_sqd.qubit.html) projects a Hamiltonian into sampled computational-basis states and solves the projected eigenproblem. Our relevance/redundancy/cardinality QUBO is diagonal:

$$
H=\sum_b E(b) |b\rangle\langle b|,\qquad
\lambda_{\min}(P_S H P_S)=\min_{b\in S}E(b).
$$

We tested the actual addon with eight candidates, four selected features and QAOA/uniform sample budgets of 16/64/512. Its projection has zero off-diagonal coupling within numerical tolerance, and its lowest eigenvalue equals direct minimum search on the same sampled subsets. At 512 draws both sources reach the exact optimum in all three samples. Smaller budgets retain gaps; any improvement comes from **which subsets were sampled**, not diagonalization. Exact enumeration needs only 70 feasible subsets. Adding an arbitrary transverse term changes the objective and would require a separate modelling justification.

Two samples estimate zero relevance for every feature at this label cap; the QUBO then rewards only redundancy/cardinality. This is a warning about statistical signal, not a quantum failure. The pilot also fixed integer-zero MI normalization and the addon's sparse-solver two-state edge case. Tiny subspaces use dense eigenvalues of the addon's projected matrix; larger ones use `solve_qubit`. Keep QAOA as the directly relevant quantum selector; do not promote SQD for this task.

The later [all-subset proxy audit](PROXY_ALIGNMENT.md) strengthens this distinction: across six larger training-period cohorts, negative-energy/AP correlation ranges −.144 to .708, while the exact optimum's predictive percentile ranges 49.3–90.7. Even perfect optimization of the present diagonal objective does not ensure predictive optimality. No validation-winning subset is promoted.

## Dream-RSI scope

[Dream-RSI](https://arxiv.org/html/2609.14858v1) improves exploration-policy code by replaying recorded discovery trees, then redeploying selected policies. Our earlier workflow had proposals, measured outcomes, parent references, reviews and pruning; it had not implemented that complete loop.

The initial follow-up replayed four explicit policies over nine **compatible measured encoding panels**, revealing scores only when queried. No model reruns or unseen scores are fabricated. A classical-first gating rule matches development best-observed AP **0.33023** while using **2.5 rather than 3** candidate queries. Later-fold replay uses 2.33 queries and scores **0.56405**, versus **0.56505** for three-query policies. This demonstrates a small quality/cost tradeoff in stored history. It is a finite-panel adaptation, not the paper's original tree ancestry or independent policy validation: all panels had already been inspected. [Replay evidence](results/encoding-replay.json) preserves every trace.

The owner correctly identified that this did not implement policy evolution. The subsequent [independent code-revision study](POLICY_EVOLUTION.md) now supplies a new executable rule, fresh prospective trees, independent review and selection frozen before reserved confirmation. Confirmation keeps AP .471666 while reducing candidate requests 2.333 → 1.333. Its generator is fixed; full architecture discovery and temporal generalization remain outside the result.

## Where design exploration led

The [landmark SVM screen](QUANTUM_LANDMARKS.md) tests 256 training labels and matched RBF landmarks. It achieves 12.19× fewer pair circuits, but ideal ZZ-16 and 4096-shot ZZ-16 fail its frozen quality gates. The [convergence audit](KERNEL_CONVERGENCE.md) finds sensitivity to SVM stopping tolerance. A separately frozen [fixed-ridge comparison](KERNEL_RIDGE.md) retains useful ideal 16-landmark ZZ ranking on six cohorts, with RBF still stronger on average. These are different objectives; the later result does not erase the earlier failure.

The [shot-feasibility diagnostic](SHOT_FEASIBILITY.md) finds that narrow angles amplify relative centered-matrix noise. [Local geometry](LOCAL_GEOMETRY.md) and a [matched tangent predictor](TANGENT_PREDICTION.md) identify the narrow-angle regime's classical metric approximation. The [landmark shot-ridge check](LANDMARK_SHOT_RIDGE.md) tests independent aggregate Binomial counts: 4096 passes its mean approximation gate but loses >.05 AP in two of nine replicates; 512 loses substantially. These counts model sampling rather than invoke the actual sampler. Together, the studies expose a compression/signal/noise tradeoff; they do not establish device feasibility or select a new final model. Wider circuits, arbitrary SQD couplings and hardware matrix submission remain pruned.

## Collect existing evidence

```sh
uv sync --locked --group data --group analysis --group quantum
uv run --no-sync python scripts/collect_library_followup.py
uv run --no-sync python scripts/replay_encoding_history.py
```

Collection does not fit models. Exclusive intents and complete/failed records remain in ignored `.cache/wildfire/library-followup*`; avoid rerunning them. The [frozen final report](FINAL_EVALUATION.md) remains separate. GitHub math uses `$$`; its Markdown API recognizes this SQD equation and all three [method equations](QUANTUM_METHODS.md). Ordinary TeX whitespace avoids Markdown stripping spacing escapes into literal commas. The library change initially passed 49 tests; [pinned isolated QA](data/current_repository_checks.json) pins 84 tests and all 49 script help paths to `a1893e2` with the expanded locked dependencies. Follow [pinned reproduction guidance](REPRODUCIBILITY.md) rather than resetting existing intents.

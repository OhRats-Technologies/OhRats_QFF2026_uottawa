# Pipeline mitigation

**Real-device follow-up completed:** two owner-authorized IBM jobs used 25 charged QPU seconds; measured counts and mixed downstream outcomes are in the [hardware report](IBM_PIPELINE_MITIGATION.md). The local study below remains preserved and separately labelled.

The owner clarified that the peer error-management steers apply to the actual QSVR and QAOA/SQD pipeline. The earlier game demonstrations did not complete this task. Board correction: `wildfire-game-agent-20261006T124227Z-ccd88339`. Historical game receipts remain preserved with this qualification.

## Fixed local study

[Plan](../experiments/pipeline_mitigation.json) freezes eight training years, four validation years (2007–2010), three simulator seeds, and 1,024 forward shots per overlap/selector arm. These development years and the narrow angle were inspected earlier; this is a mechanism diagnostic, not independent predictive confirmation. There is no final-test access, tuning, promotion or hardware submission.

- **QSVR:** actual one-layer four-qubit linear ZZ compute-uncompute circuits; analytic FidelityQuantumKernel reference; precomputed Qiskit QSVR with fixed C=1 and epsilon=0.2. Shot-only, readout-only, coherent-only, amplitude-only and phase-only controls precede raw/DD/gate-twirl/combined arms. Readout correction, PSD and fixed rank-four repair reuse counts. Cross-kernel repair projects onto training eigenvectors.
- **Selection:** actual continuous-target annual ten-feature QUBO, uniform cardinality-four StatePreparation and XY mixer, fixed gamma=0.4/beta=0.2. Exact 210-subset enumeration, uniform-all and uniform-feasible controls accompany ideal/noisy circuits. Existing cardinality filtering reports acceptance; actual Qiskit addon SQD verifies the diagonal sampled minimum. A fixed ridge regressor tests the resulting subset.
- **Noise:** declared coherent CX-target Z error and spectator idle drift; independent asymmetric readout. Four-qubit density-matrix kernels additionally include amplitude/phase damping. Ten-qubit selection uses coherent/readout errors only. This is not an IBM calibration model.
- **Accounting:** twirling divides the same total forward shots among four randomizations. Twelve additional all-zero/all-one calibration circuits consume 49,152 shots. Readout inversion is performed separately per randomized path before averaging, retaining negative quasi-probabilities. Selection clips and renormalizes them for a disclosed fixed auxiliary classical resample; it does not request replacement quantum shots.
- **DD:** ideal XpXm refocuses a deliberately inserted static spectator idle window per CX. Extra ideal pulses and the absence of a device scheduler limit interpretation. This does not remove amplitude damping or demonstrate physical scheduled DD.
- **QEC:** none. This implements suppression/mitigation/reconstruction from the [error study](QSVR_QEC_ERROR_STUDY.md), not encoded logical information, repeated syndrome extraction or fault tolerance. Hardware calibration blocks, strength/depth sweeps and the optional logical microkernel in that document remain unrun.

Noisy diagonal survival is measured and retained, not silently fixed to one. Raw matrices, every randomized count vector, calibration counts, repaired kernels, subsets and fitted coefficients are saved. Kernel geometry and downstream hectare/fire errors are both reported: improved geometry does not imply improved prediction. Seeds vary noise realization on the same four years, not independent datasets.

## Pipeline commands

Install the opt-in simulator group alongside the normal analysis/quantum groups:

```sh
uv sync --group data --group analysis --group quantum --group mitigation
uv run --no-sync python scripts/pipeline.py annual mitigation --output .cache/wildfire/pipeline-mitigation-v1
uv run --no-sync python scripts/pipeline.py annual mitigation --output .cache/wildfire/pipeline-mitigation-v1 --execute
uv run --no-sync python scripts/pipeline.py annual mitigation-collect --output .cache/wildfire/pipeline-mitigation-v1 --execute
```

The first command previews; execution requires a fresh output directory. An existing intent is never reset or retried automatically. Collection checks hashes, raw shot totals, calibration reconstruction, matrix transformations, sampled minima and saved predictor equations without new states, draws or fits. Frozen final files and sixteen execution-source pins are checked separately.

## Execution status

Executed once after freezing commit `79bec15`: **31.36 seconds**, 77 predictor fits, 78 prediction/control records. There were 3,933 measured circuit paths and 2,156,544 **local simulator** shots, including calibration. Zero hardware jobs and zero final-test reads. Three seeds share one four-year development cohort; no significance or independent replication claim follows.

[Saved summary](results/pipeline-mitigation.json) · [1.35 MB portable counts/circuits/models bundle](data/pipeline_mitigation_evidence.zip).

### QSVR: geometry repair can worsen prediction

Means across the three simulator seeds; analytic reference and classical controls are single fits.

| Arm | Training-kernel RMSE vs ideal | Validation MAE, ha/fire |
|---|---:|---:|
| Exact fidelity reference | 0 | 88.62 |
| Shots only | 0.0120 | 85.75 |
| Composite raw | 0.2955 | 71.04 |
| DD | 0.2396 | 76.68 |
| Gate twirl | 0.2919 | 74.81 |
| DD + gate twirl | 0.2388 | 82.68 |
| DD + gate + measurement twirl | 0.1692 | 88.17 |
| Then calibrated readout inversion | 0.0252 | 93.80 |
| Then PSD repair | 0.0245 | 88.23 |
| Then fixed rank-four repair | 0.0250 | 90.17 |
| Classical RBF | — | 117.01 |
| Training mean | — | 117.43 |

Raw PSD leaves prediction unchanged in this run; raw rank-four repair gives 83.01 ha/fire. Every arm, isolated channel, seed range and geometry metric is in the summary. Readout is the largest isolated kernel distortion here. Damping at the fixed small strength has a much smaller effect; this is not a strength sweep or evidence against its importance elsewhere.

The calibrated matrix is substantially closer to the ideal but its prediction is worse than raw. The noisy raw matrix acts like a different regularizer on this small cohort. Calling that an error-correction benefit would be wrong, and these development results do not replace the final annual comparison.

### QAOA/SQD: validity improves; the proxy still matters

| Arm | Accepted cardinality-four fraction | QUBO gap to exact minimum | Ridge validation MAE, ha/fire |
|---|---:|---:|---:|
| Ideal circuit | 1.0000 | 0.02397 | 84.92 |
| Composite raw | 0.4769 | 0 | 107.26 |
| DD | 0.5251 | 0 | 107.26 |
| Gate twirl | 0.4642 | 0 | 107.26 |
| DD + gate twirl | 0.5173 | 0.02397 | 84.92 |
| DD + gate + measurement twirl | 0.5498 | 0.04794 | 62.58 |
| Then readout inversion/resampling | 0.6589 | 0.04794 | 62.58 |
| Uniform feasible control | 1.0000 | 0 | 107.26 |
| Exact 210-subset control | 1.0000 | 0 | 107.26 |

Before readout, modeled logical cardinality probability rises from 0.7699 raw to 0.9095 with DD. Gate twirling does not improve it here. Readout correction raises observed acceptance but does not change the selected subset or ridge error relative to the combined arm.

Corrected ten-qubit quasi-probabilities contain negative mass **0.306–0.328**. Clipping/resampling is a biased reconstruction, not physical recovered shots; its 3,072 auxiliary classical draws are separately counted. Improved acceptance is not an unbiased distribution-recovery claim.

All sampled SQD minima equal their diagonal sampled classical minima. The exact lowest-QUBO subset has worse prediction than the higher-cost combined-arm subset. This reinforces the project's existing objective-alignment problem, not a quantum advantage. There are only 210 feasible subsets.

The ten-qubit compiled circuit has **1,123 CX gates and depth 4,257**, dominated by generic StatePreparation. It is not the earlier eight-qubit 319-CX circuit, nor a scalable Dicke construction. Noise is applied throughout that actual compiled circuit.

### Collection and coverage

Collection reconstructs **76 saved kernel/selector predictor equations** and checks **3,933** count paths with no new states, draws or fits; the public bundle passes with simulator, state generation, RNG and fit methods blocked. All 78 saved prediction metrics and the training-mean control are checked separately. The single RBF control's fitted coefficients were not saved, so its equation is not independently reconstructed; its predictions and metrics are retained.

Fourteen focused tests pass: seven suppression/readout/repair/safety tests, four existing annual-front-door tests and three public-evidence/source-pin tests. The public artifact checker passes 23 scoped checks, including the six original annual artifacts and sixteen execution-source pins. The added Aer group changes current dependency manifests; historical environment differences are disclosed rather than certified as identical.

Collect the published bundle into a fresh directory without source caches:

```sh
uv run --no-sync python scripts/run_pipeline_mitigation.py collect \
  --bundle docs/data/pipeline_mitigation_evidence.zip \
  --output .cache/wildfire/mitigation-public
```

This completes the bounded local pipeline correction after the original deadline. It does not backdate completion, validate live hardware, implement logical QEC, select a new final model or complete the entire hardware/logical research programme in the error-study document.

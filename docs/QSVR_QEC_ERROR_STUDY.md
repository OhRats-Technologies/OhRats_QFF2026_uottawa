# Deep Technical Study: QSVR, Quantum-Device Errors, and Qiskit/IBM Quantum

**Repository implementation, October 6:** the [actual pipeline study](PIPELINE_MITIGATION.md) now implements a bounded local subset of this programme on annual climate/fire data: isolated noise controls, DD/twirling, readout calibration, raw/PSD/rank kernels, QSVR predictions and QAOA/SQD cardinality diagnostics. It retains counts, circuits, models and a no-rerun collector. Improved kernel geometry did not improve QSVR error in that fixed cohort. This is simulator suppression/mitigation, not logical QEC or completed hardware calibration blocks. Earlier game instruments did not satisfy pipeline implementation.

## Scope and central conclusion

“QSVR qubit error correction” has two technically distinct interpretations:

1. **Protect a quantum support-vector regression (QSVR) workload from hardware errors.** This is the most practical interpretation for present IBM Quantum access. The quantum processor estimates a kernel; classical software repairs or mitigates that kernel and solves epsilon-SVR.
2. **Use SVR or QSVR as a quantum-error-correction decoder or error predictor.** Classical SVR has been used to predict circuit error and guide circuit fragmentation, but the literature search found no mature body of evidence showing that *quantum-kernel* SVR is a competitive real-time syndrome decoder. i-QER, for example, selected a classical RBF-SVR to predict circuit error, not QSVR.[^1]

The recommended directed study is therefore a **noise-aware QSVR kernel study on IBM hardware**, with an optional, clearly separated logical-qubit experiment. Calling dynamical decoupling, twirling, readout calibration, or positive-semidefinite kernel repair “quantum error correction” would be inaccurate. Genuine QEC encodes logical information into multiple physical qubits, repeatedly extracts syndromes, decodes them, and applies or tracks corrections; IBM’s repetition-code tutorial provides a real dynamic-circuit example, although that code protects only against bit flips and is not a complete quantum code.[^2][^3]

The strongest near-term research question is:

> **How much predictive performance and kernel geometry can be recovered in QSVR by hardware-aware compilation, Sampler-level error suppression, and statistically principled kernel reconstruction, and at what QPU and sampling cost?**

A second, higher-risk question can then ask:

> **Does encoding a restricted QSVR feature map in a small error-detecting or repetition code improve overlap estimation after accounting for extra two-qubit gates, syndrome shots, postselection, and logical-state restrictions?**

## Conceptual map

| Layer | Object | Primary failure mode | Appropriate response |
|---|---|---|---|
| Data | Classical feature vector $x$ | Scale, leakage, poor inductive bias | Train-only preprocessing, dimensionality reduction, bandwidth tuning |
| Encoding | $\vert\phi(x)\rangle=U_\phi(x)\vert0^q\rangle$ | Excessive depth, concentration, routing overhead | Shallow hardware-aligned feature maps |
| Kernel circuit | $U_\phi(x_j)^\dagger U_\phi(x_i)$ | Gate noise, decoherence, coherent error | Better layout, dynamical decoupling, twirling |
| Measurement | All-zero probability | Shot noise, assignment error | Shot allocation, measurement twirling/calibration |
| Gram matrix | $K$ | Asymmetry, non-unit diagonal, negative eigenvalues | Symmetrization, diagonal constraints, PSD or low-rank repair |
| Regressor | epsilon-SVR dual | Hyperparameter sensitivity, overfitting | Nested tuning of $C$, $\epsilon$, target scale |
| Evaluation | Test predictions | Split variance, calibration drift | Repeated outer splits and time-separated hardware blocks |
| True QEC | Encoded logical state | Logical errors and decoder latency | Syndrome extraction, decoding, correction or Pauli-frame tracking |

## Mathematical foundation

### Epsilon-SVR

Given training observations $(x_i,y_i)$, epsilon-SVR seeks a function

$$
f(x)=\langle w,\phi(x)\rangle+b
$$

that is flat while tolerating deviations smaller than $\epsilon$. Its primal objective is

$$
\min_{w,b,\xi,\xi^*}\frac{1}{2}\lVert w\rVert^2+C\sum_{i=1}^{n}(\xi_i+\xi_i^*)
$$

subject to

$$
y_i-f(x_i)\leq \epsilon+\xi_i,
$$

$$
f(x_i)-y_i\leq \epsilon+\xi_i^*,
$$

$$
\xi_i,\xi_i^*\geq0.
$$

The dual depends on samples only through a kernel $K(x_i,x_j)=\langle\phi(x_i),\phi(x_j)\rangle$:

$$
\max_{\alpha,\alpha^*}-\frac{1}{2}(\alpha-\alpha^*)^T K(\alpha-\alpha^*)-\epsilon\mathbf{1}^T(\alpha+\alpha^*)+y^T(\alpha-\alpha^*)
$$

with $0\leq\alpha_i,\alpha_i^*\leq C$ and $\sum_i(\alpha_i-\alpha_i^*)=0$. This is why the Qiskit implementation can remain a conventional scikit-learn SVR after replacing its kernel evaluator. Current Qiskit `QSVR` extends `sklearn.svm.SVR`, accepts a `quantum_kernel`, and can also consume a precomputed matrix.[^4][^5]

A critical implication is that **the QPU does not train the support-vector optimization** in Qiskit’s QSVR. It estimates entries of $K$; a classical convex solver determines the dual coefficients. This differs from quantum linear-system SVM proposals and from annealing-based SVR formulations.[^6][^7][^8]

### Fidelity quantum kernel

For a classical vector encoded as

$$
|\phi(x)\rangle=U_\phi(x)|0^q\rangle,
$$

a common kernel is

$$
K(x,z)=|\langle\phi(z)|\phi(x)\rangle|^2.
$$

The compute-uncompute circuit applies $U_\phi(x)$, followed by $U_\phi(z)^\dagger$, and estimates the probability of observing $0^q$. The all-zero probability equals the state fidelity in the noiseless pure-state case. This architecture underlies Qiskit’s `FidelityQuantumKernel` and `ComputeUncompute` path.[^9][^10]

For $n$ unique training points, symmetry and the known diagonal reduce the nominal training cost from $n^2$ to

$$
N_{\mathrm{train}}=\frac{n(n-1)}{2}
$$

distinct off-diagonal overlap circuits. For $m$ test points, the cross-kernel adds

$$
N_{\mathrm{test}}=mn
$$
overlaps. At $S$ shots per circuit, the nominal shot budget is

$$
S\left(\frac{n(n-1)}{2}+mn\right),
$$

before twirling randomizations, repeated calibrations, mitigation circuits, or feature-map tuning. This quadratic bottleneck is fundamental to the standard full Gram-matrix workflow. Nyström methods can reduce quantum-kernel construction toward linear scaling in $n$ for a fixed number of landmarks, at some approximation cost.[^11]

### Shot-noise floor

If one kernel entry is estimated as an all-zero frequency from $S$ Bernoulli samples with success probability $p=K(x,z)$, then

$$
\operatorname{Var}(\hat K)=\frac{p(1-p)}{S}\leq\frac{1}{4S}.
$$

The worst-case standard deviation is therefore $1/(2\sqrt{S})$. This gives approximately 0.0156 at 1,024 shots, 0.0078 at 4,096 shots, and 0.0055 at 8,192 shots before hardware bias. More shots reduce sampling variance but cannot remove coherent gate bias, relaxation, leakage, crosstalk, or drift. Qiskit’s `FidelityStatevectorKernel` can emulate this binomial shot noise and optionally project the resulting training kernel back to the PSD cone.[^12]

### Why PSD matters

An exact fidelity Gram matrix is positive semidefinite because it is an inner-product Gram matrix in operator space. Finite sampling and inconsistent noisy estimates can produce a matrix that is asymmetric or has negative eigenvalues. Qiskit’s `FidelityQuantumKernel` therefore exposes `enforce_psd=True`, while `evaluate_duplicates='off_diagonal'` fixes the training diagonal to one and avoids unnecessary diagonal circuits.[^13][^9]

Blind PSD projection is not automatically optimal for prediction. It changes the measured geometry and can behave as implicit regularization. A deep study should preserve both the **raw matrix** and every transformed matrix, then report:

- Asymmetry $\lVert K-K^T\rVert_F/\lVert K\rVert_F$.
- Diagonal deviation $\lVert\operatorname{diag}(K)-\mathbf{1}\rVert_2$.
- Minimum eigenvalue and total negative spectral mass.
- Effective rank.
- Frobenius alignment to the exact reference.
- Target alignment.
- Downstream RMSE, MAE, and $R^2$.

## Error taxonomy for QSVR

### Statistical measurement error

Shot noise perturbs each overlap estimate and can break PSD even if the circuit is otherwise ideal. It is input dependent because the Bernoulli variance is largest near fidelity 0.5. Shot allocation should therefore be treated as an experimental factor rather than a fixed implementation detail.

A useful extension is adaptive shot allocation. Run a pilot budget $S_0$, estimate $\hat p_{ij}(1-\hat p_{ij})$, and allocate subsequent shots preferentially to entries with large estimated variance or high leverage under the provisional SVR. This tests whether equal-shot acquisition wastes QPU time on entries near zero or one.

### State-preparation and gate error

Errors in $U_\phi(x)$ and $U_\phi(z)^\dagger$ change the encoded states and therefore bias the kernel itself. Because both halves of a compute-uncompute circuit contain data-dependent gates, the bias need not be a uniform shrinkage. Two-qubit routing gates are particularly important: an expressive feature map that performs best exactly may be inferior after mapping to a sparse coupling graph.

### Coherent error

Systematic over-rotations and residual interactions can create structured, repeatable kernel distortion. Pauli twirling converts a general channel into a Pauli channel in the twirled average while preserving the ideal circuit action, replacing one circuit with an ensemble of randomized equivalents. This can make residual errors more stochastic and easier to average, but it increases execution bookkeeping and changes how the total shot budget is divided among randomizations.[^14]

### Decoherence and idle error

Relaxation and dephasing accumulate with scheduled duration. Dynamical decoupling inserts identity-equivalent pulse sequences into idle windows to suppress coherent idle evolution. IBM Sampler exposes `XX`, `XpXm`, and `XY4` sequences; the feature is disabled by default.[^15][^14]

Amplitude damping deserves special attention because the IBM-hardware QSVR anomaly study found it more damaging than depolarizing, phase-damping, phase-flip, or bit-flip noise.[^16][^17] A feature map whose ideal states contain substantial excited-state population may therefore show input-dependent contraction toward $|0^q\rangle$, biasing all-zero probabilities in a way that can superficially increase some overlaps and decrease others.

### Readout error

The kernel is inferred from one distinguished bit string, $0^q$. Assignment errors can therefore bias the kernel even if state preparation is perfect. Measurement twirling can reduce systematic readout bias, while full assignment-matrix mitigation becomes costly as qubit count grows. A recent fidelity-kernel study proposed bit-flip tolerance, where bit strings within a calibrated Hamming distance of zero contribute to the fidelity estimate; it reported that noisy finite-shot kernels need not be PSD and combined the method with dynamical decoupling and measurement twirling.[^18]

### Drift and miscalibration

Calibration changes can move qubit frequencies, readout assignments, gate errors, and coherence times during or between Gram-matrix jobs. This is especially dangerous because the matrix is assembled from many circuits: blocks acquired at different times can have different noise maps. The QSVR anomaly study found miscalibration among the more disruptive noise conditions.[^17]

A single hardware run is consequently insufficient. The matrix should be reacquired in time-separated blocks, and each acquisition should record backend properties, physical layout, transpiled depth, two-qubit counts, timestamps, and job IDs.

### Leakage and crosstalk

Leakage violates the computational-subspace model; crosstalk creates spatially correlated errors. These are difficult for simple independent Pauli or depolarizing simulations to capture. Contemporary QEC decoders explicitly treat leakage and correlated noise as central challenges. Aer device-derived models are useful but approximate: IBM/Qiskit documentation notes that they are built from limited average calibration parameters and do not reproduce all real-device errors.[^19][^20]

## QEC, suppression, mitigation, and repair

| Method | Extra physical qubits | Extra quantum executions | Classical model assumption | Produces logical qubit? |
|---|---:|---:|---|---:|
| Better transpilation/layout | No | Usually no | Hardware topology and calibration | No |
| Dynamical decoupling | No | No extra shots, but more pulses | Idle-error cancellation | No |
| Pauli twirling | No | Multiple randomized circuits | Ensemble-averaged channel | No |
| Measurement mitigation | No | Calibration and/or randomized shots | Readout channel | No |
| Zero-noise extrapolation | No | Multiple noise-scaled runs | Smooth extrapolation toward zero noise | No |
| Probabilistic error cancellation | No | Potentially high sampling overhead | Accurate inverse-noise representation | No |
| PSD projection | No | No | Exact kernel should be PSD | No |
| Low-rank repair | No | No | Signal lies in dominant eigenspace | No |
| Repetition/stabilizer code | Yes | Syndrome cycles and decoder | Correctable error set and code assumptions | Yes, in a restricted sense |
| Fault-tolerant logical algorithm | Large | Repeated syndrome extraction | Below-threshold physical operation | Yes |

Error mitigation can work on small systems but has scaling limits. Rigorous analyses show worst-case shallow circuits for which a superpolynomial number of samples is needed to infer noiseless observables, and noise also constrains quantum-kernel estimation. Separately, quantum-kernel theory shows that noise can drive exponential concentration with circuit depth and that common mitigation methods do not generally remove the associated data-independent flattening.[^21][^22]

Therefore, the study should not assume “more mitigation is always better.” It should measure whether a method improves the **downstream regression decision**, not merely the elementwise kernel error. Recent work on decision-aware mitigation similarly argues that reducing expectation-value error need not improve rankings or downstream choices.[^23]

## Literature synthesis

### Foundational quantum kernels

Havlíček et al. introduced and experimentally demonstrated quantum-enhanced feature spaces and quantum-kernel estimation on a superconducting processor. The central opportunity is not that SVR itself becomes quantum, but that the device estimates an inner product in a feature space that may be expensive to reproduce classically.[^24]

Schuld’s kernel interpretation shows that many supervised variational quantum models can be expressed as kernel methods and emphasizes that data encoding is the central inductive choice. This motivates treating feature-map selection, bandwidth, and effective dimension as core modeling decisions rather than circuit decoration.[^25]

The “power of data” analysis provides a major caution: even when a quantum model evaluates a classically difficult function, a classical learner trained on examples can sometimes predict it competitively. Quantum advantage claims therefore require strong classical baselines and must account for data loading, kernel acquisition, and sample complexity.[^26]

### Early QSVR on IBM hardware

Djehiche and Löfdahl formulated disability-incidence modeling as QSVR, using a quantum feature map to estimate the kernel and a classical SVR for optimization. Their IBM Yorktown experiment used two of five qubits and 8,192 shots for every data pair. This paper is important as a transparent early demonstration, but it does not establish scalable advantage: the dimension and dataset are small, and the kernel-acquisition cost is not eliminated.[^27]

### Noise-aware QSVR

Suzuki et al. studied QSVC and QSVR under noiseless simulation, noisy simulation, and IonQ hardware. For regression, low-rank approximation of the noisy kernel plus epsilon-SVR hyperparameter tuning improved near-term-device performance. Their detailed treatment used eigendecomposition for a square training matrix and SVD for the rectangular train-test matrix; they also used kernel alignment as a hardware-fidelity diagnostic.[^28][^29]

This evidence supports spectral denoising but does not establish a universal recipe. A rank selected using test performance would leak information. Rank or regularization strength must be selected inside the training process or fixed from a noise model before the final test evaluation.

### IBM QSVR anomaly detection

The 2023 anomaly-detection study used a QSVR reconstruction-loss method across eleven datasets. It reported a mean simulated-QSVR AUC of 0.77 versus 0.76 for classical RBF-SVR, while the QSVR matched or exceeded the quantum autoencoder on most datasets. Those differences are small enough that split design, tuning fairness, and uncertainty matter.[^30]

The expanded hardware study ran five qubits on a 27-qubit IBM device. It reported mean AUC 0.72 on hardware versus 0.76 in noiseless simulation; hardware outperformed ideal simulation on two of eleven datasets but underperformed on eight. More than 500 noisy models were used to study noise sensitivity, with amplitude damping and miscalibration causing the strongest degradation among the tested channels.[^16][^17]

The same study found severe adversarial vulnerability: weak projected-gradient attacks with $\varepsilon=0.01$ could reduce AUC by up to an order of magnitude, and neither noise nor the tested adversarial-training setup reliably fixed it. This is relevant even for ordinary regression because it shows that apparent hardware-noise robustness does not imply robustness to structured input perturbations.[^17]

### Quantum-kernel-specific mitigation

Training quantum embedding kernels under noise has motivated methods that infer a survival factor from known unit diagonal entries and combine noise-model correction with Tikhonov regularization. Tests on simulated depolarizing noise and real QPU data found that post-processing could partially recover the noiseless kernel, with preferred methods depending on noise and shot regime.[^31]

This line of work is more directly applicable to QSVR than generic ZNE because it exploits kernel structure. A complete study should compare:

- Qiskit nearest-PSD projection.
- Eigenvalue clipping.
- Higham-style nearest correlation matrix projection.
- Tikhonov shift $K+\lambda I$.
- Truncated eigendecomposition.
- Depolarizing-model correction using diagonal/survival estimates.
- Nyström approximation with hardware-evaluated landmarks.
- Optional Hamming-radius or bit-flip-tolerant fidelity.[^31][^18][^11]

### QSVR as QEC decoder

The direct evidence here is weak. i-QER used a **classical** nonlinear RBF-SVR to predict circuit error and selected it over linear regression, lasso, and random forest; the reported training MAE was 1.2305% with $R^2=0.98$, after which predicted error guided recursive circuit fragmentation. This is error reduction through prediction and circuit cutting, not stabilizer decoding and not QSVR.[^1]

Modern QEC decoding research instead emphasizes recurrent transformers, graph methods, matching, tensor networks, and maximum-likelihood search. AlphaQubit, for example, uses a recurrent transformer trained on simulated data and fine-tuned on experimental syndrome data; it outperformed prior decoders on the studied surface-code experiments. The Tesseract project implements a search-based most-likely-error decoder for quantum LDPC codes with Stim detector-error-model support.[^32][^19]

A QSVR decoder would face three structural problems:

- The decoder output is usually a discrete correction class or logical observable, not a scalar regression target.
- Real-time QEC imposes strict latency and throughput constraints, while a quantum-kernel decoder would require additional noisy quantum executions to decode a quantum computer’s own syndrome.
- Syndrome datasets are large and repeated every code cycle, whereas full quantum-kernel construction scales quadratically in training samples.

A more plausible research use is **offline calibration regression**: classical SVR can map circuit/calibration descriptors to expected error; QSVR could be tested as an offline benchmark but is unlikely to be a practical real-time decoder without a compelling data-access model and latency advantage.

## Current IBM/Qiskit stack

### Qiskit Machine Learning

As of version 0.9.1, `QSVR` supports either a `BaseKernel` or `quantum_kernel="precomputed"`; the ordinary `kernel=` keyword is discarded. Precomputed mode is the correct interface for experiments involving multiple repaired versions of one measured kernel because it prevents accidental reacquisition.[^4]

`FidelityQuantumKernel` provides:

- `enforce_psd` for square training matrices.
- `evaluate_duplicates` to control duplicate and diagonal execution.
- `max_circuits_per_job` to split large kernel batches according to backend limits.[^13][^9]

`FidelityStatevectorKernel` provides exact overlaps, statevector caching, finite-shot emulation, and optional PSD enforcement. It is the appropriate reference for separating feature-map quality from QPU error.[^12]

### IBM primitives in October 2026

Qiskit Runtime 0.50.0 introduced client-side `Sampler` and `Estimator` implementations and deprecated the legacy `SamplerV2` and `EstimatorV2` classes. Current code should import:

```python
from qiskit_ibm_runtime.executor_sampler import Sampler
```

rather than copying older root-level imports. Client-side primitives perform pre- and post-processing locally and delegate execution to Executor, providing more visibility and control.[^33][^34][^35]

The Sampler supports dynamical decoupling and Pauli twirling. Relevant controls include:[^36]

```python
sampler.options.dynamical_decoupling.enable = True
sampler.options.dynamical_decoupling.sequence_type = "XpXm"
sampler.options.twirling.enable_gates = True
sampler.options.twirling.enable_measure = True
```

When twirling is enabled, shot precedence is subtle: the product of `num_randomizations` and `shots_per_randomization` can determine the effective shot count, and conflicting explicit values can cause job failure. Every experiment should record the resolved randomization count and shots per randomization, not only `default_shots`.[^35][^15]

Batch mode groups related primitive jobs on one QPU and is appropriate for acquiring blocks of one Gram matrix. Current IBM examples construct `Batch(backend=backend)` and pass that object through `mode` to the Sampler.[^37]

### Dynamic circuits and true QEC

IBM’s repetition-code tutorial uses mid-circuit stabilizer measurement, reset, and conditional control to protect $|\bar 1\rangle=|111\rangle$ against a single bit flip.[^2][^3] It compares repeated dynamic correction with end-only decoding and an unencoded qubit. This is the correct starting point for a genuine QEC extension, but the repetition code cannot protect an arbitrary qubit from both $X$ and $Z$ errors.

Sampler’s current dynamical-decoupling implementation is incompatible with dynamic circuits. Therefore, a logical-QSVR experiment cannot blindly combine every suppression option with syndrome-feedback circuits; compatibility must be tested condition by condition.[^38]

## Recommended experimental program

### Phase 0: Reproducible environment

Pin and archive:

- Python version.
- `qiskit`.
- `qiskit-machine-learning`.
- `qiskit-ibm-runtime`.
- `qiskit-aer`.
- `scikit-learn`, NumPy, and SciPy.
- Backend name and target snapshot.
- Full transpiler configuration and seed.
- Physical qubit layout.
- Job IDs and timestamps.
- Raw counts or bit arrays, not only reconstructed kernel values.

Raw measurement data are essential because new readout or kernel reconstruction methods can then be tested without consuming more QPU time.

### Phase 1: Exact baselines

Use two tasks:

1. A controlled synthetic regression problem where target smoothness and intrinsic dimension are known.
2. A small real tabular regression task with a preregistered split.

For each task:

- Fit linear, polynomial, RBF, and Matérn-like classical baselines where available.
- Standardize features using training data only.
- Reduce to 2–5 dimensions with PCA fitted only on the training fold.
- Standardize or robust-scale the target; transform predictions back before reporting errors.
- Sweep quantum feature-map family, repetitions, entanglement pattern, and input bandwidth.
- Evaluate exact kernel spectra and target alignment.

Do not proceed to hardware with a quantum kernel that is already poor or nearly constant in exact simulation. Exponential concentration can arise from encoding expressivity, global measurements, entanglement, and noise.[^22]

### Phase 2: Controlled noise decomposition

Use Qiskit Aer to isolate:

- Finite shots only.
- Readout error only.
- Depolarizing gate noise.
- Coherent over-rotation.
- Amplitude damping.
- Phase damping.
- Thermal relaxation using $T_1$, $T_2$, and gate duration.
- Composite backend-derived noise.

Aer provides `NoiseModel`, `QuantumError`, and `ReadoutError`; thermal relaxation is parameterized by $T_1$, $T_2$, gate time, and equilibrium excited-state population. Device-derived Aer models combine depolarizing and thermal-relaxation approximations with readout error but remain only approximations to actual hardware.[^39][^40][^20][^41]

For each channel, sweep physically interpretable strength and report both elementwise kernel distortion and regression performance. This will reveal cases in which a larger Frobenius error nevertheless regularizes the predictor, as well as cases in which a visually modest kernel error destroys the support-vector solution.

### Phase 3: Hardware acquisition

Use a blocked factorial design:

| Factor | Levels |
|---|---|
| Suppression | Off; DD; twirling; DD + twirling |
| Feature-map depth | 1; 2 repetitions |
| Shot budget | 1,024; 4,096; 8,192 or budget-equivalent levels |
| Matrix reconstruction | Raw; PSD; ridge; truncated spectrum |
| Hardware time | At least 3 time-separated calibration blocks |
| Transpilation | Fixed seed plus a small seed ensemble |

Within a block, use the same dataset, backend, feature map, physical layout, and target preprocessing. Randomize or interleave circuit order when feasible so that drift is not confounded with matrix position.

The minimum hardware matrix should be small enough to complete in one coherent block. For example, $n=20$, $m=10$ requires 190 training overlaps plus 200 test overlaps, or 390 distinct overlap circuits before randomized compilations. At 4,096 shots, this is about 1.60 million nominal shots per condition. A four-condition suppression ablation repeated across three calibration blocks already exceeds 19 million nominal shots, before calibration circuits and twirling expansion.

### Phase 4: Kernel reconstruction

#### Raw constrained matrix

Construct

$$
K_s=\frac{K+K^T}{2}
$$

and compare two diagonal choices:

- Measured diagonal, which contains information about survival and readout bias.
- Unit diagonal, required by the ideal normalized fidelity kernel.

Never overwrite the only stored copy of the measured diagonal; kernel-specific mitigation methods may use it to infer survival factors.[^31]

#### Eigenvalue clipping

If

$$
K_s=Q\Lambda Q^T,
$$

set $\Lambda_+=\max(\Lambda,0)$ and reconstruct $Q\Lambda_+Q^T$. Renormalize to unit diagonal only after checking numerical stability. This is simple but can overfit noise if many small positive eigenvalues remain.

#### Ridge repair

Use

$$
K_\lambda=K_s+\lambda I.
$$

This changes the diagonal and corresponds to a Tikhonov-style regularization. Select $\lambda$ using training-only cross-validation or a prespecified noise rule.

#### Truncated spectrum

Retain the largest $r$ positive eigenvalues:

$$
K_r=Q_r\Lambda_rQ_r^T.
$$

Choose $r$ by nested validation, a training-only explained-spectrum threshold, or a random-matrix noise threshold. The evidence from noisy QSVR supports low-rank approximation, but test-set rank selection is invalid.[^29][^28]

#### Rectangular test kernel

A square training repair does not uniquely define how to repair $K_{\mathrm{test,train}}$. The transformation must be derived solely from training geometry. One consistent projection is

$$
K^*_{r}=K^*Q_rQ_r^T,
$$

possibly followed by the same training-column normalization used for $K_r$. Alternatively, Nyström features can provide an explicit common embedding for train and test points. Independently taking an SVD of the entire test matrix risks test-dependent preprocessing and complicates deployment.

### Phase 5: Statistical analysis

Primary endpoints:

- Test RMSE.
- Test MAE.
- $R^2$.
- QPU seconds or equivalent billed usage.

Secondary endpoints:

- Exact-vs-hardware kernel alignment.
- Centered kernel-target alignment.
- Negative spectral mass.
- Effective rank.
- Support-vector count and identity stability.
- Prediction disagreement among hardware blocks.
- Calibration-to-calibration variance.

Use paired outer splits so all kernel variants see identical data. For a fixed held-out set, bootstrap paired prediction errors to estimate uncertainty in the difference between methods. Across calibration blocks, use a hierarchical model or repeated-measures analysis separating dataset split, backend time, and shot noise. Do not report only the best hardware run.

A sensible success criterion is not merely “hardware QSVR beats exact QSVR,” because noise can occasionally regularize a small dataset. Require that an intervention improves performance across multiple blocks, reduces a preregistered kernel defect, and does not achieve gains solely through post hoc rank or hyperparameter selection.

## Ablation matrix

| Ablation | Question | Confound controlled |
|---|---|---|
| Exact vs finite-shot statevector | How much error is sampling alone? | Device bias |
| Finite-shot vs Aer device model | How much comes from modeled hardware channels? | Live drift |
| Aer vs hardware raw | What remains unmodeled? | Feature-map choice |
| Raw vs DD | Does idle suppression help? | Twirling |
| Raw vs twirling | Does randomized compiling help? | DD |
| Fixed vs adaptive shots | Is equal allocation inefficient? | Total shot budget |
| Raw vs PSD | Is indefiniteness materially harmful? | QPU acquisition |
| PSD vs low rank | Is denoising more important than convexity? | Same raw matrix |
| Quantum vs RBF kernel | Is the feature map useful? | SVR optimizer |
| Physical vs encoded microkernel | Does a code improve overlap estimation? | Same logical task |

## Genuine QEC extension

### Why ordinary repetition coding is insufficient

A three-qubit bit-flip code maps

$$
\alpha|0\rangle+\beta|1\rangle
\mapsto
\alpha|000\rangle+\beta|111\rangle.
$$

It can diagnose and correct one $X$ error through parity checks, but it does not protect against phase error. A QSVR feature map involving arbitrary rotations and entangling phases will generally leave the restricted set of operations that are easy to implement fault-tolerantly in this code. The IBM repetition tutorial accordingly demonstrates protected memory for a logical basis state, not arbitrary universal logical computation.[^3][^2]

### Feasible microbenchmark

A defensible first logical-kernel experiment is deliberately narrow:

1. Encode one scalar feature into a logical state compatible with the selected code.
2. Restrict the logical circuit to operations that can be implemented transversally or with a clearly audited logical construction.
3. Estimate a physical overlap and a logical overlap under matched feature values.
4. Extract syndromes and either postselect, decode at the end, or apply dynamic correction.
5. Compare logical overlap error, acceptance probability, total shots, physical-qubit count, depth, and latency.

The correct figure of merit is not raw logical fidelity alone. Use cost-normalized improvement such as

$$
G=\frac{\operatorname{MSE}_{\mathrm{physical}}-\operatorname{MSE}_{\mathrm{logical}}}{\text{QPU cost multiplier}},
$$

and report negative values honestly when the encoding overhead makes performance worse.

### IBM hardware trajectory

IBM’s current large-scale plan targets Starling in 2029 with 200 logical qubits and 100 million gates. The proposed bivariate-bicycle “gross” code has parameters $[[144,12,12]]$, using 144 data qubits and 144 check qubits to encode 12 logical qubits; IBM presents it as roughly tenfold lower qubit overhead than a comparable surface-code construction.[^42][^43][^44]

This roadmap does not mean that a general user can currently run a fully fault-tolerant QSVR. It means QEC architecture is progressing while present user-accessible experiments remain dominated by physical circuits, dynamic-circuit demonstrations, and research-scale logical memories.

Recent IBM-hardware research is nonetheless relevant. A 2026 heavy-hex dynamic-compass-code experiment reported 24%–38% reductions in per-round logical error from context-dependent noise characterization, soft readout information, and leakage-aware postselection. This reinforces an important lesson for QSVR: detailed noise information and soft measurement data can matter more than a generic one-size-fits-all correction.[^45]

## Implementation architecture

A robust repository should separate acquisition from analysis:

```text
qsvr-study/
├── configs/
│   ├── datasets.yaml
│   ├── feature_maps.yaml
│   └── hardware_conditions.yaml
├── src/
│   ├── data.py
│   ├── feature_maps.py
│   ├── transpile.py
│   ├── acquire.py
│   ├── reconstruct.py
│   ├── qsvr.py
│   ├── metrics.py
│   └── provenance.py
├── runs/
│   └── RUN_ID/
│       ├── config.json
│       ├── backend.json
│       ├── circuits.qpy
│       ├── raw_counts/
│       ├── kernel_raw.npz
│       ├── kernel_repaired.npz
│       ├── predictions.csv
│       └── metrics.json
└── tests/
    ├── test_kernel_symmetry.py
    ├── test_no_leakage.py
    ├── test_repair_train_only.py
    └── test_cost_accounting.py
```

### Acquisition pseudocode

```python
service = QiskitRuntimeService()
backend = service.backend(BACKEND_NAME)
pm = generate_preset_pass_manager(
    backend=backend,
    optimization_level=3,
    seed_transpiler=SEED,
)

with Batch(backend=backend) as batch:
    sampler = Sampler(mode=batch)
    sampler.options.default_shots = SHOTS
    sampler.options.dynamical_decoupling.enable = ENABLE_DD
    sampler.options.dynamical_decoupling.sequence_type = "XpXm"
    sampler.options.twirling.enable_gates = ENABLE_TWIRLING

    fidelity = ComputeUncompute(
        sampler=sampler,
        pass_manager=pm,
    )
    kernel = FidelityQuantumKernel(
        feature_map=feature_map,
        fidelity=fidelity,
        enforce_psd=False,
        evaluate_duplicates="off_diagonal",
        max_circuits_per_job=MAX_CIRCUITS,
    )
    K_train_raw = kernel.evaluate(X_train)
    K_test_raw = kernel.evaluate(X_test, X_train)
```

Set `enforce_psd=False` during acquisition because otherwise the primary hardware defect is hidden before analysis. Qiskit can perform PSD projection automatically, but a scientific comparison needs the raw matrix.[^9][^13]

### Precomputed QSVR

```python
from qiskit_machine_learning.algorithms import QSVR

model = QSVR(
    quantum_kernel="precomputed",
    C=C,
    epsilon=epsilon,
)
model.fit(K_train_repaired, y_train)
y_pred = model.predict(K_test_repaired)
```

Using precomputed mode ensures hyperparameter sweeps do not re-run the QPU.[^4]

### Provenance checks

Each run should hash:

- Ordered training and test indices.
- Preprocessor state.
- Bound feature-map circuit template.
- Transpiled circuits or QPY archive.
- Physical layout.
- Kernel reconstruction parameters.
- Software lockfile.

The most common hidden reproducibility failure is reordering samples between acquisition and fitting. Because a Gram matrix has no self-describing row semantics, store sample IDs beside every matrix.

## Expected failure modes

### Mistaking regularization for correction

Noise or rank truncation can improve test error by reducing effective capacity while moving the matrix farther from the exact kernel. Report both predictive and geometric metrics. If test error improves but exact alignment worsens, describe the mechanism as regularization, not error correction.

### Data leakage in kernel repair

Choosing rank, eigenvalue threshold, or mitigation strength from final test performance invalidates the result. All choices must be fitted on training folds and then applied to the untouched test cross-kernel.

### Incomparable shot budgets

Twirling divides shots across randomized circuits. Comparing “4,096 shots” with and without twirling is ambiguous unless the total QPU shots and number of randomizations are both matched and recorded.[^15]

### Backend selection bias

Selecting the backend after inspecting final task performance is another hidden hyperparameter. Predefine a backend criterion based on availability, required qubit count, two-qubit error, readout error, and connected subgraph quality.

### Simulator overconfidence

Aer backend models are approximations based on calibration summaries and simplified channels. Agreement under Aer does not guarantee agreement under leakage, crosstalk, nonstationarity, or context-dependent error.[^20]

### Classical-baseline weakness

A quantum kernel should be compared with tuned linear, RBF, polynomial, and, where suitable, tree or Gaussian-process baselines. The anomaly-detection literature shows only a narrow average gap between QSVR and RBF-SVR in one benchmark. Untuned classical baselines do not support a quantum advantage claim.[^30]

### Unsupported QEC claims

Postselection, parity checking, twirling, and kernel projection are not interchangeable with fault-tolerant QEC. State exactly which error set is detected, which is corrected, whether correction is real-time or deferred, and whether the encoded circuit implements the intended logical operation.

## Paper reading order

### Core QSVR

1. **Djehiche and Löfdahl — Quantum Support Vector Regression for Disability Insurance.** Read for the basic hybrid architecture and early IBM hardware execution; note the two-qubit, 8,192-shot-per-pair experiment.[^27]
2. **Suzuki et al. — Quantum Support Vector Machines for Classification and Regression on a Trapped-Ion Quantum Computer.** Read for noise simulation, hardware comparison, low-rank reconstruction, and alignment diagnostics.[^28][^29]
3. **Tscharke et al. — Semisupervised Anomaly Detection Using SVR with Quantum Kernel.** Read for a multi-dataset QSVR application and baseline design.[^30]
4. **Tscharke et al. — Anomaly Detection with Quantum SVR in the NISQ Era.** Read for IBM-hardware performance, noise-channel sensitivity, and adversarial failure modes.[^17]
5. **Stühler et al. — Evaluating QSVR Methods for Price Forecasting Applications.** Read for feature compression and comparison of multiple quantum-regression kernels.[^46]

### Quantum-kernel theory

6. **Havlíček et al. — Supervised Learning with Quantum-Enhanced Feature Spaces.** Foundational feature-map and kernel-estimation experiment.[^24]
7. **Schuld — Supervised Quantum Machine Learning Models Are Kernel Methods.** Formal kernel interpretation and encoding-centric viewpoint.[^25]
8. **Huang et al. — Power of Data in Quantum Machine Learning.** Essential caution about classical learnability and advantage claims.[^26]
9. **Thanasilp et al. — Exponential Concentration in Quantum Kernel Methods.** Explains concentration from encoding, entanglement, measurement, and noise, including limitations of generic mitigation.[^22]
10. **Training Quantum Embedding Kernels on Near-Term Quantum Computers.** Kernel-specific noise correction and regularization using known diagonal structure.[^31]
11. **Quantum-Efficient Kernel Target Alignment.** Nyström strategy for reducing quantum circuit execution.[^11]

### QEC and decoding

12. **IBM repetition-code tutorial.** Concrete Qiskit dynamic-circuit implementation and the cleanest starting code for a true-QEC extension.[^3]
13. **AlphaQubit.** Modern learned surface-code decoding and the role of simulation pretraining plus experimental fine-tuning.[^19]
14. **Tesseract decoder.** Search-based qLDPC decoding with Stim/DEM integration.[^32]
15. **IBM bivariate-bicycle code work and roadmap.** High-rate qLDPC motivation and the gap between current hardware experiments and future fault-tolerant systems.[^44][^42]
16. **Dynamic compass code on heavy-hex hardware.** Current evidence that contextual noise models, soft information, and leakage handling materially improve logical decoding.[^45]

## Research claims that would be defensible

Strong claims, if supported by repeated data:

- “Under a fixed QPU budget, method A improved QSVR RMSE relative to raw hardware kernels across three calibration blocks.”
- “Low-rank repair reduced negative spectral mass and improved exact-kernel alignment, with rank selected by training-only validation.”
- “Dynamical decoupling improved the kernel only for the deeper feature map, consistent with larger idle exposure.”
- “Twirling reduced block-to-block variance but did not improve mean regression error.”
- “A repetition-coded microkernel reduced bit-flip-induced overlap error but failed under composite hardware noise.”

Claims that would not be supported:

- “The QSVR is error corrected” when only PSD projection was used.
- “Quantum advantage” from beating one untuned classical SVR.
- “Hardware noise improves generalization” from one split or one calibration.
- “QEC improves QSVR” when an encoded basis-state memory replaces an arbitrary feature map.
- “The simulator validates hardware robustness” without leakage, drift, and crosstalk tests.

## Recommended thesis structure

1. **Introduction:** Define QSVR, QEC, mitigation, and the research gap.
2. **Theory:** Derive epsilon-SVR, fidelity kernels, shot variance, PSD conditions, and cost scaling.
3. literature:** Separate QSVR-on-noisy-hardware, quantum-kernel mitigation, and ML-for-QEC.
4. **Methods:** Data protocol, feature maps, noise channels, IBM hardware, suppression, and reconstruction.
5. **Simulation results:** Isolated channel effects and concentration diagnostics.
6. **Hardware results:** Blocked ablation, kernel spectra, predictive metrics, and cost.
7. **Logical extension:** Repetition-code microkernel with explicit limitations.
8. **Discussion:** Distinguish correction, mitigation, and regularization; analyze scaling and external validity.
9. **Reproducibility:** Release raw counts, circuits, configurations, matrices, and analysis code.

## Final assessment

The deepest defensible project is not “add QEC to QSVR” as a single software option. It is a layered study showing how physical error becomes kernel distortion, how that distortion propagates through a convex regressor, which interventions recover task-relevant geometry, and where true logical encoding becomes practical or counterproductive.

Current Qiskit and IBM hardware make the suppression-and-reconstruction study executable now. Full logical QSVR remains a research proposition because available QEC demonstrations protect restricted logical operations at substantial overhead, whereas ordinary QSVR feature maps use arbitrary data-dependent rotations and entanglers. The optional repetition-code experiment is still valuable precisely because it can quantify this mismatch rather than assuming fault tolerance solves it.

---

## References

[^1]: [i -QER: An Intelligent Approach towards Quantum Error Reduction](https://ar5iv.labs.arxiv.org/html/2110.06347)
[^2]: [Repetition codes | IBM Quantum Documentation](https://quantum.cloud.ibm.com/docs/ko/tutorials/repetition-codes)
[^3]: [Repetition codes | IBM Quantum Documentation](https://quantum.cloud.ibm.com/docs/en/tutorials/repetition-codes)
[^4]: [QSVR - Qiskit Machine Learning 0.9.1](https://qiskit-community.github.io/qiskit-machine-learning/stubs/qiskit_machine_learning.algorithms.QSVR.html)
[^5]: [Source code for qiskit_machine_learning.algorithms.regressors.qsvr](https://qiskit-community.github.io/qiskit-machine-learning/_modules/qiskit_machine_learning/algorithms/regressors/qsvr.html)
[^6]: [Quantum-assisted support vector regression - Quantum Information Processing](https://link.springer.com/article/10.1007/s11128-025-04674-0)
[^7]: [MIT Open Access Articles Quantum Support Vector ...](https://dspace.mit.edu/bitstream/handle/1721.1/90391/physrevlett.113.130503.pdf)
[^8]: [Quantum support vector machine for big data classification](https://arxiv.org/html/1307.0471v3)
[^9]: [FidelityQuantumKernel - Qiskit Machine Learning 0.9.1 - GitHub Pages](https://qiskit-community.github.io/qiskit-machine-learning/stubs/qiskit_machine_learning.kernels.FidelityQuantumKernel.html)
[^10]: [Qiskit Machine Learning 0.9.1 - GitHub Pages](https://qiskit-community.github.io/qiskit-machine-learning/)
[^11]: [Quantum-Efficient Kernel Target Alignment](https://arxiv.org/html/2502.08225v1)
[^12]: [FidelityStatevectorKernel - Qiskit Machine Learning 0.9.1](https://qiskit-community.github.io/qiskit-machine-learning/stubs/qiskit_machine_learning.kernels.FidelityStatevectorKernel.html)
[^13]: [qiskit_machine_learning.kernels.fidelity_quantum_kernel source](https://qiskit-community.github.io/qiskit-machine-learning/_modules/qiskit_machine_learning/kernels/fidelity_quantum_kernel.html)
[^14]: [Error mitigation and suppression techniques | IBM Quantum Documentation](https://quantum.cloud.ibm.com/docs/guides/error-mitigation-and-suppression-techniques)
[^15]: [Specify Sampler options | IBM Quantum Documentation](https://quantum.cloud.ibm.com/docs/en/guides/sampler-options)
[^16]: [Quantum Support Vector Regression for Robust Anomaly Detection](https://arxiv.org/html/2505.01012v1)
[^17]: [Anomaly Detection with Quantum SVR in the NISQ Era](https://arxiv.org/html/2505.01012v3)
[^18]: [Mitigating exponential concentration in covariant quantum kernels for subspace and real-world data](https://arxiv.org/html/2412.07915)
[^19]: [Learning high-accuracy error decoding for quantum processors](https://www.nature.com/articles/s41586-024-08148-8)
[^20]: [Generating A Simulator That Matches A Target Backend | Qiskit Aer](https://qiskit.github.io/qiskit-aer/tutorials/2_device_noise_simulation.html)
[^21]: [Exponentially tighter bounds on limitations of quantum error mitigation](https://pmc.ncbi.nlm.nih.gov/articles/PMC11473368/)
[^22]: [Exponential concentration in quantum kernel methods](https://arxiv.org/html/2208.11060v2)
[^23]: [Decision Kernels for Quantum Error Mitigation](https://arxiv.org/html/2607.02888v1)
[^24]: [Supervised learning with quantum-enhanced feature spaces](https://dspace.mit.edu/bitstream/handle/1721.1/133544/Harrow_EMB%20UNTIL%20DSept%2013,%202019_orig%20man,%20arXiv_Supervised%20learning%20with%20quantum-enhanced%20feature%20spaces.pdf)
[^25]: [Supervised quantum machine learning models are kernel methods](https://arxiv.org/abs/2101.11020)
[^26]: [Power of data in quantum machine learning](https://arxiv.org/abs/2011.01938)
[^27]: [Quantum support vector regression for disability insurance](https://www.econstor.eu/bitstream/10419/258298/1/risks-09-00216.pdf)
[^28]: [Quantum support vector machines for classification and regression on a trapped-ion quantum computer](https://link.springer.com/article/10.1007/s42484-024-00165-0)
[^29]: [Quantum support vector machines for classification and regression on a trapped-ion quantum computer (Preprint)](https://assets-eu.researchsquare.com/files/rs-3308876/v1_covered_f5f41903-f544-4a25-acfd-f72f5cb2de9c.pdf)
[^30]: [Semisupervised Anomaly Detection using Support Vector Regression with Quantum Kernel](https://arxiv.org/html/2308.00583)
[^31]: [Training Quantum Embedding Kernels on Near-Term Quantum Computers](https://arxiv.org/html/2105.02276v1)
[^32]: [quantumlib/tesseract-decoder: Search-based most-likely-error decoder](https://github.com/quantumlib/tesseract-decoder)
[^33]: [Sampler quickstart | IBM Quantum Documentation](https://quantum.cloud.ibm.com/docs/en/guides/get-started-with-sampler)
[^34]: [Qiskit Runtime client release notes | IBM Quantum Documentation](https://quantum.cloud.ibm.com/docs/en/api/qiskit-ibm-runtime/release-notes)
[^35]: [Migrate from server-side to client-side Sampler and Estimator](https://quantum.cloud.ibm.com/docs/en/guides/migrate-to-client-side-primitives)
[^36]: [Configure noise management with Sampler | IBM Quantum Documentation](https://quantum.cloud.ibm.com/docs/en/guides/sampler-noise-management)
[^37]: [Run jobs in a batch | IBM Quantum Documentation](https://quantum.cloud.ibm.com/docs/guides/run-jobs-batch)
[^38]: [Sampler (latest version) | IBM Quantum Documentation](https://quantum.cloud.ibm.com/docs/en/api/qiskit-ibm-runtime/executor-sampler-sampler)
[^39]: [Building Noise Models - Qiskit Aer 0.17.1](https://qiskit.github.io/qiskit-aer/tutorials/3_building_noise_models.html)
[^40]: [NoiseModel - Qiskit Aer 0.17.1](https://qiskit.github.io/qiskit-aer/stubs/qiskit_aer.noise.NoiseModel.html)
[^41]: [thermal_relaxation_error - Qiskit Aer 0.17.1](https://qiskit.github.io/qiskit-aer/stubs/qiskit_aer.noise.thermal_relaxation_error.html)
[^42]: [IBM lays out clear path to fault-tolerant quantum computing](https://www.ibm.com/quantum/blog/large-scale-ftqc)
[^43]: [IBM Quantum Computing | Hardware and roadmap](https://www.ibm.com/quantum/hardware)
[^44]: [Landmark IBM error correction paper on Nature cover | IBM Quantum Blog](https://www.ibm.com/quantum/blog/nature-qldpc-error-correction)
[^45]: [Scalable quantum error correction tailored for a heavy-hex qubit array](https://arxiv.org/html/2604.14296v2)
[^46]: [Evaluating Quantum Support Vector Regression Methods for Price Forecasting Applications](https://pdfs.semanticscholar.org/157d/7653419d5e0a761046c17aa27d10902d373f.pdf)

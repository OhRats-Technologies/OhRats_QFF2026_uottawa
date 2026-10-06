# QSVR with Qiskit: Literature and Performance Guide

## Executive answer

For getting the most from Qiskit’s Quantum Support Vector Regressor (QSVR), the literature points to a consistent priority order: **tune input scaling/quantum-kernel bandwidth first; tune SVR `C` and `epsilon` jointly; keep the feature map shallow; inspect and repair the Gram matrix under sampling noise; and compare against thoroughly tuned classical kernels under identical nested cross-validation**. Qiskit’s current `QSVR` is essentially scikit-learn `SVR` with a Qiskit `BaseKernel`; it accepts `C`, `epsilon`, and other SVR options through keyword arguments, and it also supports precomputed kernel matrices.[^1]

There is no strong evidence that deeper circuits or more qubits are generally better. A large benchmark of more than 20,000 quantum-kernel models found regularization and feature scaling more influential for regression than qubit or layer count, with no universal winner between QSVR and quantum-kernel ridge regression or between fidelity and projected kernels. The most reproducible gains come from making the kernel’s inductive bias fit the target—not merely increasing quantum-circuit expressivity.[^2][^3]

## Qiskit implementation

Qiskit Machine Learning provides `FidelityQuantumKernel`, `TrainableFidelityQuantumKernel`, `QuantumKernelTrainer`, and `QSVR`. The library’s fidelity kernel computes

$$
K(x,x')=|\langle\phi(x)|\phi(x')\rangle|^2,
$$

then passes that kernel to a classical support-vector optimizer; `QSVR` extends scikit-learn’s `SVR` rather than replacing its convex optimization stage.[^4][^1]

Useful operational details:

- `QSVR(quantum_kernel=qkernel, C=..., epsilon=...)` is the direct API.
- `QSVR(quantum_kernel="precomputed", C=..., epsilon=...)` accepts cached Gram matrices.
- Supplying `kernel=` is not supported by `QSVR`; use `quantum_kernel=` instead.[^1]
- `FidelityQuantumKernel(enforce_psd=True)` projects a square training Gram matrix to a positive-semidefinite matrix.
- `evaluate_duplicates="none"` avoids spending shots on entries that are known to equal one; `"off_diagonal"` fixes only the training diagonal and is the default.[^5]
- Qiskit’s published kernel-training tutorial uses a trainable fidelity kernel, `QuantumKernelTrainer`, SPSA, and SVM-margin alignment; the documented built-in example is classification-oriented, so regression alignment may require a custom `KernelLoss` or an external optimization loop.

A robust baseline pattern is:

```python
from sklearn.svm import SVR
from qiskit_machine_learning.kernels import FidelityQuantumKernel

qkernel = FidelityQuantumKernel(
    feature_map=feature_map,
    enforce_psd=True,
    evaluate_duplicates="none",
)

K_train = qkernel.evaluate(X_train_scaled)
K_valid = qkernel.evaluate(X_valid_scaled, X_train_scaled)

model = SVR(kernel="precomputed", C=C, epsilon=epsilon)
model.fit(K_train, y_train_scaled)
y_pred = model.predict(K_valid)
```

Precomputation is preferable during model selection because the expensive quantum evaluations can be cached and reused across the `C`/`epsilon` search. The training matrix has shape `n_train × n_train`, while prediction requires `n_test × n_train`.[^1]

## Priority reading list

| Priority | Publication | Why it matters for practice |
|---|---|---|
| 1 | **Schnabel & Roth, “Quantum Kernel Methods under Scrutiny: A Benchmarking Study”** (2025) | Most useful broad benchmark: 64 datasets, regression and classification, fidelity/projected kernels, nine encodings, and more than 20,000 optimized models. It identifies scaling, regularization, projected-kernel length scale, and measurement operators as the important controls.[^3] |
| 2 | **Suzuki, Hasebe & Miyazaki, “Quantum support vector machines for classification and regression on a trapped-ion quantum computer”** (2024) | Best hardware-oriented QSVR tuning paper. It combines shallow circuits, `epsilon`-SVR tuning, kernel alignment diagnostics, and eigendecomposition/SVD low-rank denoising; the paper reports optimal noisy-kernel ranks of 8 and 10 for its two regression datasets.[^6] |
| 3 | **Canatar et al., “Bandwidth Enables Generalization in Quantum Kernel Models”** (TMLR, 2023) | Explains theoretically why rescaling inputs can move a quantum kernel from non-generalizing to generalizing. It links bandwidth to Gram-spectrum decay and task-model alignment.[^2] |
| 4 | **Zhou et al., “Quantum kernel estimation-based quantum support vector regression”** (Quantum Information Processing, 2024) | QSVR-specific trainable-kernel paper. It proposes quantum-kernel alignment for regression and then inserts the trained kernel into classical SVR.[^7] |
| 5 | **Sahin et al., “Qiskit Machine Learning: an open-source library…”** (2025) | Current architectural overview of Qiskit ML, including QSVR, fidelity kernels, trainable kernels, primitives, simulators, and hardware execution.[^4] |
| 6 | **Wang et al., “Quantum Kernel Learning for Small Dataset Modeling in Semiconductor Fabrication”** (Advanced Science, 2025) | Concrete small-data QKAR example: shallow Pauli-Z feature map plus trainable alignment layer. Its ablation found the shallow aligned map better than more entangled alternatives on that task.[^8] |
| 7 | **Tscharke et al., “Semisupervised Anomaly Detection using Support Vector Regression with Quantum Kernel”** (2024) | Useful application study and cautionary hardware result. Simulated QSVR was competitive, but early hardware runs without substantial mitigation fell to chance-level AUC on two datasets.[^15] |
| 8 | **Stühler, Pranjić & Tutschku, “Evaluating Quantum Support Vector Regression Methods for Price Forecasting Applications”** (ICAART 2024) | Compares fidelity/projected QSVR, entanglement, re-uploading, categorical encoding, and autoencoder compression. It shows architecture and dimensionality reduction effects are dataset-dependent. |
| 9 | **Djehiche & Löfdahl, “Quantum support vector regression for disability insurance”** (2021) | Early QSVR hardware application with a domain-designed two-qubit map and weighted SVR. It is a good example of encoding known structure rather than choosing a generic feature map.[^9] |
| 10 | **Park et al., “Practical application improvement to Quantum SVM: theory to practice”** (2020) | Classification-focused but highly transferable: use shallow tunable transformations and regularization rather than assuming a fixed highly expressive map will work.[^10] |
| 11 | **Slattery et al., “Numerical evidence against advantage with quantum fidelity kernels on classical data”** (2023) | Essential skeptical control: bandwidth tuning can improve prediction while simultaneously making the quantum kernel closely approximable by a classical kernel.[^11] |

## What improves QSVR

### Tune bandwidth first

For rotation-based encodings, scaling inputs by a factor `s` changes the region of Hilbert space explored and therefore changes the quantum kernel’s effective bandwidth. Poor scaling commonly produces either an almost constant Gram matrix, which underfits, or an almost identity Gram matrix, which memorizes and generalizes poorly; bandwidth theory connects the useful middle regime to a non-flat spectrum and better target alignment.[^2]

Treat scaling as a model hyperparameter rather than a fixed preprocessing convention. A practical initial grid is logarithmic, for example:

```text
s ∈ {0.03, 0.06, 0.125, 0.25, 0.5, 1.0, 2.0}
```

Apply `StandardScaler` or a robust scaler inside each training fold, then multiply by `s`. If a map expects bounded angles, clip only after fitting the scaler on the training fold. The exact optimum is dataset- and circuit-dependent; theoretical and empirical studies show that an untuned default can be dramatically worse than a cross-validated bandwidth.[^12][^2]

### Tune SVR jointly

Search `C` and `epsilon` for every kernel configuration. The trapped-ion QSVR study found distinct optima—`(epsilon, C)=(0.21, 1.4)` for noisy financial data and `(0.0, 0.3)` for a materials dataset—and observed that larger `C` hurt rather than helped after a point.[^6]

A reasonable target-standardized search is:

```text
C       ∈ 10^{−3}, 10^{−2}, …, 10^{3}
epsilon ∈ {0, 0.01, 0.03, 0.1, 0.2, 0.5}
```

Scale `y` using training-fold statistics so that an `epsilon` value has a stable meaning. Include `epsilon=0` because some low-noise tasks prefer no insensitive tube, and inspect the fraction of support vectors: nearly every point becoming a support vector is often a warning of an overly narrow bandwidth, too-small `epsilon`, excessive `C`, or target noise.

### Prefer shallow maps

Start with one encoding repetition and linear or hardware-native entanglement. Add depth only if validation improves consistently across repeated splits. The broad benchmark found circuit layers and qubit count less important than regularization and scaling for its regression datasets, while a small-data semiconductor study found a shallow Pauli-Z map with a simple alignment layer superior to more entangled variants.[^3][^8]

Evaluate at least these controlled ablations:

- Unentangled angle map.
- Linear-nearest-neighbor entanglement.
- Full entanglement only for very small dimensions.
- One versus two re-uploading repetitions.
- Fidelity kernel versus a projected kernel, if projected observables can be implemented cleanly.

Do not select a circuit on training error or kernel expressibility alone. Highly expressive fidelity kernels can exhibit concentration, near-identity Gram matrices, poor sample efficiency, and worse shot requirements.[^11][^3]

### Align to regression targets

For regression, the useful target kernel is based on centered continuous targets rather than class labels. Given centered `y`, a basic target Gram matrix is

$$
K_y = yy^T,
$$

and centered kernel-target alignment can be optimized as

$$
A_c(K,K_y)=\frac{\langle HKH,HK_yH\rangle_F}{\|HKH\|_F\,\|HK_yH\|_F},
\qquad H=I-\frac{1}{n}\mathbf{1}\mathbf{1}^T.
$$

Optimize alignment only on the inner-training fold, then freeze the circuit before validation. Zhou et al. explicitly propose regression-oriented quantum-kernel alignment, and later small-data QKAR work reports gains from adding a shallow trainable alignment layer.[^8][^7]

Alignment is a screening diagnostic, not the final objective. Select the model by out-of-fold MAE/RMSE or domain loss because high global alignment can still overweight outliers, ignore heteroscedasticity, or exploit leakage.

### Diagnose the Gram matrix

For every fold and kernel candidate, log:

- Symmetry error: `||K-K.T||F / ||K||F`.
- Diagonal deviation from one.
- Minimum eigenvalue and negative-eigenvalue mass.
- Condition number after regularization.
- Effective rank, for example `(tr K)^2 / tr(K^2)`.
- Off-diagonal median, interquartile range, and saturation near zero or one.
- Centered alignment with `yy.T`.
- Number/fraction of support vectors.
- Prediction sensitivity across shot seeds or hardware sessions.

These diagnostics separate three failure modes: **constant-kernel collapse**, **identity-kernel memorization**, and **indefinite/noisy-kernel corruption**. The broad benchmark links poor regimes to overfitting and ill-conditioned Gram matrices, while bandwidth theory explains why an excessively flat spectrum undermines sample-efficient generalization.[^3][^2]

### Repair sampled kernels

On shot-based simulation or hardware:

1. Exploit symmetry and evaluate only one triangle of the training matrix.
2. Set the diagonal exactly to one when justified.
3. Symmetrize with `(K + K.T)/2`.
4. Project the training matrix to the positive-semidefinite cone; Qiskit can do this with `enforce_psd=True`.[^5]
5. If noise dominates small spectral components, test truncated eigendecomposition for training and consistent truncated SVD for train-test matrices.
6. Select rank within training data, preferably by inner-CV prediction or stability—not with inaccessible noiseless test information.

Suzuki et al. selected rank by alignment to a noiseless reference and improved real-device QSVR, but that reference may not exist in a production-scale problem. Their result is best treated as evidence that spectral denoising works, while practical rank selection should use training-fold criteria such as held-out RMSE, eigengap stability, or repeated-shot consistency.[^6]

### Allocate shots adaptively

The cost of a full training kernel is quadratic in sample count. Begin with a low-shot pilot to reject collapsed feature maps and bad bandwidths, then increase shots only for finalists. Qiskit’s duplicate-handling options can skip known entries, and precomputed matrices prevent repeated quantum calls while searching `C` and `epsilon`.[^5][^1]

For large datasets, compare:

- Nyström landmarks selected only from the training fold.
- Rank-revealing pivoted Cholesky.
- Subsampled alignment training.
- Support-vector-aware refinement after a low-shot initial fit.

Any approximation must be evaluated against both predictive error and total circuit executions; otherwise a nominally better model may simply consume substantially more quantum resources.

## Recommended protocol

### Stage A: classical controls

Use repeated or nested cross-validation with leakage-safe preprocessing. Tune linear, polynomial, RBF, and Matérn-like classical kernels over budgets at least as large as the QSVR search. Report MAE, RMSE, `R²`, uncertainty across splits, fit/prediction time, and—separately—quantum circuit executions.

This step is essential because tuned quantum fidelity kernels can become geometrically similar to classical RBF or low-order polynomial kernels. Good QSVR accuracy alone is not evidence of quantum advantage.[^13][^11]

### Stage B: noiseless screening

For each circuit family:

1. Search input bandwidth `s`.
2. Search one to four shallow repetitions, stopping early when concentration or validation degradation appears.
3. Cache each fold’s Gram matrix.
4. Search `C` and `epsilon` using only cached matrices.
5. Reject candidates with collapsed spectra or unstable split-to-split performance.

The main benchmark explored one to eight circuit layers but found scaling and regularization generally more consequential for regression.[^3]

### Stage C: aligned kernels

Take only the best one or two static maps and add a small trainable layer. Optimize centered regression alignment or a custom validation surrogate with SPSA or another noise-tolerant derivative-free method. Qiskit’s kernel trainer supports trainable feature-map parameters and defaults toward SPSA-style optimization because analytic gradients are not generally available for its kernel loss workflow.[^14]

Use multiple initializations and stop when alignment improves but held-out error no longer does. Trainable kernels add another overfitting channel, especially when the number of circuit parameters is not small relative to the training set.

### Stage D: noisy execution

Run the finalists with progressively realistic conditions:

- Finite-shot ideal simulator.
- Backend-derived noise model.
- Transpiled hardware-native circuits.
- Real hardware across more than one calibration window.

Record raw and repaired kernels. Compare PSD projection alone against PSD plus low-rank truncation. The trapped-ion results show that a shallow three- or four-qubit QSVR can remain useful after denoising, but `R²` still fell from 0.932 to 0.868 on financial data and from 0.703 to 0.628 on materials data relative to noiseless quantum kernels.[^6]

## Suggested search budget

| Component | Initial search | Expanded search only if useful |
|---|---|---|
| Input bandwidth | 7 logarithmic values | Local log-scale refinement |
| Feature map | Z/angle, ZZ-linear, one domain map | Projected kernel or trainable map |
| Repetitions | 1, 2 | 3, 4 only with stable spectra |
| Entanglement | None, linear | Circular/full for small `d` |
| `C` | `10^-3` to `10^3` | Local refinement |
| `epsilon` | 0 to 0.5 on standardized `y` | Refine around best value |
| Shots | Low-shot pilot | Increase until ranking stabilizes |
| Spectral rank | Full, PSD-only, several eigengap ranks | Inner-CV rank sweep |

This staged design avoids the common mistake of spending the quantum budget on circuit-depth searches before optimizing the far more influential bandwidth and SVR regularization controls.[^3]

## Interpretation cautions

- **Prediction gain is not quantum advantage.** The quantum kernel must also be hard to reproduce classically, and tuned fidelity kernels often become classically approximable.[^11][^13]
- **Tiny datasets inflate variance.** Report repeated splits and confidence intervals, not the best split.
- **PCA and scaling must be fitted inside each fold.** Several application papers use aggressive dimensionality reduction because qubits are scarce; reproductions should avoid preprocessing on the full dataset.
- **Simulation success may not transfer.** Anomaly-detection QSVR studies found competitive simulation results but large early-hardware degradation without sufficient mitigation.[^15]
- **Noise is not reliable regularization.** Hardware noise can occasionally improve a dataset by chance, but QSVR studies also show strong sensitivity to amplitude damping, calibration errors, and adversarial perturbations.
- **Domain-aware encoding is more defensible than generic depth.** The disability-insurance work designed a two-qubit map around age and sex structure, illustrating how inductive bias can be built into the circuit rather than discovered through brute-force depth.[^9]

## Best practical recipe

For a new regression problem, begin with standardized inputs, standardized targets, a one-repetition linear-entangled map, and a precomputed fidelity kernel. Jointly tune the input multiplier, `C`, and `epsilon`; inspect the kernel spectrum and support-vector fraction; compare against nested-CV RBF SVR; and only then test trainable alignment, projected kernels, additional layers, or hardware execution. Under noise, symmetrize, fix justified diagonal entries, enforce PSD, and test low-rank truncation selected strictly inside training data.[^1][^5][^6][^3]

The strongest current evidence supports QSVR as a useful experimental kernel-learning framework for small, structured datasets—not as a default replacement for classical SVR. The models perform best when the quantum feature map supplies a task-specific inductive bias that cannot be obtained simply by making the circuit more expressive.[^2][^11]

For a detailed analysis of hardware noise channels, Sampler error suppression (DD, twirling), classical Gram matrix repair (PSD, low-rank, Higham), and why QSVR is not a real-time QEC decoder, see [Deep Technical Study: QSVR, Quantum-Device Errors, and Qiskit/IBM Quantum](QSVR_QEC_ERROR_STUDY.md).

---

## References

[^1]: [QSVR - Qiskit Machine Learning 0.9.1 - GitHub Pages](https://qiskit-community.github.io/qiskit-machine-learning/stubs/qiskit_machine_learning.algorithms.QSVR.html)

[^2]: [Bandwidth Enables Generalization in Quantum Kernel ...](https://arxiv.org/html/2206.06686v3)

[^3]: [Quantum Kernel Methods under Scrutiny: A Benchmarking Study](https://arxiv.org/html/2409.04406)

[^4]: [Qiskit Machine Learning: an open-source library for quantum ...](https://arxiv.org/pdf/2505.17756.pdf)

[^5]: [FidelityQuantumKernel - Qiskit Machine Learning 0.9.1](https://qiskit-community.github.io/qiskit-machine-learning/stubs/qiskit_machine_learning.kernels.FidelityQuantumKernel.html)

[^6]: [Quantum support vector machines for classification and ...](https://arxiv.org/abs/2307.02091) - Quantum machine learning is a rapidly growing field at the intersection of quantum computing and mac...

[^7]: [Quantum kernel estimation-based quantum support vector regression](https://link.springer.com/article/10.1007/s11128-023-04231-7) - Quantum machine learning endeavors to exploit quantum mechanical effects like superposition, entangl...

[^8]: [Quantum Kernel Learning for Small Dataset Modeling in ...](https://pmc.ncbi.nlm.nih.gov/articles/PMC12462921/) - Modeling complex semiconductor fabrication processes such as Ohmic contact formation remains challen...

[^9]: [Quantum support vector regression for disability insurance](https://arxiv.org/abs/2109.01570) - We propose a hybrid classical-quantum approach for modeling transition probabilities in health and d...

[^10]: [Practical application improvement to Quantum SVM](https://arxiv.org/pdf/2012.07725.pdf) - by JE Park · 2020 · Cited by 88 — QSVM could include improved analytical performance (e.g., improved...

[^11]: [Numerical evidence against advantage with quantum fidelity kernels on classical data](https://arxiv.org/html/2211.16551v1)

[^12]: [Importance of Kernel Bandwidth in Quantum Machine Learning](https://www.arxiv.org/pdf/2111.05451.pdf)

[^13]: [On the similarity of bandwidth-tuned quantum kernels and ...](https://arxiv.org/html/2503.05602v1)

[^14]: [QuantumKernelTrainer#](https://qiskit-community.github.io/qiskit-machine-learning/locale/hi_IN/stubs/qiskit_machine_learning.kernels.algorithms.QuantumKernelTrainer.html)


[^15]: [Semisupervised Anomaly Detection using Support Vector Regression with Quantum Kernel](https://arxiv.org/abs/2308.00583) — Kilian Tscharke, Sebastian Issel and Pascal Debus (2023 preprint).

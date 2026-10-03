# Q-SIGReg: independent feasibility audit

**Verdict:** implementable as a finite-feature anti-collapse regularizer; not a distribution-identifying replacement for SIGReg. The suggested four-qubit circuit cannot guarantee isotropic Gaussian embeddings. The pilot supports running a small controlled training study, not claiming superiority or quantum advantage.

## Mathematical audit

Write rho(x) = |phi(x)><phi(x)|. Fidelity is k(x,y) = Tr[rho(x)rho(y)], hence

MMD_k(P,Q)^2 = || E_P rho(X) - E_Q rho(Y) ||_F^2.

This is positive semidefinite and differentiable for the proposed smooth feature map. It can detect higher-order discrepancies invisible to ordinary covariance. However, a fixed n-qubit map has only 4^n real density-matrix coordinates (one fixed by trace). Four qubits supply at most 255 varying features. No choice of depth makes this finite feature set characteristic over arbitrary continuous distributions.

Adding mean and covariance supplies only finitely many additional constraints. This still cannot identify a Gaussian. For example, partition Gaussian space into more positive-probability sets than the number of constraints, then choose a nonzero bounded piecewise-constant h orthogonal, under the Gaussian measure, to 1, every density coordinate, x_j and x_j*x_k. Linear dependence guarantees such h. For sufficiently small epsilon, q(x)=p_G(x)(1+epsilon*h(x)) is a different nonnegative normalized distribution with exactly the same quantum feature mean, mean, and covariance. This argument establishes non-identifiability even relative to the exact Gaussian, not merely between arbitrary distributions.

The numerical pilot constructs a finite-support version: reweighting 512 Gaussian samples onto 270 support points changes total variation by 0.544, but preserves the density mean and first/second raw moments within 1.70e-13. Quantum MMD squared is 1.94e-26; a fixed classical RBF kernel yields 5.36e-5. These numerical values concern empirical measures, not equality to the population Gaussian.

A D-to-4 projection head also constrains only its four-dimensional output, not isotropy of the full D-dimensional encoder representation. “Projection-free” should mean no random one-dimensional slices, not no projection head. Canonical SIGReg can resample directions across training updates, so observing finite slices in one batch is not by itself a decisive disadvantage.


There is a positive anti-collapse argument: for a completely collapsed representation, rho_Z is pure, so its squared discrepancy from a fixed target density rho_G is at least 1 + Tr(rho_G^2) - 2*lambda_max(rho_G). This is positive whenever the target is mixed. The three empirical Gaussian targets give lower bounds 0.7139 to 0.7405 over every pure state (including states unreachable by the feature map). Thus the loss penalizes complete collapse mathematically; this does not guarantee optimization escapes a stationary point, outweighs the JEPA term, prevents partial collapse, or identifies Gaussianity.

## Circuit and gradient checks

The exact four-qubit map is H, RY(theta_j), RZ(theta_j), a CZ ring, shifted RY(theta_(j+1)), and another CZ ring. Theta=(pi/2)tanh(z), with scale s=1 in this pilot. Both embeddings and Gaussian reference samples receive the same transformation.

- Independent vectorized states agree with Qiskit Statevector states to machine precision; pair-circuit all-zero probabilities agree with overlap fidelities.
- The terminal common CZ ring cancels between U(y)^dagger and U(x). Removing it changes no kernel values; the earlier ring still matters.
- SamplerQNN with input_gradients=True produces input-angle gradients. At 16,384 shots, maximum error against exact central finite differences is about 6.49e-4 for one sampled pair.
- The measured forward/backward cost is 49 bindings per pair: one forward and 48 parameter-shift evaluations, because eight distinct inputs appear in 24 parameterized gates. Naively evaluating all 16 pairs with all input derivatives costs 784 bindings per quantum update. This is a measured implementation count, not a lower bound: reference-reference terms need no encoder gradient, Gaussian-reference derivatives need not all be computed, batching/reuse can help, and exact simulator autodiff can avoid shot-based parameter shifts.
- StatevectorSampler defaults to 1,024 shots; it is sampled, despite its name. For deterministic debugging use exact statevectors or an explicitly differentiable state simulator. This audit verifies SamplerQNN directly; TorchConnector and encoder backpropagation were not executed because Torch was absent when this independent audit started.

Tanh limits ordinary angular wrapping, but does not prove that the entire feature map is injective or characteristic. Its derivatives saturate at large magnitudes; scale s is a meaningful hyperparameter.

## Distribution pilot

Three seeds, 384 samples per distribution, exact fidelities; the following are means across seeds. RBF bandwidth is sqrt(4), fixed before results, not tuned against quantum performance.

| Distribution | Quantum unbiased MMD squared | Bq=8 paired-estimator standard deviation |
| --- | ---: | ---: |
| Independent Gaussian | 0.00067 | 0.152 |
| Complete collapse at zero | 0.806 | 0.109 |
| Near-collapse, std 0.01 | 0.805 | 0.107 |
| Independent +/-1 coordinates | 0.0296 | 0.183 |
| Uniform radius-2 sphere | 0.00346 | 0.155 |
| Variance-one Student-t(3) | 0.0112 | 0.154 |

Sphere and independent signs are isotropic in population but non-Gaussian. The quantum kernel detects some discrepancies, while their small signals are overwhelmed by individual Bq=8 updates. These standard deviations are from 2,000 paired draws per case from empirical distributions, before hardware shot noise. They concern loss-value noise; gradient variance was not measured. Negative unbiased estimates are legitimate: do not clamp them to zero and silently change the objective.

## Tiny synthetic optimization

An affine four-dimensional encoder is optimized from A=0.01 I with a two-view consistency penalty on 128 Gaussian inputs. Six losses are run across three seeds with L-BFGS-B capped at 60 iterations. Independent held-out Gaussian inputs evaluate covariance and classical RBF-MMD. Exact density-feature means implement quantum MMD against a fixed reference sample; this is not the proposed intermittent linear-time shot-based training implementation.

| Regularizer | Mean held-out minimum covariance eigenvalue | Mean feature std | Held-out biased RBF-MMD squared |
| --- | ---: | ---: | ---: |
| None | 4.5e-11 | 0.000021 | 0.1622 |
| Moments | 0.6413 | 0.9717 | 0.00853 |
| Classical RBF-MMD | 0.6274 | 0.9273 | 0.00836 |
| Quantum MMD | 0.4405 | 0.8368 | 0.01213 |
| Quantum MMD + moments, iteration-capped | 0.6417 | 0.9709 | 0.00827 |

Quantum-only optimization escapes near-collapse in all three seeds. It does not outperform the simpler classical alternatives on this check. Quantum-plus-moments hits the iteration cap in all three runs, so its similar final numbers are not converged comparisons. The sixth variant is a fixed-direction Epps-Pulley kernel proxy, not the canonical resampled SIGReg implementation; all its runs hit the cap. Its raw results are retained but not used to claim superiority over SIGReg. There is no downstream linear probe, nonlinear encoder, canonical LeJEPA training, hardware run, or calibrated hyperparameter comparison here. Relative effective rank can look reasonable even at essentially zero covariance, so absolute variance must also be reported.

## Recommended scope

Keep moments on the full classical training batch. Treat Q-MMD as an experimental finite-feature supplement, and compare against covariance, classical RBF and a classical finite-feature kernel of similar dimension. Four to eight qubits are cheap to simulate (16 to 256 amplitudes), so no computational quantum advantage is established. Test larger quantum batches or exact mean-density training before relying on four noisy pairs; distinguish hardware evaluation from training.

If a characteristic distribution discrepancy is required, add an RBF component with positive weight; characteristic behavior then comes from the classical component. A finite collection of more quantum circuits alone remains finite-feature. Increasing the family indefinitely needs a separate consistency argument.

Kernel regularization for JEPA already has relevant prior work: [KerJEPA](https://arxiv.org/abs/2512.19605). The contribution would be an evaluated choice of quantum feature map, not inventing distribution-MMD regularization or avoiding slicing for the first time. See [LeJEPA](https://arxiv.org/abs/2511.08544), [MMD linear-time estimators](https://www.jmlr.org/papers/v13/gretton12a.html), and [SamplerQNN documentation](https://qiskit-community.github.io/qiskit-machine-learning/stubs/qiskit_machine_learning.neural_networks.SamplerQNN.html).

Run `uv run python scripts/q_sigreg_audit.py`. Evidence and weights are under `artifacts/q-sigreg-audit-20261003/`; tests independently reload the collision, compare Qiskit states, check the density-mean identity, and enumerate the paired-estimator expectation. This is a time-boxed feasibility audit, not a performance claim.

## Verification status at handoff

The audit and existing repository passed 74 tests before concurrent integration of the other agent's Torch/Q-SIGReg implementation. After integration, this audit's four tests and the implementation's nine tests pass in separate processes (the latter includes TorchConnector backpropagation). Whole-repository discovery in one process terminated with native exit 139 at an Aer Kraus test; the root cause is unverified. This integration failure is recorded on the board and needs diagnosis before describing the combined suite as passing. It does not replace the separate module checks or extend this pilot into a full LeJEPA experiment.

# Classical bottleneck repair and quantum entanglement lifetime

Restoring T4a_R's outgoing counts after threshold-1,000 pruning nearly restores the intact graph's subdominant eigenvalue, but **does not restore its entanglement-breaking index**. Only restoring Y3_R and T4a_R together among all 28 two-row interventions restores the original index. These are exact certificates for the specified coarse population channel, not biological timescales.

| Intervention | Raw-P subdominant modulus | T4a_R escape probability | Exact EB index |
| --- | ---: | ---: | ---: |
| Intact | 0.853469 | 0.095013 | 7 |
| Pruned, then row-normalized | 0.871768 | 0.075544 | 8 |
| Removed probability held as self-loops | 0.879154 | 0.073953 | 8 |
| Restore T4a_R outgoing row | 0.853374 | 0.095013 | 8 |
| Restore Y3_R and T4a_R outgoing rows | 0.854487 | 0.095013 | 7 |

The classical diagnostic uses P. The composed quantum channel E = 0.6 Id + 0.4 D_P has population transition M = 0.6 I + 0.4 P. These are distinct matrices; the saved Dobrushin coefficients use M raised to the indicated step.

## What was checked

The experiment enumerates intact and pruned graphs, a removed-mass-to-self-loop control, every single-row restoration (8), every two-row restoration (28), and three targeted edge restorations. All 42 interventions have matching exact rational lower and upper EB certificates: a negative partial-transpose determinant at the preceding step and a nonnegative product-mixture residue at the claimed EB step.

All eight single-row restorations retain index 8. Of the 28 pairs, only Y3_R + T4a_R has index 7. At step 7, the pruned graph's only numerically negative partial-transpose pair is Pm4_R / T4a_R. Restoring its two direct outgoing edges (13 and 8 contacts), separately or together, still leaves index 8. Thus restoring the direct witness edges is insufficient; multi-step transition paths matter. This does not identify a unique causal pathway.

Fifteen local six-qubit density-matrix simulations explicitly apply the noisy Kraus channel to half of three Bell pairs, at steps 6, 7 and 8 for five contrasts. Their normalized Choi matrices agree with the analytic expression after accounting for Qiskit's register order. These are local channel simulations, not hardware runs or estimates from a unitary walk.

## Interpretation and limits

The pruning slowdown is consistent with the first paper's boundary-trap motivation. The more useful quantum insight is the controlled mismatch: nearly restoring one classical spectral diagnostic is insufficient to restore the quantum EB threshold. This complements the existing isospectral controls; it does not show that classical and quantum behavior are unrelated.

These interventions are exploratory. The targeted witness edges were selected after inspecting the pruned model; all one- and two-row combinations are reported to avoid selecting only a favorable result. Threshold 1,000 is aggressive for this induced eight-population graph. Row normalization conditions on retained connections, while the self-loop control retains the original outgoing denominators; neither represents measured physiology. Gamma = 0.6 is an assumed retention parameter. No full-CNS replication, biological quantum computation, quantum advantage, or universal pruning theorem is claimed.

Run `uv run python -m flybrain.pruning_mechanisms`. Results, rational certificates, circuit comparisons and source hashes are saved under `artifacts/pruning-mechanisms-20261003/`. The focused tests reload representative certificates, verify intervention coverage and mass conservation, and independently check Kraus-circuit register ordering.

# Numerical stability of the kernel comparison

This numerical diagnostic uses individual-fire classification scores, not annual aggregate predictions. [Scope correction](SCOPE_CORRECTION.md).

**ZZ landmark rankings depend substantially on solver tolerance.** The failed [landmark screen](QUANTUM_LANDMARKS.md) remains a valid measured outcome under its frozen defaults, but its AP loss cannot be attributed entirely to discarded kernel information. This training-only diagnostic reproduces the default predictions, then checks fixed tighter tolerances without selecting one by best AP.

## Fixed check

[Plan](../experiments/kernel_convergence.json), recipe commit `fc2a68c`: same 256/256 fires, seeds 811/821/823, four inputs, encoding, C=1 and landmark ridge as the parent. Dense RBF/ZZ and ideal ZZ 8/16/32; tolerances 1e-3, 1e-6, 1e-9; maximum 100,000 solver iterations. No new pair circuits, shots, hardware or test-year access. **54 fits**, **1,536 exact-state preparations**, **2.01 seconds** including imported diagnostic dependencies and reconstruction, excluding interpreter startup, preflight and prior acquisition.

The [SVC documentation](https://scikit-learn.org/stable/modules/generated/sklearn.svm.SVC.html) identifies tolerance as an optimization stopping criterion, not a bound on prediction errors. We record the primal/dual gap, KKT residual, score spread, iteration count and fit status. A known-margin fixture verifies the objective calculations; a constant-kernel majority-class fixture verifies a legitimate degenerate optimum.

## Results

| Kernel | Mean AP · 1e-3 | 1e-6 | 1e-9 |
|---|---:|---:|---:|
| Dense RBF | .4110 | .4114 | .4114 |
| Dense ZZ | .3930 | .4036 | .4029 |
| ZZ · 8 landmarks | .3008 | .3203 | .2278 |
| ZZ · 16 landmarks | .2560 | .3694 | .3276 |
| ZZ · 32 landmarks | .2728 | .3792 | .3608 |

The tighter columns are **diagnostic outputs, not uniformly converged estimates**. Iteration-limited fits: **0/18** at 1e-3, **6/18** at 1e-6 and **12/18** at 1e-9. All three RBF samples converge and change AP by less than .002; no RBF sample crosses the fixed .02 sensitivity threshold. Nine of the 15 kernel/seed default-to-tight comparisons cross it; all involve ZZ. Only six of 15 tight kernel/seed fits satisfy both the convergence flag and the frozen 1e-5 duality-gap check.

At 16 landmarks, linear and explicitly precomputed representations of the **same** shared-feature kernel agree within **3.4e-12** at the tight setting. This argues against a train/cross representation mismatch as the cause. Their agreeing iteration-limited answers still do not certify the optimum.

Several small-landmark ZZ score spreads shrink toward **1e-7** at the tight setting, while rankings continue to change. An almost constant negative decision function can yield apparently useful AP from tiny differences; AP does not certify useful separation or calibrated risk. Some larger-landmark/dense ZZ cases retain nonzero spread, so this finding is not a blanket statement that every quantum ranking is arbitrary.

The installed scikit-learn version is 1.9.1. Its [libsvm source](https://github.com/scikit-learn/scikit-learn/blob/1.9.1/sklearn/svm/src/libsvm/svm.cpp) caches Q-matrix entries as `float` (`Qfloat`) even though input matrices are double precision. That is a relevant numerical limitation, but this audit does not isolate cache precision from degeneracy, conditioning or the shrinking heuristic. More iterations alone are not an established remedy.

## Decision

Keep the original failed promotion and negative shot comparisons. Do not select the most favorable tolerance, relabel these samples as confirmation or reinterpret simulator scores as quantum advantage. The subsequent separately frozen [kernel-ridge comparison](KERNEL_RIDGE.md) tests a smooth objective on the same ideal inputs, using double-precision solves, residual checks and matched RBF/linear controls. It remains an incident-label study. The next project priority is the missing annual macro baseline, not another numerical variant.

## Evidence and reproduction

[Audited outputs](results/kernel-convergence.json) retain every kernel/tolerance/representation, parent-prediction reproduction, saved metric checks and comparison thresholds. The collector recomputes metrics and score spreads; solver objectives/KKT diagnostics come from the committed runner and are not independently recomputed here. Shared chronological years and previously inspected features remain exploratory.

```sh
uv run --no-sync python scripts/run_convergence_screen.py
uv run --no-sync python scripts/collect_convergence.py
```

Exclusive ignored intents refuse overwriting an existing diagnostic. Collection performs no fitting. The frozen [final report](FINAL_EVALUATION.md) is unchanged; this is a numerical warning for future comparisons, not a retrospective final-test rerun.

# Does better QUBO energy mean better prediction?

This surrogate alignment audit concerns incident classification. No analogous alignment experiment was run for macro annual prediction. [Scope correction](SCOPE_CORRECTION.md).

**The surrogate is informative in five samples but unreliable at its optimum. Better quantum optimization cannot, by itself, fix that mismatch.** This training-only diagnostic follows the [constrained-selector study](CONSTRAINED_SELECTION.md); it changes no frozen final model.

## Fixed comparison

Reuse its six capped cohorts: 256 training fires from 1988–2014 and 256 validation fires from 2015–2018 per sample. Keep the eight inputs, training-only median/standard scaling, saved relevance/redundancy/cardinality QUBO and fixed logistic C=1. Enumerate **all 70 four-feature subsets** in integer-mask order and fit one identical predictor per subset. The [plan](../experiments/proxy_alignment.json) was committed at `b36f7cc` before execution, with a 420-fit/120-second cap. No new selector fits, quantum calls, hardware jobs or final-test access occur.

Spearman correlation compares **negative energy** with validation AP, so a positive value means lower energy broadly accompanies higher AP. AP midrank percentiles include half the tied subsets; higher is better. Every cohort has one objective optimum here.

| Cohort seed | Energy/AP Spearman | Exact AP | Exact AP percentile | L1 AP | Descriptive maximum AP |
|---|---:|---:|---:|---:|---:|
| 811 | .488 | .3286 | 90.7 | .3070 | .3731 |
| 821 | .413 | .3445 | 60.7 | .3998 | .5914 |
| 823 | .268 | .2256 | 62.1 | .2256 | .3553 |
| 907 | .708 | .3765 | 50.7 | .4158 | .4642 |
| 911 | .307 | .4476 | 53.6 | .4599 | .5321 |
| 919 | −.144 | .2122 | 49.3 | .2137 | .4321 |

## Interpretation

The proxy has a useful broad association in five cohorts, but its exact optimum lies near the middle of the predictive ranking in three. In seed 919 the association reverses. The optimum falls .0446–.2469 AP below the descriptive maximum. L1 beats the exact optimum in four cohorts, ties in one and loses in one, despite its higher QUBO energy in five. Reaching the exact optimum therefore certifies this objective, not predictive optimality.

This is expected from a marginal-relevance/pairwise-redundancy surrogate: it does not directly optimize a regularized logistic model's held-out AP. The measured magnitude and sampling dependence are useful project evidence, not a new theoretical discovery. It qualifies the [SQD](QISKIT_FOLLOWUP.md#sqd-and-feature-selection) result: SQD can return the sampled minimum yet still select a weaker predictive subset. It also explains why preserving QAOA cardinality does not establish useful selection.

The maximum over 70 validation scores is an **oracle envelope on reused years**, not a newly selected baseline, unbiased performance estimate or promotion. All samples overlap in years; no p-values, confidence intervals or independent temporal confirmation are claimed. Do not choose the validation winner, retune the QUBO or reopen 2019–2024. Retain the diagnostic and prune further circuit optimization without a separately justified modelling objective.

## Coefficient stability

Predictive misalignment and objective sensitivity are different questions. From the same 70 stored energies, we can determine when an exact optimum stops being unique under additive **linear-coefficient** perturbations, with all pair coefficients fixed. For optimum `b*`, Hölder's inequality bounds each competitor's energy gap by its original gap minus the perturbation norm times its Hamming distance. The unrestricted first-tie radius is

$$
\rho_a=\min_{b\ne b^\star: \sum_j b_j=4}
\frac{E(b)-E(b^\star)}{\lVert b-b^\star\rVert_1},
\qquad \rho_r=4\rho_a.
$$

Every perturbation strictly inside `rho_a` preserves the unique optimum among feasible four-feature subsets. At the boundary, perturbing each changed coordinate opposite to the competitor's inclusion difference constructs a tie. Since relevance contributes `-r_j/4` to the linear coefficient, `rho_r` expresses the same bound in relevance units. This keeps the cardinality and redundancy terms fixed.

| Seed | Minimum energy gap | Linear radius `rho_a` | Relevance-equivalent radius `rho_r` |
|---|---:|---:|---:|
| 811 | .037148 | .018574 | .074295 |
| 821 | .062349 | .031175 | .124699 |
| 823 | .024228 | .012114 | .048455 |
| 907 | .015313 | .007656 | .030625 |
| 911 | .001218 | .000609 | .002437 |
| 919 | .018489 | .009244 | .036977 |

Seed 911 has a much smaller margin than seed 821. That does **not** establish that mutual-information errors exceed either bound. No estimator was refitted and no statistical uncertainty was measured. Perturbations are unrestricted; witnesses need not retain relevance in `[0,1]` with maximum one, as re-estimated normalized MI would. Thus the radius is a deterministic fixed-objective guarantee, not an empirical error bar or a measurement of actual data-induced flips. A stable surrogate can still be predictively weak; neither margin nor exact energy certifies AP.

The [six certificates](results/qubo-stability.json) hash-link the public energies and retain constructive tie witnesses. All 70 masks are checked, every source optimum remains unique strictly inside its radius, and each witness displaces it just outside the boundary. Three toy checks cover a known two-state radius, existing ties and a farther-energy competitor with a smaller radius. The latter matters because the runner-up energy gap alone is insufficient in general. Floating-point checks use 1e-12 tolerance; these are not formal interval-arithmetic certificates. No private data, fitting, quantum calls or new cache runner is involved.

Reproduce the radii and boundary witnesses from public evidence:

```sh
uv run --no-sync python - <<'PY'
import hashlib, json
from pathlib import Path
import numpy as np
source = Path('docs/results/proxy-alignment.json').read_bytes()
saved = json.loads(Path('docs/results/qubo-stability.json').read_text())
assert hashlib.sha256(source).hexdigest() == saved['source_sha256']
for cohort, reference in zip(json.loads(source)['seeds'], saved['certificates']):
    states = np.array([row['state'] for row in cohort['rows']])
    energy = np.array([row['energy'] for row in cohort['rows']])
    bits = ((states[:, None] >> np.arange(8)) & 1).astype(float)
    best = energy.argmin()
    distance = np.abs(bits - bits[best]).sum(axis=1)
    other = distance > 0
    radius = np.min((energy[other] - energy[best]) / distance[other])
    assert np.isclose(radius, reference['linear_coefficient_linf_radius'], rtol=0, atol=1e-12)
    shifted = energy + bits @ np.array(reference['witness_linear_perturbation'])
    witness = np.flatnonzero(states == reference['first_tie_witness_state'])[0]
    assert shifted.min() >= shifted[best] - 1e-12
    assert abs(shifted[witness] - shifted[best]) < 1e-12
    print(cohort['seed'], radius, 4 * radius)
PY
```

## Evidence and collection

The run took **.9509 seconds** for 420 converged predictor fits. Collection took **.5252 seconds**, reconstructed every stored prediction/metric and exactly reproduced the prior exact/L1 references within 1e-9. Fitting, objective fitting and quantum state preparation were patched to fail during collection. Three focused fixtures check exhaustive coverage, tied percentiles, incomplete/tampered outcomes and collection without fitting. [Public evidence](results/proxy-alignment.json) records all subset metrics; ignored per-example predictions and coefficients remain in the exclusive cache. Prior data, caches, credentials and hardware records are preserved.

```sh
uv run --no-sync python scripts/proxy_alignment.py collect
```

Do not reset the completed intent. For a replica, follow [pinned reproduction](REPRODUCIBILITY.md) in a separate checkout/cache. This diagnostic adds no new kernel, circuit or algorithm.

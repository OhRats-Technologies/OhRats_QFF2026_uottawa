# Does local kernel geometry preserve predictions?

These ridge predictions fit binary incident labels, not actual hectares or annual averages. No macro prediction or continuous fire-size regression follows from the result. [Scope correction](SCOPE_CORRECTION.md).

**At α=.01, the circuit-derived classical tangent kernel closely preserves exact ZZ ridge rankings; at wider angles it does not.** RBF has the highest mean AP in these matched samples. This is an encoding interpretation and useful classical control, not a new algorithm or quantum advantage.

The [frozen protocol](../experiments/tangent_prediction.json), opening `982d6b8`, follows the [labels-free geometry diagnostic](LOCAL_GEOMETRY.md). It reuses its fixed metric and all twelve exact matrices. Same three seeds (811/821/823), 256 training and 256 validation rows per sample, four bounded inputs, train 1988–2014 and validate 2015–2018. These samples reuse years and are dependent. No final-test access or angle selection occurs. [Evidence](results/tangent-prediction.json) includes every condition and audit certificate.

## Matched objective and controls

Ordinary linear, training-median RBF, tangent and all inherited ZZ scales use training-only kernel centering and unit mean diagonal. Ridge minimizes **sum** squared error with λ=1, labels −1/+1 and the training-mean intercept. This reproduces the previous [ridge control](KERNEL_RIDGE.md), rather than substituting an SVM or changing normalization.

The tangent features are bG½, where b is the already bounded transformed input and G is the fixed circuit-derived real quantum geometric tensor. The common Taylor amplitude cancels under unit-variance normalization. A four-dimensional explicit primal solve verifies the dual result. This is linear in transformed inputs, not raw geography. G comes from the circuit, not label fitting.

| Predictor | AP: seed 811 | AP: 821 | AP: 823 | Mean AP |
|---|---:|---:|---:|---:|
| Ordinary linear | .28559 | .45138 | .34900 | .36199 |
| RBF | .29735 | .56719 | .36116 | **.40857** |
| Classical tangent | .28308 | .45400 | .34239 | .35982 |
| Exact ZZ, α=.01 | .28904 | .46921 | .35000 | .36942 |
| Exact ZZ, α=.05 | .29550 | .53689 | .36625 | .39955 |
| Exact ZZ, α=.10 | .30879 | .55203 | .34408 | .40163 |
| Exact ZZ, α=.50 | .19919 | .37560 | .33485 | .30321 |

No mean selects a new model. RBF exceeds every ZZ scale on mean AP, but not every individual condition: seed 811's .10 ZZ exceeds its RBF control. Report this variation rather than claiming a universal ordering.

## Narrow-angle closeness and its limits

Before fitting, the .01 protocol required mean absolute AP difference ≤.02, every seed ≤.03 and every prediction Spearman ≥.99. **All three operational checks pass.** They are practical tolerances, not a statistical equivalence test or an AP guarantee from kernel resemblance.

| ZZ scale versus tangent | Mean absolute AP difference | Largest seed AP difference | Minimum prediction Spearman | Mean prediction RMSE |
|---|---:|---:|---:|---:|
| .01 | **.00960** | .01521 | **.99840** | .00794 |
| .05 | .03972 | .08289 | .93631 | .06371 |
| .10 | .04181 | .09803 | .86819 | .10240 |
| .50 | .05661 | .08389 | .40140 | .18311 |

At .01, exact ZZ exceeds tangent AP in all three samples by .00596/.01521/.00761, while their centered prediction L2 differences are 3.17–5.71% relative to exact predictions. High rank correlation does not mean identical precision-recall behavior. At .05/.10, nonlinear residuals matter more; .50 is outside this local approximation. This agrees with the earlier matrix geometry, but labels and ridge now supply an actual predictive check.

## Deterministic certificate

Let Ke/Kt be centered normalized exact/tangent training kernels, Be/Bt their cross-kernels, and at the tangent ridge coefficients. Their intercepts agree. The resolvent identity gives

$$
a_e-a_t=(K_e+\lambda I)^{-1}(K_t-K_e)a_t.
$$

Consequently,

$$
\lVert f_e-f_t\rVert_2\le
\left[\frac{\lVert B_e\rVert_2\lVert K_t-K_e\rVert_2}
{\lambda_{\min}(K_e+\lambda I)}+\lVert B_t-B_e\rVert_2\right]\lVert a_t\rVert_2.
$$

All twelve comparisons satisfy this bound, **but it is far too loose to certify useful closeness**. At .01 its upper bounds are 2,043–2,404 versus measured L2 differences .0785–.1576. The generic worst-direction norm bound does not exploit coefficient/kernel alignment. The operational conclusion comes from reconstructed predictions and fixed tolerances, not this inequality. No AP bound is claimed.

## Verification, cost and decision

The runner takes **.320s**, with 21 dual predictor solves and six explicit-feature primal reference solves. It adds **zero states, pair circuits, shots or hardware jobs**. Collection takes **.452s** and recomputes kernels/metrics/coefficient equations without solving or preparing states; the recorded audit succeeds with both operations patched to fail. Prior linear/RBF/.05 ZZ metrics match within 1e-9. Maximum solve residual is 2.92e-15 and primal/dual prediction difference 4.67e-15. Interpreter startup and opening-recipe checks are excluded; source reconstruction is included.

Two disposable fixtures verify the bound, reconstruction without solving and rejection of changed coefficients/predictions. Four pipeline-status fixtures pass. Frozen parent hashes and every stored coefficient remain in the ignored lineage.

```sh
uv run --no-sync python scripts/collect_tangent_prediction.py
```

Keep the tangent control and the local geometry/noise explanation. Prune further angle/depth sweeps and promotion from these reused-year samples. The narrow regime combines a simple four-feature classical approximation with poor relative finite-shot signal; widening adds nonlinear differences without a mean RBF advantage here. Preserve `.cache/wildfire/tangent-prediction` and the final evidence. This closes the specific approximation question without changing the frozen final model.

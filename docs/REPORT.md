# Ontario annual wildfire regression

Development and frozen reused-year findings · October 5, 2026 · Qiskit Fall Fest open challenge. Scientific deliverables were published before **5 PM Toronto**; the deadline review is closed. Models use **1988–2018 training** and **2019–2024 reused evaluation**.

**No main climate model beats the training-mean baseline on the six reused years.** Four-input QSVR beats matched RBF there, but both miss the large annual swings; ten-qubit predictions are nearly constant. RBF leads chronological development. Quantum feature selection supplies no consistent benefit across predictors. The contribution is an audited macro dataset and a reproducible negative comparison, not demonstrated forecasting skill or quantum advantage.

## Question and observation unit

Can classical or quantum selection and kernels estimate **Ontario annual mean agency-reported fire size**, in hectares per size-observed incident? Each province-year is one observation: **31 training years, 1988–2018**. Mean size, total reported hectares and incident count are distinct quantities. This study predicts the annual mean; it is neither individual-fire classification nor ignition forecasting.

The source-specific annual rules retain incidents without precise daily dates, coordinates or nearby weather stations. They include **39,616 size-observed NFDB Ontario fires**, compared with 37,801 in the geographically selected older classifier cohort. Unknown/negative size is excluded from the size denominator rather than recorded as zero. Source coverage does not establish a complete census or final burned area. [Annual table](data/annual_training.csv) · [schema](DATA_SCHEMA.md) · [source rules and plan](../experiments/annual_qsvr.json).

ECCC station-month data supply ten climate summaries. Annual mean temperature needs at least nine measured months; annual totals/extremes need twelve; spring/summer summaries need all three months. Eligible station-years receive equal weight. All ten predictors exist for every training year, but station counts vary **65–340**, depending on feature/year. Equal station weighting is not provincial area weighting. Same-year full climate gives **retrospective annual estimation**, not an advance forecast.

## Design

Outer chronological validation blocks are 2007–2010, 2011–2014 and 2015–2018, each preceded by an expanding training window. Three expanding inner splits choose parameters. Every fit estimates its imputer, input standardization and log1p target standardization from its training window only. Predictions are inverse-transformed to nonnegative hectares. Reported MAE/RMSE are mean outer-fold errors; twelve development years are reused across comparisons, not independent replications.

Baselines include training mean/median, a year trend, ridge, linear SVR and RBF-SVR. The matched kernel comparison gives **36 candidate configurations per family, input width and outer fold**, selected by inner MAE: RBF bandwidth multipliers .25/1/4/16 or four quantum maps, each crossed with C=.1/1/10 and epsilon=.05/.2/.5. Epsilon is tolerance in standardized log-target space; it is not a hardware-noise correction.

The actual [FidelityQuantumKernel API](https://qiskit-community.github.io/qiskit-machine-learning/stubs/qiskit_machine_learning.kernels.FidelityQuantumKernel.html) computes state overlaps. Cached matrices feed actual [QSVR](https://qiskit-community.github.io/qiskit-machine-learning/stubs/qiskit_machine_learning.algorithms.QSVR.html), whose solver extends classical SVR; a fixture verifies equivalence to sklearn precomputed SVR.

For a training-standardized climate feature $z_j$, encode

$$\theta_j=a\tanh(z_j/2),\qquad k_q(x,y)=|\langle\phi(x)|\phi(y)\rangle|^2.$$

A four- or ten-qubit linear ZZ feature map uses single-feature and pairwise phase terms, with one/two repetitions and amplitude $a\in\lbrace\pi/4,\pi/2\rbrace$. Entangling gates enable circuit interactions; they do not guarantee useful meteorological interactions or better prediction. Exact local compute-uncompute simulation is the reference. No hardware was used.

## Matched development results

| Model | Inputs | MAE (ha/fire) | RMSE (ha/fire) |
|---|---:|---:|---:|
| Training mean | 0 | 92.00 | 116.05 |
| Linear year trend | 0 | 88.91 | 120.62 |
| Ridge, tuned | 10 | 81.21 | 116.85 |
| Matched RBF-SVR | 4 | **77.02** | **106.74** |
| Matched QSVR | 4 | 86.64 | 120.30 |
| Matched RBF-SVR | 10 | 81.00 | 115.26 |
| Matched QSVR | 10 | 81.86 | 115.39 |

The apparent best individual four-qubit map (74.57 MAE) is not a fair selected-family result. Inner validation selects another map; the equal-budget result favors RBF. Four-qubit QSVR wins the first outer fold and loses two; ten-qubit QSVR loses all three by small margins. The bandwidth refinement followed initial development inspection, so it is adaptive development, not independent confirmation. [All initial maps](ANNUAL_QSVR.md) · [matched receipt](results/annual-matched.json).

![Development predictions and annual denominators](figures/annual-development/annual-development.png)

Both families miss the exceptionally large 2011 mean. Annual provincial summaries and log-target regression smooth a highly variable response. Low average error cannot be presented as reliable extreme-fire prediction.

![Matched errors](figures/annual-development/annual-matched.png)

## Selection and SQD

Eight selectors use one fixed ridge predictor, common annual training windows and three sensitivity seeds. Except the explicit all-ten control, each selects four inputs. Continuous-target mutual information supplies relevance; absolute correlations supply redundancy. The QUBO penalizes incorrect cardinality. [Plan](../experiments/annual_selectors.json) · [complete results](results/annual-selectors.json).

| Selector | Mean fold/seed MAE (ha/fire) |
|---|---:|
| Exact classical QUBO | 79.58 |
| Uniform bitstring sampling | 80.31 |
| QAOA sampling | 81.66 |
| Mutual-information ranking | 82.79 |
| Lasso ranking | 89.22 |
| Physical four | 89.78 |
| Random four | 90.61 |
| All ten | 102.00 |

This table compares selectors with **fixed ridge alpha=1**, not tuned kernels. QAOA uses depth one, 40 optimizer evaluations and 512 synthetic draws per fold/seed. All optimizers reach their bounded evaluation cap; no convergence is claimed. Uniform sampling has a slightly worse surrogate-energy gap than QAOA but lower prediction error. Better surrogate optimization does not ensure better regression.

Actual qiskit-addon-sqd projection and diagonalization recover the best sampled energy to numerical precision. This objective is diagonal, with only **210 feasible four-of-ten subsets**. SQD therefore adds no optimization beyond choosing the lowest-cost sampled subset; exhaustive classical enumeration is the natural control. We retain the demonstration and prune SQD advantage claims.

## What the ablations teach

| Fixed four-input climate condition | Ridge MAE | RBF MAE | QSVR MAE |
|---|---:|---:|---:|
| Same-year measured-month control | 89.78 | 85.19 | 90.39 |
| Same-year zero missing-day counts | 79.56 | 76.51 | 79.62 |
| Previous-year climate | 88.19 | 89.76 | 82.51 |
| Training-only station roster | 84.62 | 85.56 | 83.48 |

Data quality changes errors more than the matched ten-qubit/classical difference. Zero missing-day counts improve all three fixed models; unknown counts remain excluded. This is a sensitivity, not complete source certification. Prior-year inputs address a different horizon, while source publication latency remains unresolved. We retain the original same-year recipe for the primary comparison. [Context receipt](results/annual-context.json).

A fixed official Ontario boundary now masks NRCan previous-year land-cover maps for all training years. The 1 km equal-area estimate includes water/other classified classes and explicitly excludes unclassified/nodata cells. A 500 m probe changes treed/water fractions by less than .03 percentage points, with no uncovered province cells. This is coarse sampled class area, not exhaustive 30 m area, tree density or biomass. Historical temporal processing remains retrospective. [Woodland table](data/annual_training_cover.csv) · [boundary source](https://geo.statcan.gc.ca/geo_wa/rest/services/2021/Digital_boundary_files/MapServer/0) · [woodland receipt](results/annual-woodland.json).

Adding mapped treed fraction worsens fixed ridge/RBF error (98.50/94.29 versus 89.78/85.19). Fixed QSVR improves to 84.59, but adding calendar year alone gives 85.51 and both additions use five qubits. This does not establish a forest-specific gain; do not promote the lowest-looking ablation.

![Kernel similarity diagnosis](figures/annual-development/annual-kernel-similarity.png)

Across outer maps, mean validation/training fidelity is **.07576 at four qubits versus .001002 at ten**. Ten-qubit training matrices are nearly identity, with effective rank essentially equal to the training count. This measured loss of cross-year similarity explains the nearly unchanged ten-qubit predictions; more qubits do not automatically add useful information.

## Frozen 2019–2024 evaluation

All settings and learned states were [published before evaluation](ANNUAL_FINAL.md). The final runner computes predictions from saved coefficients, support weights and scalers: **zero predictor fits during evaluation**. These six years overlap the inspected incident branch; they are reused evaluation, not a pristine holdout.

| Model | MAE (ha/fire) | RMSE (ha/fire) | Bias (ha/fire) |
|---|---:|---:|---:|
| training mean | 276.81 | 336.12 | -205.34 |
| linear year trend | 286.58 | 353.63 | -233.16 |
| ridge 10 | 294.98 | 372.24 | -261.27 |
| matched rbf svr 4 | 299.81 | 380.52 | -272.74 |
| matched fidelity svr 4 | 280.68 | 352.51 | -250.92 |
| matched rbf svr 10 | 309.25 | 382.01 | -265.45 |
| matched fidelity svr 10 | 298.99 | 380.05 | -271.00 |

QSVR improves on matched RBF by **19.13 ha/fire at four inputs** and **10.26 at ten**, yet loses to the train-mean control. The family ordering differs from development. Six shared years support descriptive paired errors, not a significance claim. All eleven main models underestimate on average.

![Annual reused-year predictions](figures/annual-final/annual-reused-predictions.png)

Observed annual means range from 9.34 to 656.99 ha/fire, versus training means of 3.73–477.72. The six-year mean is 329.97; the training-mean constant is 124.63. Same-year climate summaries, varying station coverage and log-target compression are candidate contributors to failure; this experiment does not separate their causal effects. Inverse log transformation includes no mean-bias correction. Neither changing the target nor retuning from these errors is allowed.

![Every reused-year error](figures/annual-final/annual-reused-errors.png)

The fixed **eight selectors × three predictors × three seeds** crossover is complete. Mutual-information ridge averages 276.67 MAE, only 0.14 below the constant. QAOA loses to exact/uniform selection with ridge but slightly improves on those controls with QSVR; no consistent selector advantage emerges. All combinations, repeated-subset seeds and the different-budget all-ten control are in [final notes](ANNUAL_FINAL.md).

Selected ten-qubit eigenvalues span **0.980–1.028**, condition number **1.049**, effective rank **30.998/31**, and cross-year fidelity **.000899**. Predictions span just **57.98–59.60** ha/fire. The matrix is stable but nearly identity: numerical conditioning alone cannot certify predictive usefulness. Its saved zero-cross intercept predicts 59.01 ha/fire; actual similarity-weighted contributions change this by just -1.03 to +0.59. Narrow-bandwidth RBF4 also stays near its 57.51 intercept (-5.06 to +2.70). [Audited algebraic decomposition](results/annual-kernel-signal.json). All 24 unique final kernel spectra and PSD/concentration checks are [published](results/annual-final-audit.json). The [guide adoption table and future protocols](ANNUAL_FINAL.md#guide-adoption-and-deferral) cover scale tuning, alignment and sampled repair; they are not unrun improvements disguised as results.

A separately frozen **post-final input-only bandwidth probe** makes that caveat concrete. With the same ten input features and one ZZ repetition, pi/4 → pi/32 changes training mean fidelity .000805 → .538897 and effective rank 30.998 → 5.187. Four-input rank falls to 2.190, with condition number 4.58e7: eliminating identity-like similarity can instead approach a poorly conditioned, near-constant regime. No targets, test rows or predictors were used; no scale was selected. This supports the guide’s geometry mechanism, not improved regression. Ten matrices cost 4,650 additional analytic pair circuits / 48.89 s. The original 83 predictions/24 kernels still audit unchanged. [Diagnostic and replication commands](ANNUAL_BANDWIDTH_GEOMETRY.md) · [expanded 145-test/69-CLI QA](data/annual_bandwidth_repository_checks.json).

## Cost and verification

Four/ten-qubit development screens took **10.58/193.17 s**, running concurrently; these are not isolated throughput benchmarks. Classical preparation/fitting took .89/.29 s, matched classical exploration .45 s, selectors 2.41 s, context checks 4.05 s and province-cover processing/ablation 316.02 s. Interpreter startup/acquisition and QA refits are separate costs. All quantum measurements were simulated.

The [annual evidence audit](results/annual-evidence-audit.json) reproduces the table byte-for-byte, checks 171 metric records and replays 18 classical/24 cached-QSVR fits without new quantum states. The first collector required a correction to use each runner's exact float input path; its failed record remains preserved. Expanded verification passed **142 tests / 68 CLI help paths** at 3fae875. Clean-clone public collection reproduces all 83 final predictions and 24 matrix diagnostics without fits/new states; the existing pinned venv was reused. [QA](data/annual_final_repository_checks.json) · [portability](data/annual_portability_receipt.json). Historical 130/64 counts remain tied to their original snapshot.

Four bounded annual follow-up plans are complete: matched bandwidth budgets, continuous-target selectors, climate context, and province-masked woodland. We prune extra architecture search. This is a proposal/evaluate/prune workflow, not full Dream-RSI policy evolution. The earlier independent policy-code study concerns the incident branch only.

Final training/evaluation took **93.75/9.63 s**, with 12,092/2,232 analytic fidelity-pair circuits respectively, 36 training quantum matrices, 80 final learned predictor fits and zero evaluation fits. Selector sampling is synthetic and its cost is separate. The 80 fit count covers sklearn/QSVR fits; the calendar trend adds one polynomial fit and two constants are deterministic summaries. The [final no-fit audit](results/annual-final-audit.json) reproduces 83 predictions and 24 matrix pairs. A [267 kB evidence package](data/annual_final_evidence.zip) supports collection without raw downloads or credentials. [Source/table checks](data/annual_table_reaggregation.json), [304 rounded table values](data/annual_reporting_audit.json), [local source and figure integrity](data/annual_source_integrity.json), and [GitHub/document checks](data/annual_document_checks.json) pass. The [handoff](HANDOFF.md) is complete; board review closed at 5 PM. Test reuse, small annual sample, network/reporting changes, retrospective sources, extreme-year error and ideal simulation remain explicit limitations.

[Run commands and detailed evidence](ANNUAL_QSVR.md) · [current goal](../GOAL.md) · [earlier scope correction](SCOPE_CORRECTION.md) · [preserved incident findings](FINAL_EVALUATION.md).

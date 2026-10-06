# Annual Ontario wildfire regression · active study

Owner-authorized run on October 5, 2026 through **5 PM Toronto**. [Goal and timeline](../GOAL.md) · [frozen plan](../experiments/annual_qsvr.json).

**Primary task:** estimate annual mean agency-reported fire size (hectares), one Ontario year per example. Train 1988–2018, validate chronologically inside those years, then evaluate 2019–2024 as explicitly reused years. Climate predictors are same-year station summaries: this is retrospective annual estimation, not an advance fire forecast. Annual totals and counts are retained with denominators, not conflated with mean size.

## Milestones

| Milestone | Status |
|---|---|
| Frozen annual target, source rules and bounded budgets | Committed plan |
| Audited annual table and classical baseline results | Complete: 31 annual rows / 27 outer comparison records |
| Matched four/ten-feature RBF-SVR and QSVR | Complete: equal 36-candidate inner selection per family/width |
| Justified small ablations / selectors | Continuous-target selectors measured; climate checks running |
| Frozen reused-test evaluation | Pending |
| Verified figures, concise report and handoff | Due 5 PM |

QSVR uses FidelityQuantumKernel overlaps and a classical SVR solver. Small chronological grids tune C and epsilon; scaling, imputation and target transforms are fitted inside every fold. Fixed circuits are compared under equal input/tuning budgets. Exact simulation comes first. No hardware job is planned.

Annual fire aggregation does not require the old classifier’s station-distance, exact-date or buffer eligibility. Unknown size remains outside the size-observed denominator, not zero hectares. Climate station weighting and coverage counts stay explicit. The acquired woodland bounding crop is not an Ontario mask; a provincial cover statistic cannot be derived by calling all crop pixels Ontario. Climate/fire baselines will proceed before any woodland work delays them.

The [earlier scope correction](SCOPE_CORRECTION.md) describes what was missing at 1:51 PM; it is historical, not a claim about future progress. Saved incident results remain separate. This page will be updated with actual outcomes and runnable commands as implementation finishes.

## First measured milestone · 2:10 PM Toronto

The 31-row annual training table and classical development screen are complete. Labels include **39,616 size-observed source incidents**, without the old classifier’s coordinate/date/weather-distance exclusions. All ten climate features have measurements in all 31 years; eligible station counts vary substantially (65–340 depending on feature/year). Equal station weighting is not spatial area weighting. Annual means range from 3.73 to 477.72 reported hectares per fire.

[Saved classical evidence](results/annual-classical.json) records all 27 outer comparison records, nested chronological tuning, actual/predicted yearly hectares, source/table/plan hashes and timing. Data preparation took .89 s and classical fitting .29 s, excluding interpreter startup. Development uses 12 validation years in three chronological blocks, not independent replications.

| Model | Inputs | Mean outer-fold MAE (ha/fire) | Mean outer-fold RMSE (ha/fire) |
|---|---:|---:|---:|
| linear | 4 | 100.51 | 127.05 |
| linear | 10 | 83.03 | 112.61 |
| linear_year_trend | 0 | 88.91 | 120.62 |
| rbf | 4 | 81.73 | 101.15 |
| rbf | 10 | 85.67 | 116.40 |
| ridge | 4 | 90.55 | 127.96 |
| ridge | 10 | 81.21 | 116.85 |
| training_mean | 0 | 92.00 | 116.05 |
| training_median | 0 | 92.64 | 122.86 |

The four-input RBF and ten-input ridge controls improve on the training-mean baseline in average fold MAE. This is development evidence, not final-test performance or a robust generalization claim. Four- and ten-qubit actual FidelityQuantumKernel/QSVR screens completed in separate caches. Each fixed circuit uses the same nine C/epsilon choices as SVR; four circuit configurations are reported separately, so their exploration cost must not be hidden when comparing with the one-bandwidth RBF baseline. A matched bandwidth-budget check will precede any quantum promotion.

Six focused tests pass: macro size denominators, station weighting/coverage, unknown-year targets, fold-local scaling, actual fidelity API/state-overlap agreement and QSVR/precomputed-SVR equivalence. No new test-year results or hardware jobs have been accessed.

```sh
uv run --no-sync python scripts/run_annual_regression.py --output .cache/wildfire/annual-qsvr/my-new-classical-run
uv run --no-sync python scripts/run_annual_quantum.py --dataset .cache/wildfire/annual-qsvr/development-v2/data/annual.csv --output .cache/wildfire/annual-qsvr/my-new-quantum-4-run --qubits 4
```

Use a new output directory; preserve existing records. The first v1 dataset omitted all-zero audit columns; v2 makes them explicit without changing outcomes or predictive inputs. Both records remain preserved.

## Four-qubit development complete

Actual FidelityQuantumKernel/QSVR completed all 12 outer circuit/fold comparisons in **10.58 seconds**, including inner kernels and SVR tuning, excluding interpreter startup and prior data acquisition. [Saved outcome](results/annual-quantum-4.json). The ten-qubit outcome is reported below.

| Circuit repetitions | Angle amplitude | Mean fold MAE (ha/fire) | Mean fold RMSE (ha/fire) |
|---|---:|---:|---:|
| 1 | 0.785 | 83.61 | 120.81 |
| 1 | 1.571 | 86.64 | 120.30 |
| 2 | 0.785 | 76.73 | 121.48 |
| 2 | 1.571 | 74.57 | 98.30 |

Report all four circuit configurations; do not compare only the best quantum map with one untuned classical bandwidth and call that a fair win. Exact simulation and three chronological development blocks do not establish hardware advantage or independent replication.

## Ten-qubit development complete

The ten-qubit FidelityQuantumKernel/QSVR screen completed all 12 outer circuit/fold comparisons in **193.17 seconds**, including inner kernels/tuning and excluding interpreter startup. [Saved outcome](results/annual-quantum-10.json). Both widths are now measured; no annual test results were accessed.

| Circuit repetitions | Angle amplitude | Mean fold MAE (ha/fire) | Mean fold RMSE (ha/fire) |
|---|---:|---:|---:|
| 1 | 0.785 | 81.74 | 115.39 |
| 1 | 1.571 | 82.17 | 115.74 |
| 2 | 0.785 | 81.86 | 115.51 |
| 2 | 1.571 | 81.93 | 115.47 |

Ten features/qubits do not automatically improve the result. These settings have similar development errors between 81.74 and 82.17 ha/fire; the four-qubit settings vary more. The next mandatory check is matched classical bandwidth exploration before selecting a final configuration. All outcomes remain exploratory development evidence.

## Equal-budget comparison · 2:30 PM

[Matched receipt](results/annual-matched.json) · [frozen refinement](../experiments/annual_matched.json). Each family receives 36 candidate settings per width/fold: four kernel settings crossed with the same nine C/epsilon choices. Configuration selection uses inner chronological MAE, never the outer errors. This refinement followed inspection of initial development results; it is not an independent replication.

| Family | Inputs | Mean fold MAE (ha/fire) | Mean fold RMSE |
|---|---:|---:|---:|
| RBF-SVR | 4 | 77.02 | 106.74 |
| Fidelity QSVR | 4 | 86.64 | 120.30 |
| RBF-SVR | 10 | 81.00 | 115.26 |
| Fidelity QSVR | 10 | 81.86 | 115.39 |

The apparent best-map quantum improvement disappears under matched selection. Four-input QSVR wins the earliest outer fold and loses the other two. Ten-input results are close, but QSVR has higher MAE in each fold. We retain all initial maps rather than publishing a selected best-looking result. This check adds 654 classical fits (.45 s); it reuses measured quantum kernels.

## Continuous-target selection

[Selector receipt](results/annual-selectors.json) · [frozen plan](../experiments/annual_selectors.json). Eight selectors share one fixed ridge predictor (alpha=1), the same annual training windows, and three sensitivity seeds. All-ten has a different input budget; the other selectors choose four of ten climate inputs. Relevance uses continuous-target mutual information and redundancy uses absolute correlation. Seeds reuse the same twelve validation years; they are not independent datasets.

| Selector | Mean fold/seed MAE (ha/fire) |
|---|---:|
| Exact QUBO | 79.58 |
| Uniform bitstring sampling | 80.31 |
| QAOA bitstring sampling | 81.66 |
| Mutual information ranking | 82.79 |
| Lasso ranking | 89.22 |
| Physical four | 89.78 |
| Random four | 90.61 |
| All ten | 102.00 |

This is a feature-selection comparison, not the tuned kernel comparison above. QAOA used 360 optimizer objective calls, nine final sampling states and nine reconstruction states, with 4,608 synthetic draws; no device was used. Optimizer termination hit the bounded budget, so the selected subset is a measured feasible sample, not a convergence certificate. The all-ten objective includes the four-feature cardinality penalty; its saved objective gap must not be interpreted as a feasible-selector quality gap.

Actual qiskit-addon-sqd projection/diagonalization returned the minimum sampled diagonal-QUBO energy (numerical agreement within 1e-9). With no off-diagonal Hamiltonian terms, this is mathematically equivalent to choosing the lowest-cost sampled subset. It demonstrates SQD applicability but supplies no new optimization or prediction gain. The full selector experiment took 2.41 s, excluding startup.

## Climate coverage and information checks

[Context receipt](results/annual-context.json) · [frozen plan](../experiments/annual_context.json). These checks use physical four inputs and fixed settings (ridge alpha=1; RBF/QSVR C=1, epsilon=.2; quantum reps=1, amplitude=pi/2). They isolate aggregation/information changes rather than repeat the tuned model search.

| Climate condition | Ridge MAE | RBF MAE | QSVR MAE |
|---|---:|---:|---:|
| Same-year measured-month control | 89.78 | 85.19 | 90.39 |
| Same-year zero missing-day counts | 79.56 | 76.51 | 79.62 |
| Prior-year climate | 88.19 | 89.76 | 82.51 |
| Same-year training-only station roster | 84.62 | 85.56 | 83.48 |

Errors are mean outer-fold hectares per fire. A zero missing-day count is required for the sensitivity, including exclusion of unknown counts. It improves all three fixed models here, but is not a comprehensive source quality certificate. Training-only roster sizes are 98, 67 and 55 stations; eligible-year coverage changes even within these rosters. All condition tables have every predictor in every training year. Previous-year inputs change the information horizon; historical source products still do not establish real-time availability.

These are reused development comparisons. We will not select the lowest-error condition and present it as an independently validated gain. The primary matched study keeps its originally declared same-year aggregation.

## One front door

The annual workflow is available through the existing pipeline. Preview first, then add `--execute` to run into a new directory:

```sh
uv run --no-sync python scripts/pipeline.py annual matched --output .cache/wildfire/annual-qsvr/my-new-matched-run
uv run --no-sync python scripts/pipeline.py annual quantum --qubits 10 --output .cache/wildfire/annual-qsvr/my-new-ten-qubit-run --execute
```

`classical` prepares raw-source annual data and controls; `quantum`, `matched`, `selectors` and `context` use explicit annual inputs. Matched selection requires the pinned published quantum parent receipts. None of these development operations opens test years or submits hardware.

## Province-masked woodland

[Woodland receipt](results/annual-woodland.json) · [annual table with cover](data/annual_training_cover.csv) · [frozen plan](../experiments/annual_woodland.json). Existing NRCan maps for 1987–2017 now provide previous-map context for every 1988–2018 training year. The official [Statistics Canada province layer](https://geo.statcan.gc.ca/geo_wa/rest/services/2021/Digital_boundary_files/MapServer/0) supplies Ontario geometry, used as a fixed retrospective mask. It is not an added predictive measurement source.

Nearest-neighbor samples on a 1 km EPSG:6933 equal-area grid estimate classified cover fractions. This is a coarse spatial approximation, not exhaustive native 30 m class area. Treed codes are 81/210/220/230; the denominator includes water and other classified land and excludes 0/255. The 1987 500 m probe differs by at most **0.0002903** in treed/water fraction; no masked cell is outside source coverage in any year. Unclassified cells remain explicit (10.51% of the mask in 1987). The estimated classified treed share rises 63.65% to 67.56%; this mapped trend does not establish a causal biological change. Temporal source processing is retrospective, even with map year t-1.

The complete aggregation and fixed model ablation took **316.02 s**. A calendar-year control checks whether adding a slowly varying quantity alone changes results:

| Physical four plus… | Fixed ridge MAE | Fixed RBF MAE | Fixed QSVR MAE |
|---|---:|---:|---:|
| Nothing | 89.78 | 85.19 | 90.39 |
| Calendar year | 97.80 | 92.69 | 85.51 |
| Previous-map treed fraction | 98.50 | 94.29 | 84.59 |

These are the same fixed predictor settings as the climate checks. The forest addition worsens both classical controls; QSVR improves, but only slightly beyond the calendar-year addition and with five rather than four qubits. We do not promote this as forest-specific or quantum gain. The accepted 2022 source cutoff remains explicit; this training-only check does not fabricate 2023–2024 maps.

## Reproduction and kernel diagnosis

[Evidence audit](results/annual-evidence-audit.json) re-created the 31-row training table byte-for-byte, recomputed 171 result metrics and replayed 18 classical / 24 cached-QSVR fits with saved settings. No new quantum state or test target was accessed. Reproduction fits are QA, not new scientific replications. The first audit exposed an input-parity error: classical fits had consumed pre-serialization floats and quantum fits parsed CSV. The corrected audit follows each original input path and reproduces predictions; both audit attempts remain in ignored caches.

Across twelve outer matrices per width, mean validation/training fidelity is **0.07576** at four qubits and **0.001002** at ten. Ten-qubit Gram spectra are nearly identity (effective rank 19.00–27.00 for 19–27 training years). This explains why changing those ten-qubit circuit settings barely changes predictions; it does not prove the kernel family cannot work on another task or encoding.

![Annual development predictions](figures/annual-development/annual-development.png)

![Matched kernel errors](figures/annual-development/annual-matched.png)

![Kernel similarities](figures/annual-development/annual-kernel-similarity.png)

Figures use saved development evidence only. SVG counterparts are available alongside each PNG. The frozen reused-year comparison is complete; see [final notes](ANNUAL_FINAL.md) for results, all selected Gram diagnostics and the literature-guide adoption table. Final repository/document checks and handoff remain in progress.

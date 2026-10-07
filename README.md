# Quantum kernels for annual Ontario wildfire estimation

Qiskit Fall Fest **open challenge · Quantum Machine Learning / Sustainability**. Can classical and quantum models estimate **annual mean reported wildfire size in Ontario**, measured in **hectares per size-observed fire**? This is retrospective estimation using the same year's climate, not an advance forecast or an individual-fire classifier. Success means lower chronological MAE than a training-mean baseline, at a documented computation budget.

**Frozen matched comparison:** RBF leads development. None of eleven main models beats the training mean on the six reused evaluation years. More qubits do not automatically yield useful similarities; encoding scale changes concentration and conditioning. We demonstrate no quantum or hardware advantage.

[Judge guide](docs/JUDGES.md) · [Presentation](web/presentation/README.md) · [Fireline canvas game](web/demo/README.md) · [Report](docs/REPORT.md) · [Frozen evidence](docs/ANNUAL_FINAL.md)

**Comprehensive followup:** [goal receipt](GOAL.md), [coverage](docs/RESEARCH_COVERAGE.md) and [new findings](docs/RESEARCH_FINDINGS.md). Six local followups and nine new IBM jobs are measured (82 charged QPU seconds). Broader tuning and mitigation give mixed results; all ten saved studies replay from a clean tracked tree and209 tests pass. These followups preserve the frozen evaluation above.

**Measurement-count followup:** [512/1,024/2,048 shots on Marrakesh and Quebec](docs/SHOT_SWEEP.md). All 12 real jobs completed: 301,056 shots, 108 charged QPU seconds. More shots collect candidates but do not repair low feasible yield; measured subset quality and classical controls are reported.

**Scientific review response:** [measured sensitivity and factual audit](docs/CRITIQUE_RESPONSE.md). Exact four-of-twenty QUBO enumeration takes 3.07 ms median on this Mac. Saved tuning choices are sensitive to validation weights, and classical repair can sharply change downstream error while retaining dominant measured geometry. These are development diagnostics, not predictive confirmation.

## Data and design

- **One row per Ontario year:** 1988–2018 training (**31 observations**); 2019–2024 evaluation (**six reused years**, previously inspected in an incident study).
- **Fire labels:** audited NRCan National Fire Database point snapshot, with 39,616 size-observed training incidents and 3,828 evaluation incidents. Identity and prescribed-fire exclusions are explicit. Mean size, total reported hectares and incident count are separate outcomes; recorded fires are not a certified census.
- **Climate:** ECCC Monthly Climate Summaries, 456 downloaded months covering 1987–2024. Ten temperature/precipitation/snowfall/degree-day summaries; eligible station-years have equal weight. Counts vary 65–340. Monthly weather is not daily weather.
- **Woodland:** NRCan annual land-cover maps, official Ontario boundary, prior-year classified-area fractions in a separate training ablation. Map coverage ends in 2022; woodland is not a final predictor. Classes are not tree density.

[Data sources, coverage and download commands](docs/DATA_DOWNLOADS.md) · [Schema and exclusions](docs/DATA_SCHEMA.md) · [Independent source audit](docs/DATA_REVIEW.md) · [31-row public table](docs/data/annual_training.csv). Source versions and SHA-256 hashes are recorded in manifests and frozen plans; no large raw download is needed for the public replay below.

Three expanding chronological outer folds cover 2007–2010, 2011–2014 and 2015–2018. Three inner splits tune each model, with preprocessing fit inside its training window. Targets use log1p and training-only standardization, then return to nonnegative hectares. Final states were committed before annual evaluation; previous exposure means those years are **not independent confirmation**.

## Quantum and classical methods

Training-standardized climate values become bounded circuit angles:

$$\theta_j=a\tanh(z_j/2),\qquad k_q(x,y)=|\langle\phi(x)|\phi(y)\rangle|^2.$$

Actual Qiskit **FidelityQuantumKernel** computes overlaps using an exact local compute-uncompute sampler. **QSVR** feeds that matrix to a classical support-vector solver. Linear ZZ feature maps use four or ten features/qubits, one/two repetitions and amplitudes pi/4 or pi/2. Entangling gates enable interactions; they do not guarantee useful meteorological features.

Mean, median, calendar trend, ridge, linear SVR and RBF-SVR are controls. RBF and QSVR each receive **36 configurations per width/fold**: four bandwidths/maps crossed with nine C/epsilon choices. The matched inputs and chronological folds separate kernel choice from data access.

Eight feature selectors are compared with fixed ridge, then crossed with ridge/RBF/QSVR. QAOA uses a continuous-target relevance/redundancy QUBO and synthetic bitstring draws. Actual **qiskit-addon-sqd** projection recovers the best sampled diagonal energy; with only 210 feasible four-of-ten subsets, SQD adds no optimization beyond choosing that sample. It is an applicability demonstration, not an advantage.

## Results

MAE in **ha/fire**, lower is better. Development is the mean of three chronological fold errors; these are not independent seed replications.

| Four-input comparison | Development | Reused 2019–2024 |
|---|---:|---:|
| Training mean | 92.00 | **276.81** |
| RBF-SVR | **77.02** | 299.81 |
| QSVR | 86.64 | 280.68 |

QSVR beating RBF on reused years does not establish useful prediction: both lose to the constant. Annual extremes remain poorly predicted. Ten-qubit cross-year fidelity averages 0.000899 and predictions remain close to the fitted intercept. A later **input-only** scale diagnostic changes ten-qubit training similarity from 0.000805 to 0.538897, but narrower angles can produce poor conditioning. **This diagnostic fitted no predictor or replacement for the frozen final model.** [Annual errors and all models](docs/ANNUAL_FINAL.md) · [Bandwidth evidence](docs/ANNUAL_BANDWIDTH_GEOMETRY.md).

## View the presentation and demo

```sh
bun run web/presentation/serve.ts
```

[Presentation](http://127.0.0.1:8790/web/presentation/) · [Fireline](http://127.0.0.1:8790/web/demo/). Viewing uses committed assets and Bun. The [latest clean-tree verification](docs/data/fireline_canvas_verification.json) verifies slides, context and game controls with external requests blocked, separately from scientific reproduction.

## Reproduce the result

The separate [pipeline mitigation study](docs/PIPELINE_MITIGATION.md) applies DD/twirling, calibrated readout and kernel repair to actual QSVR/QAOA/SQD circuits. The [Fez/Marrakesh/Quebec comparison](docs/IBM_PIPELINE_MITIGATION.md) returned 224,256 physical shots across six jobs, using **75 charged QPU seconds**. Geometry repair and predictive error do not consistently improve together.

Later, separately frozen development work adds [six numerical forest families](docs/FOREST_CONTEXT.md), [10/16/20-candidate selection](docs/SELECTOR_SCALING.md) and [actual expanded hardware selection/QSVR](docs/SELECTOR_HARDWARE.md). Forest inputs and graph-matched controls reveal retrospective associations. Optimized two-layer QAOA improves ideal20-feature objective sampling, but that subset predicts worse with QSVR; deep hardware preparation sharply reduces feasible yield. These development results do not replace the original final-year evidence or demonstrate quantum advantage. Public collectors replay saved counts and prediction equations without fits, states, draws, credentials or downloads. Game instruments remain separate.

Use Python **3.12** and [uv](https://docs.astral.sh/uv/). Versions are locked: Qiskit 2.5.2, Qiskit Machine Learning 0.9.1, scikit-learn 1.9.1 and qiskit-addon-sqd 0.13.1.

```sh
uv sync --locked --group data --group analysis --group quantum
uv run --no-sync python scripts/pipeline.py annual collect --output .cache/wildfire/annual-public --execute
```

The later scientific critique replays separately with `uv run --no-sync python scripts/collect_critique.py`: eleven saved prediction panels, 99 cached-choice diagnostics and eight matrix-repair diagnostics, without fits, new measurements or timing reruns.

Offline collection checks scientific code, plans, learned states, matrices and predictions. Later dependency-manifest changes are disclosed rather than blocking arithmetic replay; training/evaluation still enforce their original complete environment guards.

The 267 kB public bundle reproduces **83 predictions and 24 matrix pairs** without raw data, credentials, fitting or quantum execution. Use a new output directory. Preview by omitting `--execute`. For fresh training-only reproduction, use the fixed plans and commands in [reproduction](docs/REPRODUCIBILITY.md); some preparation stages require ignored source files. The simulator is analytic, with no physical shots; selector sensitivity seeds are 7/19/31.

Final training/evaluation took **93.75/9.63 seconds**, excluding environment installation: 36/12 quantum matrices and 12,092/2,232 analytic fidelity-pair circuits. There were 80 final sklearn/QSVR fits, plus a polynomial trend; evaluation performed zero fits. The separate geometry diagnostic used ten matrices/4,650 analytic pair circuits in 48.89 seconds. **No hardware jobs were submitted for this annual study.** [Resource receipts](docs/ANNUAL_FINAL.md).

Historical scientific verification passes **145 tests / 69 CLI help paths** at `870abe2`; presentation verification is recorded separately. Fresh-clone setup and evidence replay pass in a new isolated environment on this Mac, using uv's shared package cache. Collection took 35.57 seconds. [QA receipt](docs/data/annual_bandwidth_repository_checks.json) · [Fresh-clone receipt](docs/data/judge_portability_receipt.json).

The later forest/hardware extension passes **185 tests /81 CLI paths** and public replay from a source-free tracked clone using the existing locked environment. [Current scoped completion and verification](docs/data/forest_hardware_handoff.json) preserves the earlier receipts and records the actual hardware charges, failures and remaining monthly allowance.

## Interpretation and credits

This is an exploratory negative comparison with a concrete kernel diagnosis. Small annual sample size, six reused years, retrospective climate/map processing, variable station coverage, source reporting changes and ideal simulation limit generalization. Kernel conditioning alone is not predictive quality. A prospective horizon, more independent observations, raw/log-target controls and train-only scale tuning are future work, not completed results.

Fernando Nogueira and collaborator `n123xyz` contributed through this repository; [commit history](https://github.com/OhRats-Technologies/OhRats_QFF2026_uottawa/commits/main/) and the append-only board identify contributions and reviews. Codex assisted implementation, experiments and documentation; it is not an independent scientific replication. Dataset credits, source URLs and reused-method references are in [source documentation](docs/DATA_DOWNLOADS.md), [the report](docs/REPORT.md) and the [QSVR guide](<docs/QSVR with Qiskit Literature and Performance Guide.md>). Preserve source attribution.

The earlier [incident-classification branch](docs/FINAL_EVALUATION.md) is supporting evidence, separate from this annual task. Internal [goal](GOAL.md), [handoff](docs/HANDOFF.md) and [board protocol](AGENT_BOARD.md) are for coordination. Credentials remain in ignored `.env`; public replay needs none.

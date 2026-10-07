# Documentation Portal and Directory Guide

Welcome to the documentation suite for the OhRats Qiskit Fall Fest 2026 challenge repository.

This project investigates whether quantum machine learning—specifically Quantum Support Vector Regression (QSVR) and Quantum Approximate Optimization Algorithm (QAOA) feature selection—can improve retrospective macro estimation of annual wildfire burn severity across Ontario, Canada, benchmarked under strictly matched computational and data budgets.

> [!NOTE]
> **Core Finding in 30 Seconds:**
> On the frozen 2019–2024 holdout evaluation, classical RBF-SVR leads development, and **no tested climate model beats the historical training-mean baseline**. Across **39 IBM Quantum hardware executions** (1.1M shots on Heron and Eagle processors), we show that:
> 1. Scaling shots buys candidate coverage but **does not increase feasible yield** on deep circuits (~1,000 CZs).
> 2. Classical uniform feasible sampling **outperforms 11 of 12 measured hardware minima**.
> 3. Readout error mitigation lowers Gram matrix RMSE but **can worsen downstream regression despite lower matrix error**.
> 4. Classical station-reporting coverage (MAE 83.08) and calendar trends (MAE 88.61) provide competitive development controls alongside weather models (baseline 92.00 ha/fire).
>
> We report this as a rigorous, fully reproducible **empirical benchmark and diagnostic post-mortem on NISQ machine learning**, with zero hype and no claimed quantum advantage.

---

## Curated Reading Pathways

With 50 detailed technical documents in this directory, choose your reading pathway below based on your role and interest:

```mermaid
flowchart TD
    Start["Where do you want to start?"] --> Judges["Hackathon Judge / Quick Evaluator<br/>(10 minutes)"]
    Start --> Quantum["Quantum & Hardware Specialist<br/>(QPU Benchmarks, Noise & Circuits)"]
    Start --> ML["ML, Climate & Geospatial Reviewer<br/>(Datasets, Baselines & Confounders)"]
    Start --> Peer["Scientific Auditor & Peer Reviewer<br/>(Critique, Stability & Reproducibility)"]
    Start --> Game["Interactive Demo / Game Player<br/>(Fireline Canvas Simulator)"]

    Judges --> J1["1. docs/JUDGES.md<br/>2. docs/REPORT.md<br/>3. docs/ANNUAL_FINAL.md<br/>4. docs/SUBMISSION_AUDIT.md"]
    Quantum --> Q1["1. docs/SHOT_SWEEP.md<br/>2. docs/IBM_PIPELINE_MITIGATION.md<br/>3. docs/SELECTOR_HARDWARE.md<br/>4. docs/QSVR_QEC_ERROR_STUDY.md"]
    ML --> M1["1. docs/DATA_SCHEMA.md<br/>2. docs/FOREST_CONTEXT.md<br/>3. docs/FIRE_FEATURE_SPACE.md<br/>4. docs/LABEL_QUALITY.md"]
    Peer --> P1["1. docs/WORK_ANALYSIS_20261006.md<br/>2. docs/SCIENTIFIC_CRITIQUE_20261006.md<br/>3. docs/CRITIQUE_RESPONSE.md<br/>4. docs/REPRODUCIBILITY.md"]
    Game --> G1["1. docs/FIRELINE_CANVAS.md<br/>2. docs/WILDFIRE_GAME.md<br/>3. web/demo/README.md"]
```

---

## Master Thematic Document Directory

All 50 documentation files in this folder are organized into seven logical categories below:

### 1. Core Reports and Official Submission Gateways
*Start here to understand the core research question, experimental methodology, and final results.*

| Document | Description |
| :--- | :--- |
| **[`JUDGES.md`](JUDGES.md)** | **Primary entry point for judges.** Core challenge question, matched results, reading order, and checklist. |
| **[`REPORT.md`](REPORT.md)** | **Main scientific paper.** Formulation of annual Ontario wildfire regression, matched RBF/QSVR comparison, and negative results. |
| **[`ANNUAL_FINAL.md`](ANNUAL_FINAL.md)** | **Frozen annual holdout results.** Final evaluation errors across all 11 models on 2019–2024, spectra, and parameter tables. |
| **[`SUBMISSION_AUDIT.md`](SUBMISSION_AUDIT.md)** | Complete audit against hackathon prompts, slide deck readiness, and submission requirements. |
| **[`REPRODUCIBILITY.md`](REPRODUCIBILITY.md)** | Step-by-step reproduction guide, public offline evidence bundle instructions, and environment locks. |

---

### 2. Real IBM QPU Hardware Benchmarks and NISQ Scaling
*Empirical results from 39 IBM Quantum jobs across `ibm_fez`, `ibm_marrakesh`, and `ibm_quebec`.*

| Document | Description |
| :--- | :--- |
| **[`SHOT_SWEEP.md`](SHOT_SWEEP.md)** | **Two-device physical shot sweep** (512, 1024, 2048 shots on Marrakesh & Quebec; 12 jobs, 301k shots). Shows increased candidate coverage without a consistent increase in feasible yield, while classical sampling beats 11/12 QPU minima. |
| **[`IBM_PIPELINE_MITIGATION.md`](IBM_PIPELINE_MITIGATION.md)** | **Three-device pipeline comparison** (`ibm_fez`, `ibm_marrakesh`, `ibm_quebec`; 6 jobs, 75s QPU). Evaluates DD, twirling, and readout mitigation across QPUs. |
| **[`SELECTOR_HARDWARE.md`](SELECTOR_HARDWARE.md)** | **Hardware selector execution** on `ibm_marrakesh` for 10/16/20 feature pools, Dicke state preparation depth, and 10-shard recovery from scheduler error 1520. |
| **[`SELECTOR_SCALING.md`](SELECTOR_SCALING.md)** | Ideal vs noisy QAOA/SQD selection across 10, 16, and 20 candidate pools; details why better QUBO sampling does not improve regression. |
| **[`RESEARCH_FINDINGS.md`](RESEARCH_FINDINGS.md)** | Comprehensive search followup: 6 local studies, multi-start QAOA ($p=1\dots 4$), distinct 720-grid hyperparameter tuning ($C=100$ boundary collapse), and 9 IBM jobs. |
| **[`RESEARCH_COVERAGE.md`](RESEARCH_COVERAGE.md)** | Verification matrix mapping proposed research milestones to implemented evidence. |

---

### 3. Scientific Review, Peer Critique and Stability Audits
*In-depth synthesis, adversarial critique, and empirical sensitivity checks.*

| Document | Description |
| :--- | :--- |
| **[`WORK_ANALYSIS_20261006.md`](WORK_ANALYSIS_20261006.md)** | **Full synthesis of October 6 campaign** (08:00–16:15 EDT) covering 5 research streams, 39 QPU jobs, 405s QPU time, and key takeaways. |
| **[`SCIENTIFIC_CRITIQUE_20261006.md`](SCIENTIFIC_CRITIQUE_20261006.md)** | **Adversarial peer-review critique** identifying the $N=31$ sample size limitation, combinatorial triviality of $\binom{20}{4}$, calibration drift, and reporting confounders. |
| **[`CRITIQUE_RESPONSE.md`](CRITIQUE_RESPONSE.md)** | **Formal response to critique** with leave-one-out sensitivity analysis, exact classical timing benchmarks (3.07 ms), and spectral validation without retraining. |

---

### 4. Environmental Data, Forestry Rasters and Geospatial Audits
*Data provenance, spatial-temporal joins, and rigorous cleaning of Canadian environmental feeds.*

| Document | Description |
| :--- | :--- |
| **[`DATA_SCHEMA.md`](DATA_SCHEMA.md)** | Formal schema, entity relationships, and temporal join logic for NFDB fire points, ECCC monthly weather, and NRCan forest cover. |
| **[`DATA_REVIEW.md`](DATA_REVIEW.md)** | Detailed audit of historical fire record counts, size denominators, and extreme fire distributions. |
| **[`DATA_DOWNLOADS.md`](DATA_DOWNLOADS.md)** | Exact source URLs, retrieval dates, and commands for downloading Canadian open data snapshots. |
| **[`FOREST_CONTEXT.md`](FOREST_CONTEXT.md)** | Numerical forest expansion: 42 coarse raster layers (canopy height, crown closure, biomass, stem volume, stand age) across Ontario (1988–2022). |
| **[`FIRE_FEATURE_SPACE.md`](FIRE_FEATURE_SPACE.md)** | Exhaustive audit of all 46 Open Canada `fire` search pages, assessing geospatial coverage, resolution, and availability. |
| **[`LABEL_QUALITY.md`](LABEL_QUALITY.md)** | Audit of reported-size boundaries, missing coordinates, and exclusion rules. |
| **[`SOURCE_ASSUMPTIONS.md`](SOURCE_ASSUMPTIONS.md)** | Core assumptions on station spatial averaging, reporting lags, and retrospective annual boundaries. |

---

### 5. Quantum Methods, Error Mitigation and Algorithmic Theory
*Mathematical formulations, noise models, and algorithmic behavior.*

| Document | Description |
| :--- | :--- |
| **[`QSVR_QEC_ERROR_STUDY.md`](QSVR_QEC_ERROR_STUDY.md)** | **Deep 50KB technical monograph** on QSVR mathematics, hardware noise channels, Pauli twirling, and error mitigation theory. |
| **[`QSVR with Qiskit Literature and Performance Guide.md`](QSVR%20with%20Qiskit%20Literature%20and%20Performance%20Guide.md)** | Comprehensive literature review and performance guide for implementing QSVR in Qiskit. |
| **[`PIPELINE_MITIGATION.md`](PIPELINE_MITIGATION.md)** | Specification of pipeline error-mitigation techniques (DD, twirling, readout calibration, PSD/rank repair). |
| **[`PROXY_ALIGNMENT.md`](PROXY_ALIGNMENT.md)** | Empirical study evaluating whether minimizing QAOA QUBO energy aligns with lower regression error. |
| **[`ANNUAL_BANDWIDTH_GEOMETRY.md`](ANNUAL_BANDWIDTH_GEOMETRY.md)** | Investigation of input encoding bandwidth ($\theta = a \tanh(z/2)$) and its impact on kernel conditioning and concentration. |
| **[`LOCAL_GEOMETRY.md`](LOCAL_GEOMETRY.md)** | Quantum Geometric Tensor (QGT) analysis and local classical tangent space approximations. |
| **[`TANGENT_PREDICTION.md`](TANGENT_PREDICTION.md)** | Comparison of local tangent linear models against exact quantum kernels. |
| **[`QUANTUM_METHODS.md`](QUANTUM_METHODS.md)** | Mathematical formulation of feature maps, compute-uncompute circuits, and resource scaling. |
| **[`KERNEL_CONVERGENCE.md`](KERNEL_CONVERGENCE.md)** | Numerical stability and condition number analysis of quantum Gram matrices. |
| **[`KERNEL_RIDGE.md`](KERNEL_RIDGE.md)** | Direct smooth Kernel Ridge Regression controls vs support vector regression. |
| **[`QUANTUM_LANDMARKS.md`](QUANTUM_LANDMARKS.md)** | Nyström landmark approximation and low-rank quantum kernel subsampling. |
| **[`LANDMARK_SHOT_RIDGE.md`](LANDMARK_SHOT_RIDGE.md)** | Landmark kernel ridge regression under explicit binomial shot noise models. |
| **[`SHOT_FEASIBILITY.md`](SHOT_FEASIBILITY.md)** | Theoretical shot budget requirements as a function of feature dimension and angle scaling. |
| **[`CONSTRAINED_SELECTION.md`](CONSTRAINED_SELECTION.md)** | Comparison of penalty-based QAOA vs constrained mixer designs for cardinality constraints. |
| **[`PROBABILITY_REPORT.md`](PROBABILITY_REPORT.md)** | Reliability diagrams, calibration curves, and Brier score analysis. |
| **[`QISKIT_FOLLOWUP.md`](QISKIT_FOLLOWUP.md)** | Analysis of Qiskit library primitives, runtime options, and addon-sqd capabilities. |

---

### 6. Interactive Demonstrations and Educational Game Engine
*Interactive tools and browser-based educational experiences.*

| Document | Description |
| :--- | :--- |
| **[`FIRELINE_CANVAS.md`](FIRELINE_CANVAS.md)** | Architecture and guide for the **Fireline 2D Canvas Engineering Simulator** (`web/demo/`), an interactive sandbox for building, testing, and repairing QSVR engines. |
| **[`WILDFIRE_GAME.md`](WILDFIRE_GAME.md)** | Game design document covering Ontario wildfire strategy mechanics and resource allocations. |
| **[`QSVR_GAME.md`](QSVR_GAME.md)** | Documentation of the interactive educational QSVR kernel repair interface. |

---

### 7. Historical Context and Preserved Milestone Records
*Preserved records from earlier development phases retained for transparency and provenance.*

| Document | Description |
| :--- | :--- |
| **[`FINAL_EVALUATION.md`](FINAL_EVALUATION.md)** | Historical final evaluation of the earlier incident-level classification branch ($\ge 10$ ha fires). |
| **[`PILOT_REPORT.md`](PILOT_REPORT.md)** | Preliminary pilot report on Ontario wildfire size estimation. |
| **[`ANNUAL_QSVR.md`](ANNUAL_QSVR.md)** | Initial active planning document for the annual macro regression study. |
| **[`FINDINGS.md`](FINDINGS.md)** | Early development findings and initial hypothesis screening. |
| **[`SCOPE_CORRECTION.md`](SCOPE_CORRECTION.md)** | Formal scope correction document recording the shift from individual-fire classification to macro annual regression. |
| **[`GOAL_AUDIT.md`](GOAL_AUDIT.md)** | Formal audit of repository milestones, execution authority, and historical constraints. |
| **[`POLICY_EVOLUTION.md`](POLICY_EVOLUTION.md)** | Experiment records from autonomous policy evolution testing. |
| **[`HANDOFF.md`](HANDOFF.md)** | Engineering handoff receipts and milestone change logs. |
| **[`PIPELINE.md`](PIPELINE.md)** | Core processing pipeline architecture and directory layout. |
| **[`EXPERIMENTS.md`](EXPERIMENTS.md)** | Experimental design principles and model hypothesis log. |

---

## Core Quantitative Results at a Glance

### Annual Wildfire Regression (MAE in hectares / recorded fire)
*Chronological development (1988–2018) vs frozen holdout (2019–2024). Lower is better.*

| Model | Width | Chronological Development MAE | Reused 2019–2024 Holdout MAE |
| :--- | :---: | :---: | :---: |
| **Training Mean Baseline** | 0 | 92.00 | **276.81** |
| **Linear Year Trend** | 0 | 88.91 | 321.12 |
| **Tuned Ridge Regression** | 10 | 81.21 | 305.42 |
| **Matched Classical RBF-SVR** | 4 | **77.02** | 299.81 |
| **Matched Quantum QSVR** | 4 | 86.64 | 280.68 |
| **Station Count Alone** *(Confounder Control)* | 1 | **83.08** | — |
| **Calendar Trend Alone** *(Confounder Control)* | 1 | **88.61** | — |
| **Weather + Calendar Ridge** *(Confounder Control)* | 11 | **67.97** | — |

*Takeaway:* While 4-input QSVR edges out RBF on the holdout, neither beats the simple training mean baseline. Station-coverage and calendar-only controls warrant checking whether weather gains reflect reporting or time effects; these errors do not establish causation.

![Annual holdout predictions and actual observed fire size across models](figures/annual-final/annual-reused-predictions.png)

---

### Hardware Shot Sweep on 20-Feature Selector
*Feasible cardinality-4 yield across shot levels on `ibm_marrakesh` (Heron) and `ibm_quebec` (Eagle).*

| Backend | Arm | 512 Shots: Valid Yield | 1,024 Shots: Valid Yield | 2,048 Shots: Valid Yield | Best Objective Gap (2,048 shots) |
| :--- | :--- | :---: | :---: | :---: | :---: |
| **Marrakesh** | Raw | 74 (14.45%) | 129 (12.60%) | 259 (12.65%) | 0.0895 |
| **Marrakesh** | DD + Twirling | 13 (2.54%) | 35 (3.42%) | 75 (3.66%) | 0.1791 |
| **Quebec** | Raw | 2 (0.39%) | 10 (0.98%) | 19 (0.93%) | 0.1912 |
| **Quebec** | DD + Twirling | 4 (0.78%) | 6 (0.59%) | 12 (0.59%) | 0.3027 |
| **Classical Uniform** | 100 MC Trials | 512 (100.0%) | 1,024 (100.0%) | 2,048 (100.0%) | **0.0432** (mean) |

*Takeaway:* Feasible fractions do not increase consistently as shots quadruple. Classical uniform feasible sampling achieves a lower minimum cost than 11 of the 12 measured QPU runs at matched draw counts.

![Measured feasible yield across shot counts on Heron and Eagle processors](figures/shot-sweep-both-yield.png)

![Observed best objective gap versus classical uniform sampling](figures/shot-sweep-both-quality.png)

---

## Completed Hardware Extension

[Restricted repetition-code overlap benchmark](REPETITION_MICROKERNEL.md): four completed IBM jobs, two blocks each on Marrakesh and Quebec, comparing physical, encoded and dynamic-corrected overlaps. All 1,474,560 shots validate; the four jobs consumed 414 charged QPU seconds. The unencoded overlap wins the no-injection controls on both devices. Quebec correction reduces delayed encoded error in both blocks but still loses to the physical kernel. This study is separate from the completed 39-job campaign and the frozen wildfire predictions.

## Quick Reproduction Commands

Saved public evidence can be replayed and verified offline using [uv](https://docs.astral.sh/uv/) and Python 3.12:

```sh
# 1. Replay annual scientific evaluation (no network, no credentials)
uv run python scripts/pipeline.py annual collect --output .cache/wildfire/annual-public --execute

# 2. Replay the listed saved QPU searches and shot sweeps (no new jobs)
uv run python scripts/collect_hardware_search.py shot-sweep-marrakesh
uv run python scripts/collect_hardware_search.py shot-sweep-quebec
uv run python scripts/collect_hardware_search.py shallow-hardware-search
uv run python scripts/collect_hardware_search.py tuned-kernel-hardware

# 3. Replay scientific critique and sensitivity diagnostics
uv run python scripts/collect_critique.py

# 4. Run the entire unit test suite (214 tests in ~8 seconds)
uv run python -m unittest discover -s tests -v

# 5. Launch the local presentation and Fireline demo server
bun run web/presentation/serve.ts
```

For questions regarding data provenance, model specifications, or hardware verification, refer to [`JUDGES.md`](JUDGES.md) and [`REPORT.md`](REPORT.md).

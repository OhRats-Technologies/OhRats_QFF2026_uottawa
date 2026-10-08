# Quantum Kernels for Annual Ontario Wildfire Estimation

**OhRats — Qiskit Fall Fest 2026 Open Challenge**

[![Python](https://img.shields.io/badge/python-3.12-blue)](pyproject.toml)
[![Qiskit](https://img.shields.io/badge/Qiskit-2.5.2-purple)](https://qiskit.org/)
[Play Fireline](https://fireline.ohrats.party/) · [Watch the five-minute presentation](https://fireline.ohrats.party/presentation/) · [Research report](docs/REPORT.md)

---

## 1. Problem and Goal

We ask whether climate summaries and quantum kernels can estimate Ontario’s annual mean reported wildfire size. **No main climate model beats the training-mean baseline on the six evaluated years.** The experiments explain how encoding scale, feature selection and hardware noise affect the result.

**Theme:** Quantum Machine Learning / Environmental Sustainability. Can QSVR and QAOA/SQD feature selection improve annual fire-size estimates over classical controls with matched inputs and tuning budgets?

One Ontario calendar year is one observation: **1988–2018 training (31 rows)**, **2019–2024 evaluation (six reused years)**. Success means lower MAE/RMSE than the training mean and matched classical models. The target is mean agency-reported size in **hectares per size-observed fire incident (ha/fire)**.

---

## 2. Data and Assumptions

The public [training table](docs/data/annual_training.csv) has one row per Ontario year. Its ten climate inputs use °C, precipitation mm, snowfall cm and degree-days (base 18°C); the target uses ha/fire.

- **Fire records:** NRCan NFDB point snapshot **20260811**; 39,616 size-observed incidents in training and 3,828 in evaluation. Keep Ontario records with valid years; quarantine blank/duplicate identities and exclude prescribed fires. Unknown/negative sizes are excluded from the size denominator, not treated as zero.
- **Weather:** ECCC Monthly Climate Summaries, **456 source CSVs, 1987–2024**. Aggregate each station-year, then average eligible stations equally (65–340 per feature/year). Annual means require nine months; totals/extremes require twelve; spring/summer require all three months.
- **Forest context:** Later studies use 42 layer×epoch records masked to Ontario. These are separate from the original climate-only comparison.
- **Access and assumptions:** [Source URLs, hashes and download inventory](docs/data/reproduction_inputs.json) identify the exact raw inputs; [data methods](docs/DATA_SCHEMA.md) explain acquisition and coverage. Same-year climate supports retrospective estimation, not a pre-season forecast; equal station weighting is not area weighting.

---

## 3. Approach

Each training fold learns median imputation, feature standardization and standardized `log1p` target scaling. Predictions are inverse-transformed and clipped to nonnegative hectares. Expanding chronological folds compare classical and quantum models:

- **Quantum Feature Map & Encoding:**
  Training features $z_j$ are standardized and mapped to bounded rotation angles:
  $$\theta_j = a \tanh(z_j / 2), \quad a \in \{\pi/4, \pi/2\}$$
  Qiskit uses linear $ZZ$ feature maps with four/ten qubits and one/two repetitions. Bounded angles and shallow circuits keep the small-data comparison tractable:
  $$k_q(x, y) = |\langle\phi(x)|\phi(y)\rangle|^2$$
- **QSVR Regressor:** Overlap matrices computed via Qiskit's `FidelityQuantumKernel` feed a classical SVR optimizer with $C \in \{0.1, 1.0, 10.0\}$ and $\epsilon \in \{0.05, 0.2, 0.5\}$.
- **Quantum Feature Selection (QAOA & SQD):**
  A QUBO rewards mutual-information relevance, penalizes correlated features and enforces four inputs. QAOA samples candidates from 10/16/20-feature pools. SQD diagonalizes the sampled subspace; for this diagonal objective, it returns the lowest-cost sampled subset.
- **Classical controls:** Training mean, calendar trend, tuned ridge and RBF-SVR. RBF receives the same C/epsilon and 36-candidate budget. Station-count and calendar-only controls test reporting changes and time trends.

---

## 4. Setup and Execution

### Dependencies and environment

- **Python:** 3.12 managed via [uv](https://docs.astral.sh/uv/)
- **Core Packages:** `qiskit==2.5.2`, `qiskit-machine-learning==0.9.1`, `scikit-learn==1.9.1`, `qiskit-addon-sqd==0.13.1`
- **Frontend / Demo:** [Bun](https://bun.sh/) for canvas demo serving and test suite.

### Replay the saved annual evaluation

```sh
# 1. Sync locked Python environment
uv sync --locked --group data --group analysis --group quantum

# 2. Check saved predictions without fitting, credentials or hardware calls
uv run --no-sync python scripts/pipeline.py annual collect --output .cache/wildfire/annual-public --execute

# 3. Run Python tests
uv run python -m unittest discover -s tests -v

# 4. Run game tests
bun test web/demo/canvas/*.test.js

# 5. Launch local presentation and Fireline canvas workbench
bun run web/presentation/serve.ts
```

Use a new output directory for each collection. The [recorded fresh-clone replay](docs/data/judge_portability_receipt.json) checked 83 predictions in **35.57 seconds**, without fitting or raw downloads; installation time depends on package caches. [Reproduction details](docs/REPRODUCIBILITY.md) include training reruns and historical environments.

The original kernels use exact local `ComputeUncompute` simulation (`shots=None`, seed **7**), with no QPU calls. Original selector seeds are **7, 19, 31**; depth-one QAOA uses at most **40 COBYLA evaluations and 512 synthetic draws** per fold/seed. Plans pin all settings: [kernels](experiments/annual_qsvr.json), [matched grid](experiments/annual_matched.json), [selectors](experiments/annual_selectors.json).

The hosted [game](https://fireline.ohrats.party/) and [presentation](https://fireline.ohrats.party/presentation/) need no installation. For local authoring, the Bun command serves `/web/demo/` and `/web/presentation/` on port 8790.

---

## 5. Experiments

We performed controlled experiments across local simulation and IBM Quantum physical hardware:

1. **Matched Development Kernel Grid:**
   - 36 configurations per model width/fold: 4 kernel bandwidths/maps $\times$ 9 $(C, \epsilon)$ pairs.
   - Expanding training windows end in 2006/2010/2014 and validate on 2007–2010/2011–2014/2015–2018. Three inner chronological splits select hyperparameters by pooled MAE. Cached kernels give both SVRs the same 36-candidate budget.
2. **Frozen Reused-Year Evaluation (2019–2024):**
   - Parameters, fitted states and scalers were published before evaluation. The evaluation stage performed no fitting; these years had already been inspected in the incident study.
3. **Hardware Shot Sweep:**
   - 12 real QPU jobs across `ibm_marrakesh` and `ibm_quebec` testing 512, 1,024, and 2,048 shots across raw and combined dynamical decoupling (DD) + Pauli twirling arms.
4. **Real QPU Error Mitigation Benchmark:**
   - 6 jobs / 75 charged QPU seconds across `ibm_fez`, `ibm_marrakesh`, and `ibm_quebec` comparing raw versus mitigated QSVR Gram matrices and downstream SVR error.
5. **Unsuccessful / Negative Experiments:**
   - *10-qubit kernels:* Nearly identity-like matrices (mean validation/training fidelity 0.0010 vs 0.0758 at four qubits) left predictions near the fitted intercept.
   - *Feature selection:* Better QUBO costs did not consistently improve prediction. The 4-of-20 search still has only 4,845 feasible subsets, making exact classical enumeration inexpensive.

---

## 6. Results

### Annual wildfire regression (reused evaluation, 2019–2024)
*Lower error is better. Values reported in hectares per fire.*

| Model | Width | Chronological Dev MAE | 2019–2024 MAE | 2019–2024 RMSE |
| :--- | :---: | :---: | :---: | :---: |
| **Training Mean Baseline** | 0 | 92.00 | **276.81** | **336.12** |
| **Linear Year Trend** | 0 | 88.91 | 286.58 | 353.63 |
| **Tuned Ridge Regression** | 10 | 81.21 | 294.98 | 372.24 |
| **Matched Classical RBF-SVR** | 4 | **77.02** | 299.81 | 380.52 |
| **Matched Quantum QSVR** | 4 | 86.64 | 280.68 | 352.51 |
| **Station Count Alone, QSVR** *(Control)* | 1 | **83.08** | — | — |
| **Calendar Trend Alone, QSVR** *(Control)* | 1 | **88.61** | — | — |
| **Weather + Calendar Ridge** *(Control)* | 11 | **67.97** | — | — |

![Annual mean reported fire size and model predictions](docs/figures/annual-final/annual-reused-predictions.png)

### Real Hardware Shot Sweep Yield (20-Feature Selector)

| Device | Arm | 512 Shots Valid | 1,024 Shots Valid | 2,048 Shots Valid | Best Objective Gap (2,048) |
| :--- | :--- | :---: | :---: | :---: | :---: |
| **ibm_marrakesh** | Raw | 74 (14.45%) | 129 (12.60%) | 259 (12.65%) | 0.0895 |
| **ibm_marrakesh** | DD + Twirling | 13 (2.54%) | 35 (3.42%) | 75 (3.66%) | 0.1791 |
| **ibm_quebec** | Raw | 2 (0.39%) | 10 (0.98%) | 19 (0.93%) | 0.1912 |
| **ibm_quebec** | DD + Twirling | 4 (0.78%) | 6 (0.59%) | 12 (0.59%) | 0.3027 |
| **Classical Uniform** | Monte Carlo | 512 (100.0%) | 1,024 (100.0%) | 2,048 (100.0%) | **0.0432** (mean) |

Original final training/evaluation took **93.75/9.63 seconds** and **12,092/2,232 analytic fidelity-pair circuits**, with zero evaluation fits. [Saved outputs and accounting](docs/REPORT.md#training-freeze-and-saved-evidence) include all models and selector comparisons.

The [hardware ledger](docs/data/hardware_accounting.json) totals **45 jobs (two failed), 2,580,992 returned shots and 819 charged QPU seconds**, across accounts and separate studies. The [shot sweep](docs/SHOT_SWEEP.md) accounts for 12 jobs/108 seconds; [three-device mitigation](docs/IBM_PIPELINE_MITIGATION.md), six/75; [repetition microkernels](docs/results/repetition-microkernel.json), four/414. Charged time excludes queue waits.

Annual errors are descriptive results on six reused years; selector seeds reuse the same observations. Shot-yield plots include Wilson intervals under an independent-shot assumption, not device-to-device or predictive confidence guarantees.

---

## 7. Discussion and Limitations

RBF leads matched development; QSVR beats matched RBF on reused evaluation years, but neither beats the mean. This establishes a reproducible comparison, not predictive or quantum advantage.

Ten-qubit encoding makes different years almost orthogonal. Narrowing the angle restores similarity, but can produce a nearly constant, poorly conditioned kernel. More qubits alone do not fix the information available to regression.

Hardware readout correction lowers kernel error in the three-device diagnostic, yet increases prediction error in its corresponding comparisons. DD/twirling does not consistently help. Matrix quality, valid sample yield and downstream error are separate measurements.

The main limitations are 31 training years, six reused evaluation years, changing station coverage and retrospective inputs. The original final comparison uses exact local simulation; later hardware studies are separate development diagnostics. Fireline runs educational calculations in the browser and does not generate research evidence.

---

## 8. Conclusions

The main climate models do not improve on the historical-mean baseline for annual Ontario fire size in this evaluation. Our contributions are the audited annual dataset, matched QSVR comparison, encoding-scale diagnosis, and real-device measurements showing why better subset costs or kernel accuracy need not improve prediction.

Future work could use regional or ecozone-month observations and choose encoding scale within training folds. Those would be new studies; the published final models remain fixed.

---

## 9. Sources and Contributions

- **Datasets:**
  - Natural Resources Canada (NRCan): [Canadian National Fire Database (NFDB)](https://cwfis.cfs.nrcan.gc.ca/ha/nfdb)
  - Environment and Climate Change Canada (ECCC): [Monthly Climate Summaries](https://climate.weather.gc.ca/prods_servs/cdn_climate_summary_e.html)
  - Statistics Canada: [2021 Digital Boundary Files](https://geo.statcan.gc.ca/geo_wa/rest/services/2021/Digital_boundary_files/MapServer/0)
  - NRCan forest products and their versions are cited in [data methods](docs/DATA_SCHEMA.md#sources-and-observation-units).
- **Software:** [Qiskit/Qiskit Machine Learning](https://github.com/qiskit-community), `qiskit-addon-sqd` and scikit-learn (versions above).
- **Methods and attribution:**
  - Canatar et al., [Bandwidth Enables Generalization in Quantum Kernel Models](https://arxiv.org/abs/2206.06686v3); Qiskit [FidelityQuantumKernel API](https://qiskit-community.github.io/qiskit-machine-learning/stubs/qiskit_machine_learning.kernels.FidelityQuantumKernel.html).
  - IBM’s [QAOA tutorial](https://quantum.cloud.ibm.com/docs/en/tutorials/quantum-approximate-optimization-algorithm) and [SQD overview](https://quantum.cloud.ibm.com/learning/en/courses/quantum-diagonalization-algorithms/sqd-overview) describe the algorithm foundations; our diagonal feature-selection case differs from molecular SQD.
  - Reused software is listed above; [Fireline asset credits](web/demo/canvas/ASSETS.md) identify supplied/generated art and original audio.
- **Team Contributions:**
  - **Fernando Nogueira, Othmane Daali & collaborator `n123xyz`:** Problem formulation, experimental design, QPU execution, classical controls, Fireline canvas workbench, and documentation.
  - Full revision history and discussion are preserved in the git commit log and [`AGENT_BOARD.jsonl`](AGENT_BOARD.jsonl).


---

## Documentation Index

- **[Live presentation](https://fireline.ohrats.party/presentation/):** Seven talk slides and two appendices.
- **[Fireline](https://fireline.ohrats.party/):** Play with feature subsets, kernel angles and SVR settings.
- **[Research report](docs/REPORT.md):** Methods, comparisons, frozen evaluation and limitations.
- **[Data and model methods](docs/DATA_SCHEMA.md):** Source contracts, aggregation, encoding and selection.
- **[Hardware Shot Sweep](docs/SHOT_SWEEP.md):** 12-job QPU scaling benchmark.
- **[Pipeline Mitigation](docs/IBM_PIPELINE_MITIGATION.md):** Error mitigation analysis across Fez, Marrakesh, and Quebec.
- **[Hardware Feature Selector](docs/SELECTOR_HARDWARE.md):** Dicke state preparation and selection results.
- **[Reproduction Instructions](docs/REPRODUCIBILITY.md):** Step-by-step verification guide.

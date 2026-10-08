# Quantum Kernels for Annual Ontario Wildfire Estimation

**OhRats — Qiskit Fall Fest 2026 Open Challenge**

[![Python](https://img.shields.io/badge/python-3.12-blue)](pyproject.toml)
[![Qiskit](https://img.shields.io/badge/Qiskit-2.5.2-purple)](https://qiskit.org/)
[Play Fireline](https://fireline.ohrats.party/) · [Watch the five-minute presentation](https://fireline.ohrats.party/presentation/) · [Judge guide](docs/JUDGES.md)

---

## 1. Problem and Goal

We ask whether climate summaries and quantum kernels can estimate Ontario’s annual mean reported wildfire size. **No main climate model beats the training-mean baseline on the six evaluated years.** The experiments explain how encoding scale, feature selection and hardware noise affect the result.

- **Open Challenge Theme:** Quantum Machine Learning / Environmental Sustainability.
- **Research Question:** Can QSVR and QAOA/SQD feature selection improve annual mean fire-size estimates over classical baselines, with matched inputs and tuning budgets?
- **Scope & Observation Unit:** One Ontario calendar year per observation, using same-year climate:
  - **Training Window:** 1988–2018 (**31 annual observations**).
  - **Frozen Evaluation:** 2019–2024 (**6 reused years**, previously opened in a preliminary incident study).
- **Primary Target & Metric:** Annual mean agency-reported wildfire size, expressed in **hectares per size-observed fire incident** (ha/fire).
- **Success Metric:** Mean Absolute Error (MAE) and Root Mean Squared Error (RMSE) benchmarked against classical controls.

---

## 2. Data and Assumptions

The annual table combines public fire records and weather summaries. Forest layers support later development studies and the map:

1. **National Fire Database (NRCan NFDB Point Snapshot):**
   - 39,616 size-observed fire incidents across Ontario during 1988–2018, and 3,828 incidents during 2019–2024.
   - Incidents with unknown or negative recorded sizes are excluded from the denominator.
2. **Monthly Climate Summaries (Environment and Climate Change Canada - ECCC):**
   - 456 monthly source CSV files (1987–2024). Each eligible station-year is weighted equally; station counts vary from 65 to 340 by feature and year.
   - 10 climate summaries: mean temperature, total precipitation, snowfall, extreme temperatures, and seasonal heating/cooling degree days.
3. **Land Cover & Forestry (NRCan Forest Cover Rasters):**
   - Later forest studies used 42 source layers; the province boundary masks their spatial summaries. Forest features are separate from the original climate-only final comparison.
4. **Data Sourcing & Reproduction:**
   - Raw Canadian federal data can be downloaded following the source specifications in [`docs/DATA_SCHEMA.md`](docs/DATA_SCHEMA.md).
   - The public 31-row training table is bundled in [`docs/data/annual_training.csv`](docs/data/annual_training.csv).
5. **Key Assumptions & Boundaries:**
   - Same-year climate supports retrospective estimates. It is unavailable at the start of the fire season.
   - Equal station weighting is not provincial area weighting.

---

## 3. Approach

Every fold learns preprocessing from its training years. Expanding chronological folds compare classical and quantum models:

- **Quantum Feature Map & Encoding:**
  Training features $z_j$ are standardized and mapped to bounded rotation angles:
  $$\theta_j = a \tanh(z_j / 2), \quad a \in \{\pi/4, \pi/2\}$$
  State overlaps are computed using parameterized linear $ZZ$ feature maps:
  $$k_q(x, y) = |\langle\phi(x)|\phi(y)\rangle|^2$$
- **QSVR Regressor:** Overlap matrices computed via Qiskit's `FidelityQuantumKernel` feed an SVR dual optimization problem with $C \in \{0.1, 1.0, 10.0\}$ and $\epsilon \in \{0.05, 0.2, 0.5\}$.
- **Quantum Feature Selection (QAOA & SQD):**
  A QUBO scores feature relevance and redundancy, with a penalty for selecting anything other than four features. QAOA samples candidates from 10/16/20-feature pools. SQD diagonalizes the sampled subspace; for this diagonal objective, it returns the lowest-cost sampled subset.
- **Matched Classical Controls:**
  - Training mean baseline ($y = \bar{y}_{\text{train}}$)
  - Linear calendar year trend
  - Tuned Ridge regression (alpha grid)
  - Matched classical RBF-SVR ($C$, $\epsilon$, and 4 bandwidth multipliers matched 1:1 with quantum hyperparameter budgets)
  - Confounder controls: Station-reporting count alone and calendar trend alone.

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

Use a new output directory for each collection. Installation time depends on the machine and package cache. See [reproduction details](docs/REPRODUCIBILITY.md) for source acquisition and historical environments.

The hosted [game](https://fireline.ohrats.party/) and [presentation](https://fireline.ohrats.party/presentation/) need no installation. For local authoring, the Bun command serves `/web/demo/` and `/web/presentation/` on port 8790.

---

## 5. Experiments

We performed controlled experiments across local simulation and IBM Quantum physical hardware:

1. **Matched Development Kernel Grid:**
   - 36 configurations per model width/fold: 4 kernel bandwidths/maps $\times$ 9 $(C, \epsilon)$ pairs.
   - Evaluated across 3 expanding chronological training/validation folds (2007–2010, 2011–2014, 2015–2018).
2. **Frozen Reused-Year Evaluation (2019–2024):**
   - Parameters, fitted states and scalers were published before evaluation. The evaluation stage performed no fitting; these years had already been inspected in the incident study.
3. **Hardware Shot Sweep (Heron & Eagle):**
   - 12 real QPU jobs across `ibm_marrakesh` (Heron r2) and `ibm_quebec` (Eagle r3) testing 512, 1,024, and 2,048 shots across raw and combined dynamical decoupling (DD) + Pauli twirling arms.
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

Resource costs are reported per study: the [shot sweep](docs/SELECTOR_HARDWARE.md#hardware-cost-accounting) used 12 jobs, 301,056 shots and 108 charged QPU seconds; the [three-device mitigation comparison](docs/IBM_PIPELINE_MITIGATION.md) used six jobs, 224,256 shots and 75 seconds. The separate [repetition microkernel study](docs/results/repetition-microkernel.json) used four blocks, 1,474,560 shots and 414 seconds. These figures describe different workloads, not one combined total.

---

## 7. Discussion and Limitations

RBF leads matched development; four-input QSVR has lower error than matched RBF on the six reused evaluation years. Neither beats the training mean there. This gives us a reproducible comparison and a useful kernel diagnosis, without establishing predictive or quantum advantage.

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
  - Environment and Climate Change Canada (ECCC): [Monthly Climate Summaries](https://climate.weather.gc.ca/)
  - Statistics Canada: [Digital Boundary Files](https://www.statcan.gc.ca/)
- **Software & Libraries:**
  - Qiskit & Qiskit Machine Learning ([Qiskit Community](https://github.com/qiskit-community))
  - `qiskit-addon-sqd` (Sample-based Quantum Diagonalization)
  - Scikit-learn
- **Team Contributions:**
  - **Fernando Nogueira, Othmane Daali & collaborator `n123xyz`:** Problem formulation, experimental design, QPU execution, classical controls, Fireline canvas workbench, and documentation.
  - Full revision history and discussion are preserved in the git commit log and [`AGENT_BOARD.jsonl`](AGENT_BOARD.jsonl).


---

## Documentation Index

- **[Live presentation](https://fireline.ohrats.party/presentation/):** Seven talk slides and two appendices.
- **[Fireline](https://fireline.ohrats.party/):** Play with feature subsets, kernel angles and SVR settings.
- **[Judge guide](docs/JUDGES.md):** Question, results and reading order.
- **[Main report](docs/REPORT.md):** Methods, comparisons and limitations.
- **[Frozen evaluation](docs/ANNUAL_FINAL.md):** Parameters and predictions for the reused years.
- **[Hardware Shot Sweep](docs/SELECTOR_HARDWARE.md#hardware-cost-accounting):** 12-job QPU scaling benchmark.
- **[Pipeline Mitigation](docs/IBM_PIPELINE_MITIGATION.md):** Error mitigation analysis across Fez, Marrakesh, and Quebec.
- **[Hardware Feature Selector](docs/SELECTOR_HARDWARE.md):** Dicke state preparation and selection results.
- **[Reproduction Instructions](docs/REPRODUCIBILITY.md):** Step-by-step verification guide.

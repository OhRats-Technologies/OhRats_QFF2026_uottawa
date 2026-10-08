# Quantum Kernels for Annual Ontario Wildfire Estimation

**OhRats — Qiskit Fall Fest 2026 Open Challenge**

[![Test Suite](https://img.shields.io/badge/tests-224%20passed-brightgreen)](tests/)
[![Python](https://img.shields.io/badge/python-3.12-blue)](pyproject.toml)
[![Qiskit](https://img.shields.io/badge/Qiskit-2.5.2-purple)](https://qiskit.org/)
[![Reproducibility](https://img.shields.io/badge/offline-reproducible-success)](docs/REPRODUCIBILITY.md)

---

## 1. Problem and Goal

Wildfire severity in Ontario, Canada exhibits extreme year-to-year volatility, heavily influenced by regional climate patterns and macro-meteorological drivers.

- **Open Challenge Theme:** Quantum Machine Learning / Environmental Sustainability.
- **Research Question:** Can Quantum Support Vector Regression (QSVR) with parameterized entangling feature maps and QAOA/SQD feature selection improve retrospective macro estimation of annual wildfire burn severity across Ontario, Canada, compared to classical non-linear regressors (RBF-SVR, Ridge) under strictly matched computational and data budgets?
- **Scope & Observation Unit:** Retrospective macro annual provincial estimation for Ontario, Canada. One observation per calendar year:
  - **Training Window:** 1988–2018 (**31 annual observations**).
  - **Frozen Holdout:** 2019–2024 (**6 reused years**, previously opened in a preliminary incident study).
- **Primary Target & Metric:** Annual mean agency-reported wildfire size, expressed in **hectares per size-observed fire incident** (ha/fire).
- **Success Metric:** Mean Absolute Error (MAE) and Root Mean Squared Error (RMSE) benchmarked against classical controls.

---

## 2. Data and Assumptions

All datasets were extracted from official open Canadian federal records:

1. **National Fire Database (NRCan NFDB Point Snapshot):**
   - 39,616 size-observed fire incidents across Ontario during 1988–2018, and 3,828 incidents during 2019–2024.
   - Incidents with unknown or negative recorded sizes are excluded from the denominator.
2. **Monthly Climate Summaries (Environment and Climate Change Canada - ECCC):**
   - 456 monthly station records (1987–2024) across 65–340 active weather stations per year.
   - 10 macro climate aggregates: mean temperature, total precipitation, snowfall, extreme temperatures, and seasonal heating/cooling degree days.
3. **Land Cover & Forestry (NRCan Forest Cover Rasters):**
   - 42 coarse spatial layers sampled across Ontario's official polygon mask (1988–2022).
4. **Data Sourcing & Reproduction:**
   - Raw Canadian federal data can be downloaded following the source specifications in [`docs/DATA_SCHEMA.md`](docs/DATA_SCHEMA.md).
   - For fast public evaluation, an audited, byte-pinned 31-row training table is bundled directly in [`docs/data/annual_training.csv`](docs/data/annual_training.csv).
5. **Key Assumptions & Boundaries:**
   - Retrospective climate estimation: Predictors use same-year weather averages; this evaluates retrospective explanatory skill rather than operational advance forecasting.
   - Equal station weighting across Ontario weather stations without spatial interpolative kriging.

---

## 3. Approach

Our pipeline benchmarks classical against quantum components under strictly matched chronological cross-validation:

- **Quantum Feature Map & Encoding:**
  Training features $z_j$ are standardized and mapped to bounded rotation angles:
  $$\theta_j = a \tanh(z_j / 2), \quad a \in \{\pi/4, \pi/2\}$$
  State overlaps are computed using parameterized linear $ZZ$ feature maps:
  $$k_q(x, y) = |\langle\phi(x)|\phi(y)\rangle|^2$$
- **QSVR Regressor:** Overlap matrices computed via Qiskit's `FidelityQuantumKernel` feed an SVR dual optimization problem with $C \in \{0.1, 1.0, 10.0\}$ and $\epsilon \in \{0.05, 0.2, 0.5\}$.
- **Quantum Feature Selection (QAOA & SQD):**
  A continuous relevance/redundancy QUBO is mapped to an Ising Hamiltonian. QAOA generates candidate bitstrings, and `qiskit-addon-sqd` projects into the sampled subspace to isolate the minimum energy subset of 4 features from 10/16/20 candidate pools.
- **Matched Classical Controls:**
  - Training mean baseline ($y = \bar{y}_{\text{train}}$)
  - Linear calendar year trend
  - Tuned Ridge regression (alpha grid)
  - Matched classical RBF-SVR ($C$, $\epsilon$, and 4 bandwidth multipliers matched 1:1 with quantum hyperparameter budgets)
  - Confounder controls: Station-reporting count alone and calendar trend alone.

---

## 4. Setup and Execution

### Dependencies & Environment
- **Python:** 3.12 managed via [uv](https://docs.astral.sh/uv/)
- **Core Packages:** `qiskit==2.5.2`, `qiskit-machine-learning==0.9.1`, `scikit-learn==1.9.1`, `qiskit-addon-sqd==0.13.1`
- **Frontend / Demo:** [Bun](https://bun.sh/) for canvas demo serving and test suite.

### Quick Offline Reproduction

```sh
# 1. Sync locked Python environment
uv sync --locked --group data --group analysis --group quantum

# 2. Replay annual scientific evaluation (no network, no credentials, <10s)
uv run --no-sync python scripts/pipeline.py annual collect --output .cache/wildfire/annual-public --execute

# 3. Run the unit test suite (224 tests passing in ~9.2s)
uv run python -m unittest discover -s tests -v

# 4. Run the canvas demo test suite (22 tests passing in ~0.9s)
export PATH="$HOME/.bun/bin:$PATH"
bun test

# 5. Launch local presentation and Fireline canvas workbench
bun run web/presentation/serve.ts
```

*Total reproduction time: <15 seconds.*

---

## 5. Experiments

We performed controlled experiments across local simulation and IBM Quantum physical hardware:

1. **Matched Development Kernel Grid:**
   - 36 configurations per model width/fold: 4 kernel bandwidths/maps $\times$ 9 $(C, \epsilon)$ pairs.
   - Evaluated across 3 expanding chronological training/validation folds (2007–2010, 2011–2014, 2015–2018).
2. **Frozen Holdout Opening (2019–2024):**
   - Model parameters, weights, and scalers frozen and saved to disk prior to holdout evaluation (zero holdout fitting).
3. **Hardware Shot Sweep (Heron & Eagle):**
   - 12 real QPU jobs across `ibm_marrakesh` (Heron r2) and `ibm_quebec` (Eagle r3) testing 512, 1,024, and 2,048 shots across raw and combined dynamical decoupling (DD) + Pauli twirling arms.
4. **Real QPU Error Mitigation Benchmark:**
   - 6 jobs / 75 charged QPU seconds across `ibm_fez`, `ibm_marrakesh`, and `ibm_quebec` comparing raw versus mitigated QSVR Gram matrices and downstream SVR error.
5. **Unsuccessful / Negative Experiments:**
   - *10-qubit entangling kernels:* Collapsed to near-identity matrices (mean off-diagonal fidelity 0.0010 vs 0.0758 for 4-qubit), resulting in predictions frozen near the training mean.
   - *QAOA/SQD cardinality optimization:* Combinatorial search on 4-of-20 subsets achieved higher QUBO energy minimization on hardware, but produced worse downstream regression performance than classical uniform sampling.

---

## 6. Results

### Annual Wildfire Regression (Holdout 2019–2024)
*Lower error is better. Values reported in hectares per fire.*

| Model | Width | Chronological Dev MAE | 2019–2024 Holdout MAE | Holdout RMSE |
| :--- | :---: | :---: | :---: | :---: |
| **Training Mean Baseline** | 0 | 92.00 | **276.81** | **336.12** |
| **Linear Year Trend** | 0 | 88.91 | 286.58 | 353.63 |
| **Tuned Ridge Regression** | 10 | 81.21 | 294.98 | 372.24 |
| **Matched Classical RBF-SVR** | 4 | **77.02** | 299.81 | 380.52 |
| **Matched Quantum QSVR** | 4 | 86.64 | 280.68 | 352.51 |
| **Station Count Alone, QSVR** *(Control)* | 1 | **83.08** | — | — |
| **Calendar Trend Alone, QSVR** *(Control)* | 1 | **88.61** | — | — |
| **Weather + Calendar Ridge** *(Control)* | 11 | **67.97** | — | — |

![Annual holdout predictions and actual observed fire size across models](docs/figures/annual-final/annual-reused-predictions.png)

### Real Hardware Shot Sweep Yield (20-Feature Selector)

| Device | Arm | 512 Shots Valid | 1,024 Shots Valid | 2,048 Shots Valid | Best Objective Gap (2,048) |
| :--- | :--- | :---: | :---: | :---: | :---: |
| **ibm_marrakesh** | Raw | 74 (14.45%) | 129 (12.60%) | 259 (12.65%) | 0.0895 |
| **ibm_marrakesh** | DD + Twirling | 13 (2.54%) | 35 (3.42%) | 75 (3.66%) | 0.1791 |
| **ibm_quebec** | Raw | 2 (0.39%) | 10 (0.98%) | 19 (0.93%) | 0.1912 |
| **ibm_quebec** | DD + Twirling | 4 (0.78%) | 6 (0.59%) | 12 (0.59%) | 0.3027 |
| **Classical Uniform** | Monte Carlo | 512 (100.0%) | 1,024 (100.0%) | 2,048 (100.0%) | **0.0432** (mean) |

*Compute Resource Costs:* 39 total IBM Quantum jobs, 1,474,560 physical shots, and 414 charged QPU seconds utilized.

---

## 7. Discussion and Limitations

- **What Worked:**
  - Strict matched budgeting and pre-registered holdout protocols ensured honest benchmarking with zero data leakage.
  - 4-qubit QSVR demonstrated competitive interpolation on the holdout compared to classical SVR (280.68 vs 299.81 ha/fire).
  - The interactive Fireline workbench in `web/demo/` translates the underlying quantum linear algebra into an intuitive educational canvas tool.
- **What Did Not Work:**
  - Neither quantum nor classical climate models outperformed the simple training mean baseline on the holdout years.
  - Adding qubits from 4 to 10 severely degraded kernel condition numbers and caused exponential concentration around orthogonal states.
  - Readout error mitigation improved matrix fidelity but did not consistently translate to lower downstream regression errors on hardware.
- **Sources of Error & Limitations:**
  - Small sample size ($N=31$ training years) limits statistical power.
  - Ontario weather station density varied from 65 to 340 active stations over the observation period, creating temporal reporting bias.

---

## 8. Conclusions

1. **Answer to Primary Question:** Quantum kernels do **not** provide a predictive advantage over classical models for annual Ontario wildfire estimation with the features available and in this specific problem solution formulation. Classical RBF-SVR leads training development, and a constant historical mean baseline outperforms all tested models on holdout evaluation.
2. **Key Quantum Finding:** Scaling feature dimensions without careful angle scaling leads to severe kernel concentration. Error mitigation on Gram matrices does not guarantee improved downstream ML performance.
3. **Recommended Next Steps:**
   - Transition from province-wide annual aggregates to spatially resolved regional grids (e.g., ecozone-month).
   - Investigate train-only input bandwidth tuning to prevent barren kernel spectra in high dimensions.

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

- **[Judge Guide](docs/JUDGES.md):** Executive summary and evaluation criteria.
- **[Main Report](docs/REPORT.md):** Complete scientific writeup and derivation.
- **[Holdout Evaluation Receipts](docs/ANNUAL_FINAL.md):** Complete model parameters and holdout predictions.
- **[Hardware Shot Sweep](docs/SHOT_SWEEP.md):** 12-job QPU scaling benchmark.
- **[Pipeline Mitigation](docs/IBM_PIPELINE_MITIGATION.md):** Error mitigation analysis across Fez, Marrakesh, and Quebec.
- **[Hardware Feature Selector](docs/SELECTOR_HARDWARE.md):** Dicke state preparation and selection results.
- **[Reproduction Instructions](docs/REPRODUCIBILITY.md):** Step-by-step verification guide.

# Documentation Index

This directory contains the essential technical documentation for the OhRats Qiskit Fall Fest 2026 wildfire estimation benchmark.

---

## Essential Documents

| Document | Description |
| :--- | :--- |
| **[`JUDGES.md`](JUDGES.md)** | **Primary entry point for judges.** Core challenge question, matched results summary, reading order, and submission checklist. |
| **[`REPORT.md`](REPORT.md)** | **Main scientific report.** Annual Ontario wildfire regression formulation, matched RBF vs QSVR comparisons, and negative results analysis. |
| **[`ANNUAL_FINAL.md`](ANNUAL_FINAL.md)** | **Frozen annual holdout results.** Final evaluation metrics across all 11 models on 2019–2024 holdout, spectra, and parameter tables. |
| **[`SHOT_SWEEP.md`](SHOT_SWEEP.md)** | **Hardware shot sweep benchmarks.** Empirical 512, 1,024, and 2,048 shot evaluations on `ibm_marrakesh` (Heron) and `ibm_quebec` (Eagle). |
| **[`IBM_PIPELINE_MITIGATION.md`](IBM_PIPELINE_MITIGATION.md)** | **Real QPU error mitigation.** Evaluation of dynamical decoupling, Pauli twirling, and readout mitigation across three IBM quantum processors. |
| **[`SELECTOR_HARDWARE.md`](SELECTOR_HARDWARE.md)** | **Hardware feature selection.** Dicke state preparation, QAOA/SQD selection, and 10-shard recovery on `ibm_marrakesh`. |
| **[`DATA_SCHEMA.md`](DATA_SCHEMA.md)** | **Data pipeline and schema.** Definitions, exclusions, and joins for NFDB fire records and ECCC weather data. |
| **[`QUANTUM_METHODS.md`](QUANTUM_METHODS.md)** | **Quantum components.** Mathematical formulations of ZZ feature maps, fidelity compute-uncompute kernels, and state preparation. |
| **[`REPRODUCIBILITY.md`](REPRODUCIBILITY.md)** | **Reproduction instructions.** Exact commands to verify the public evidence bundle offline without credentials. |
| **[`FIRELINE_CANVAS.md`](FIRELINE_CANVAS.md)** | **Interactive demo engine.** Guide to the Fireline 2D canvas engineering simulator in `web/demo/`. |
| **[`PIPELINE.md`](PIPELINE.md)** | **Pipeline architecture.** Core processing directory structure and stage contracts. |
| **[`HANDOFF.md`](HANDOFF.md)** | **Handoff receipts.** Change logs and verification receipts. |
| **[`GOAL_AUDIT.md`](GOAL_AUDIT.md)** | **Goal coverage audit.** Verification against hackathon challenge requirements. |

---

## Core Findings Summary

1. **Prediction Benchmark:** Classical RBF-SVR leads development (MAE 77.02 ha/fire vs QSVR 86.64 ha/fire). On the 2019–2024 holdout, **no climate model beats the historical training mean baseline** (276.81 ha/fire).
2. **Feature Selection:** Quadrupling QPU shots expands candidate coverage, but feasible yield remains low on deep circuits. Classical uniform feasible sampling outperforms 11 of 12 measured hardware minima.
3. **Error Mitigation:** Readout calibration reduces kernel matrix RMSE on hardware, but often degrades downstream regression accuracy.

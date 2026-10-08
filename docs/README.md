# Documentation Index

[Play Fireline](https://fireline.ohrats.party/) · [View the presentation](https://fireline.ohrats.party/presentation/)

Start with the judge guide for the findings, the report for methods, or reproduction for a saved-evidence check.

---

## Essential Documents

| Document | Description |
| :--- | :--- |
| **[`JUDGES.md`](JUDGES.md)** | Question, main findings and a five-minute reading route. |
| **[`REPORT.md`](REPORT.md)** | Annual dataset, matched RBF/QSVR comparison and failure analysis. |
| **[`ANNUAL_FINAL.md`](ANNUAL_FINAL.md)** | Saved parameters, spectra and errors for 11 main models on six reused evaluation years. |
| **[`SHOT_SWEEP.md`](SHOT_SWEEP.md)** | 512/1,024/2,048-shot comparisons on Marrakesh and Quebec. |
| **[`IBM_PIPELINE_MITIGATION.md`](IBM_PIPELINE_MITIGATION.md)** | DD, twirling and readout correction on three IBM devices. |
| **[`SELECTOR_HARDWARE.md`](SELECTOR_HARDWARE.md)** | Dicke preparation, QAOA/SQD and measured predictor kernels. |
| **[`DATA_SCHEMA.md`](DATA_SCHEMA.md)** | NFDB/ECCC definitions, exclusions and joins. |
| **[`QUANTUM_METHODS.md`](QUANTUM_METHODS.md)** | ZZ encoding, fidelity kernels and state preparation. |
| **[`REPRODUCIBILITY.md`](REPRODUCIBILITY.md)** | Saved-evidence checks and source reconstruction commands. |
| **[`FIRELINE_CANVAS.md`](FIRELINE_CANVAS.md)** | Game design, browser calculations and dated verification receipts. [Play online](https://fireline.ohrats.party/). |
| **[`PIPELINE.md`](PIPELINE.md)** | Commands, stages and outputs. |
| **[`HANDOFF.md`](HANDOFF.md)** | Current entry points followed by historical closeout receipts. |
| **[`GOAL_AUDIT.md`](GOAL_AUDIT.md)** | Historical scope and requirement checks. |

---

## Core Findings Summary

1. **Prediction:** Classical RBF-SVR leads development (MAE 77.02 ha/fire vs QSVR 86.64 ha/fire). On the six reused 2019–2024 evaluation years, **no main climate model beats the historical training mean baseline** (276.81 ha/fire).
2. **Feature Selection:** Quadrupling QPU shots expands candidate coverage, but feasible yield remains low on deep circuits. Classical uniform feasible sampling outperforms 11 of 12 measured hardware minima.
3. **Error mitigation:** In the three-device diagnostic, readout calibration lowers kernel RMSE but raises downstream prediction error. DD/twirling does not consistently help.

The [game README](../web/demo/README.md) and [presentation README](../web/presentation/README.md) cover controls and local serving. [Hosting notes](../deploy/fireline/README.md) describe the Coolify deployment. The separate [repetition microkernel results](results/repetition-microkernel.json) and [figure](figures/repetition-microkernel.png) retain their four-block hardware measurements.

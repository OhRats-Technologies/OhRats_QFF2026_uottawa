# Judge guide

**Question:** Can quantum kernels improve retrospective annual Ontario wildfire-size estimation under a matched budget?

**Answer:** No. Classical RBF leads matched development (MAE 77.02 ha/fire vs QSVR 86.64); on the 2019–2024 holdout, no tested climate model beats the historical training mean (276.81 ha/fire). The primary quantum finding is a concrete encoding-scale and conditioning trade-off rather than predictive advantage.

**Hardware Reality (39 QPU jobs across Heron and Eagle):**
- **Shot scaling:** Increasing shots expands candidate coverage, but does not increase feasible yield on deep circuits (~1,000 CZ gates). Classical uniform sampling outperforms 11 of 12 measured hardware minima ([shot sweep](SHOT_SWEEP.md)).
- **Error mitigation:** Readout calibration and twirling lower Gram matrix RMSE, but downstream regression error often worsens despite lower matrix error ([pipeline mitigation](IBM_PIPELINE_MITIGATION.md)).
- **Feature selection:** Higher QAOA/SQD objective coverage does not produce better downstream predictive accuracy, while classical subset enumeration is instantaneous ([selector hardware](SELECTOR_HARDWARE.md)).


## Reading Order for Judges

1. **[README](../README.md):** Quick overview of research questions, data pipeline, QPU benchmarks, and offline reproduction commands.
2. **[Slide Deck](../web/presentation/README.md):** Hackathon presentation with interactive QPU benchmarks and speaker notes.
3. **[Fireline Interactive Demo](../web/demo/README.md):** Browser workbench demonstrating feature selection, kernel Gram matrices, and error mitigation.
4. **[Main Report](REPORT.md):** Controlled empirical study, methodology, mathematical formulations, and negative results.
5. **[Frozen Evaluation](ANNUAL_FINAL.md):** Complete benchmark tables across all 11 models on 2019–2024 holdout.

## Measured Evidence Summary

- **Dataset:** 31 annual observations (1988–2018) for chronological training; 6 years (2019–2024) for evaluation.
- **Features:** Audited NRCan National Fire Database (39,616 training fires) + ECCC Monthly Climate Summaries (10 summaries from 65–340 weather stations).
- **QPU Execution:** 39 IBM Quantum hardware jobs across `ibm_fez`, `ibm_marrakesh` (Heron), and `ibm_quebec` (Eagle) with zero unrun claims.

## Submission Checklist

- [x] **Self-contained README:** Offline reproduction with `uv` and zero credentials required.
- [x] **Slide Presentation:** 9-slide deck in `web/presentation/` with speaker notes.
- [x] **Interactive Simulator:** Fireline canvas workbench in `web/demo/`.
- [x] **Public Scientific Code:** Complete pipeline in `wildfire_lab/` and `scripts/`.
- [x] **Unit & Verification Tests:** 224 automated test cases passing in CI / local test runner.
- [x] **Challenge Deadline:** October 7, 2026, 11:59 PM ET.


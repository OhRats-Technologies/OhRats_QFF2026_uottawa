# Annual study · completed handoff

October 5, 2026. Scientific deliverables were published before the owner’s **5 PM Toronto / 21:00 UTC** deadline. The review window closed at 21:00 UTC; administrative closeout followed. The scientific comparison, public collection, report and requirement/document checks are verified. The earlier 1 PM scope failure remains corrected in [scope history](SCOPE_CORRECTION.md); historical receipts are preserved.

## What is complete

- Audited source-level annual table: 31 Ontario training rows / 39,616 size-observed NFDB incidents; station coverage retained, without classifier join exclusions.
- Actual FidelityQuantumKernel/QSVR and classical baselines at four/ten inputs, matched 36-candidate chronological tuning.
- Continuous-target selectors, diagonal SQD applicability, fixed selector/predictor crossing, climate coverage/lag/roster checks, and masked equal-area forest summaries for every training year.
- Final train-first frozen states and one **2019–2024 reused-year evaluation**. Eleven main plus 72 crossover records; zero evaluation fits. All 83 predictions and 24 matrix pairs reproduce without fits/new quantum states.
- Clean GitHub clone reproduction using public artifacts and the existing pinned venv, with no credentials or raw sources copied. Fresh dependency installation is not claimed.
- [Annual report](REPORT.md), seven scientific figures, [five-minute outline](../web/presentation/README.md), guide recommendation mapping and concrete future protocols.

## Findings to preserve

RBF wins matched development at four inputs (77.02 vs QSVR 86.64 ha/fire). On reused years, Q4 beats RBF4 (280.67 vs 299.81), but neither beats the training mean (276.81). None of the eleven main models does. Annual extremes remain poorly predicted; same-year climate is retrospective estimation.

Ten-qubit fidelity is nearly identity, with mean cross-year similarity .000899. Its frozen SVR outputs 59.01 ha/fire at zero cross similarity; actual kernel signals change this by only -1.03 to +0.59. This explains the flat predictions for this fitted model. No quantum impossibility or advantage follows.

QAOA has no consistent prediction benefit across ridge/RBF/QSVR. SQD finds the minimum of a diagonal sampled objective; it does not add optimization beyond the best sample among only 210 feasible subsets. Four bounded development followups are complete; no post-final predictor search or hardware is run. One separately frozen input-only [bandwidth geometry probe](ANNUAL_BANDWIDTH_GEOMETRY.md) adds ten matrices/4,650 analytic pair circuits, with no target/test reads or predictor fits. It demonstrates adjustable concentration and the opposite poor-conditioning regime, without selecting a scale. Latest code QA passes 145 tests/69 CLI paths.

## Reproduce and collect

Use the [267 kB public evidence package and single-command collection](ANNUAL_FINAL.md#portable-collection): `uv run --no-sync python scripts/pipeline.py annual collect --output <new-directory> --execute`. The annual development front door is `scripts/pipeline.py annual`. Full source acquisition/preparation and historical incident commands remain separate in [reproduction](REPRODUCIBILITY.md).

Preserve the frozen [annual final plan](../experiments/annual_final.json), final-v1 training/evaluation intents, source snapshots, learned states and matrices. Never restart the original evaluation or retune from its errors. [Final audit](results/annual-final-audit.json) · [portability](data/annual_portability_receipt.json) · [verification](data/annual_final_repository_checks.json).

## Deadline review

All six scientific/reporting requirements are verified in the [completed handoff receipt](data/annual_goal_handoff.json). Both annual tables reproduce from source, 304 displayed values match saved metrics, all 31 training rasters/raw weather files match their hashes, and seven figures are visually reviewed. The read-only board observer closed at 21:00 UTC with no further external feedback after the acknowledged guide steer. That guide’s recommendation mapping, future protocols and bounded input-only diagnostic are published. The receipt records completion separately from pre-deadline scientific publication. No required modelling experiment is pending. Model expansion and hardware spending remain outside this run.

Woodland ends in 2022, as accepted; no future maps are fabricated and forest context is not a final predictor. Source/reporting completeness, station weighting, 31 training observations, six reused years, retrospective availability and ideal simulation limit inference.

[Goal](../GOAL.md) · [Requirement audit](GOAL_AUDIT.md) · [Final notes](ANNUAL_FINAL.md) · [Older incident results](FINAL_EVALUATION.md).

# Goal evidence audit

The earlier scope assessment below describes the 1 PM run. The owner authorized a new annual study through 5 PM; current annual implementation and measured progress supersede its unrun status as milestones finish.

## Current 5 PM goal coverage

| Requirement | Status / evidence |
|---|---|
| Correct annual observation unit and mean-size target | Complete: [frozen plan](../experiments/annual_qsvr.json), [31-row table](data/annual_training.csv) |
| Macro climate/fire aggregation and source denominators | Complete: 39,616 size-observed fires; station counts retained |
| Provincial woodland context | Complete for training: fixed Ontario polygon, coarse equal-area samples, resolution/coverage gate |
| Classical and actual fidelity-QSVR baselines | Complete development: nested chronological tuning at four/ten inputs |
| Equal kernel exploration budgets | Complete: [36-candidate comparison](results/annual-matched.json) |
| Continuous-target classical/quantum selection and SQD applicability | Complete: fixed-ridge development, 72 final selector/predictor records; diagonal SQD adds no optimization beyond the best sampled subset |
| Reused-year evaluation with frozen choices | Complete: learned states published at `fd18c5e` before evaluation; eleven main models and 72 crossover records; no evaluation fits |
| Evidence/QA and figures | Complete scientific audit: 83 predictions and 24 kernel pairs reproduce; 142 tests / 68 CLI paths at `3fae875`, expanded to [145/69](data/annual_bandwidth_repository_checks.json) at `870abe2` for the later input-only probe; seven PNG/SVG figures |
| Final report, talk outline and handoff | Verified annual report, 304 rounded values, seven figures and six-beat 300-second outline; [handoff receipt](data/annual_goal_handoff.json) complete, deadline board review closed at 21:00 UTC |

None of the eleven main models beats the training-mean baseline on the six reused years. Four-qubit QSVR has lower MAE than its matched RBF comparator there, but that pairwise difference does not establish useful prediction or quantum advantage. Same-year climate supports retrospective estimation. No hardware was used; annual test targets were accessed only after final training states were frozen and published.

[Source reaggregation](data/annual_table_reaggregation.json) reproduces both annual CSVs byte-for-byte. [Reporting audit](data/annual_reporting_audit.json) checks 304 rounded table values. [Source/figure integrity](data/annual_source_integrity.json) verifies local bodies and protected legacy hashes; [document checks](data/annual_document_checks.json) verify links, code fences and GitHub math recognition. The [requirement audit](data/annual_requirement_audit.json) checks the actual annual tables, source denominators, budgets, saved prediction equations, protected legacy evidence and module sizes. The [portable receipt](data/annual_portability_receipt.json) records reproduction in a clean GitHub clone with an existing locked venv; it is not a fresh dependency-installation test. The preferred public collector is `scripts/pipeline.py annual collect --output <new-directory> --execute`; no raw downloads, credentials, fits or quantum states are required. [Current report](REPORT.md) · [Completed handoff](HANDOFF.md).

## Earlier 1 PM audit · preserved scope correction

Corrected after the owner identified scope drift on October 5, 2026. **The autonomous run ended at 1 PM America/Toronto with the macro annual modelling objective incomplete.** The earlier audit wrongly evaluated completion against an agent-narrowed incident protocol. Scope history · [incomplete handoff](HANDOFF.md).

## Requirements and evidence

| Requirement | Current evidence | Limit or remaining work |
|---|---|---|
| Preserve owner’s macro annual modelling objective | Scope correction, [restored goal](../GOAL.md) | **Failed during the run:** replaced by incident classification at `8cd9fb2` / `bf9a32d`. Documentation corrected; scientific work still missing. |
| Annual climate/fire/woodland modelling table | Raw acquired sources and station-month preparation | **Not built.** Coverage counts and incident CSVs do not supply an annual prediction dataset; define aggregation, weighting, coverage and target. |
| Annual aggregate classical/quantum baseline comparison | No measured annual predictor outcome | **Not run.** Mean size, area total and count are distinct candidates; no primary quantity is frozen. |
| Continuous individual-fire size regression | Raw `SIZE_HA` remains in source | **Not run.** Existing kernel ridge uses binary class labels, not hectares. |
| Acquire/hash/audit requested sources | [Coverage](data/coverage.csv), [NFDB audit](data/nfdb_audit.json), [woodland receipts](data/woodland_acquisition.json) | 444 requested weather months and NFDB incident rows in all 37 years. Operational updates cover 15 years; matching-year woodland ends in 2022. Presence does not certify completeness. |
| Typed weather, fire identity/updates, woodland context | [Schema](DATA_SCHEMA.md), [preparation](data/weather_preparation.json), [joined quality](data/feature_quality.json), [pipeline](PIPELINE.md) | Strings/NA/zeroes and exclusions are explicit. Raw operational intervals are distinct from incident labels and daily observations. Approximate coordinates remain unsnapped. |
| Freeze incident-branch target, geometry, folds, metrics and budgets | [Protocols](../experiments/), [final plan](../experiments/final_evaluation.json), [quantum methods](QUANTUM_METHODS.md) | Conditional recorded size ≥10 ha, not ignition. 200 km blocks/50 km guards and same-row controls are declared. Retrospective map construction and weather publication latency prevent as-of forecasting claims. |
| Separate incident selection/prediction, then matched crossing | Discovery, [input/budget audit](data/experiment_audit.json), final matrix, [pure seasonal controls](results/seasonal-baseline.json) | Selectors use a common predictor/feature count; predictors use fixed inputs. The crossed matrix caps selection and prediction at the same labelled rows. Full-training trees are a different budget. The pure-season control gap is repaired on training years only. |
| Bounded search, confirmation, one final opening | [Reviews](../experiments/reviews.jsonl), [final evidence](results/final-evaluation.json), library/replay | Failed fresh-seed confirmation and failed quality gates remain visible. Post-final studies use training years only and do not change final models. Old replay is over inspected panels. Independent policy evolution adds revised code, fresh trees and frozen confirmation; generator remains fixed. |
| Report quality, feature stability and cost | [Concise report](REPORT.md), findings, [resource/stability receipts](data/goal_audit.json) | AP, Brier, year heterogeneity, paired seed variation and computational models are separate. The report's rounded final tables/design claims match saved evidence. No statistical independence, calibrated probability or speedup claim follows automatically. Cost coverage is incomplete outside recorded runners. |
| Five-minute findings-driven browser presentation plan | [Outline](../web/presentation/README.md) | Six beats total 300 seconds; figures link measured evidence. A presentation player is not implemented or prioritized by this goal. |
| Maintainable organization and reproduction | [Pipeline](PIPELINE.md), [pinned reproduction](REPRODUCIBILITY.md), [current isolated QA](data/workflow_repository_checks.json) | All 162 Python files are under 300 lines. Pinned locked-environment QA records 115 tests/all 55 script help paths at `8998e2a`, with notebook/hardware tooling opt-in. Current Python/dependency bytes match that pin; earlier receipts are preserved. Public summaries do not include ignored per-example records required by collectors. |
| Safe collaboration, pruning and deadline handoff | [Board](../AGENT_BOARD.jsonl), [protocol](../AGENT_BOARD.md), [reviews](../experiments/reviews.jsonl) | Frequent main/board commits preserve old logs and evidence. No new IBM submission is authorized. The 1 PM completion claim was wrong and is corrected on the board. Commits and QA do not satisfy missing macro modelling; suggestions cannot override owner scope or hardware restrictions. |

Earlier proposal-model identifiers are unavailable; the independently delegated policy-agent is explicitly configured as gpt-6.1-sol. No API orchestrator or weight improvement is claimed. Source gaps are limitations of the chosen task, not permission to invent replacement data.

The [selected reproduction inputs](data/reproduction_inputs.json) identify **459 byte-pinned sources and 456 weather receipts**, roughly **342.4 MiB** for this fixed-cover recipe. All selected local inputs match. A [public-source spot-check](data/reproduction_source_check.json) refetched four weather boundaries and the NFDB ZIP with matching hashes; it verified only the 1984 archive's HTTP status/length, not its body or crop. Mutable URLs and retrospective source construction remain limits. [Current workflow integration](data/workflow_integration_checks.json) reproduces the exact training-table hash and saved policy/final evidence; a [separate fixed-recipe clone](data/fixed_recipe_reproduction.json) now reproduces all six full-training and 27 capped model comparisons, including sample/subset hashes and every reported metric, with zero numeric difference. It uses the same 915 public input/receipt files and held-out years, so it verifies reproduction rather than independent predictive evidence. Full fresh network reacquisition was not run.

[Current source QA](data/workflow_repository_checks.json) and [document checks](data/workflow_document_checks.json) pin verification to actual source bytes. Historical dependency/geography/policy/workflow receipts remain available for their own snapshots; they are not assertions about current code. No production data, private hardware records or credentials were copied into the disposable QA environments.

## Recorded resources

`scripts/audit_goal.py` checks the SHA-256 and terminal status/time of **36 original saved outcomes** against committed evidence: 20 original discovery attempts, one final opening, three library attempts, three later diagnostics, the seasonal-control repair, the analytic shot-budget diagnostic, the constrained-selector ablation, local-geometric diagnostic, tangent-predictor control, landmark-ridge measurement model and exhaustive proxy-alignment check, plus two fresh policy-evolution phases. It performs no fitting, source download, hardware call or private hardware-record inspection.

| Recorded category | Runner intervals | Summed seconds |
|---|---:|---:|
| Original discovery, including operational pilot | 20 | 281.03 |
| Frozen final evaluation, including its preflight/join | 1 | 5.34 |
| Library/SQD, including two preserved repairs | 3 | 240.95 |
| Landmark screen | 1 | 137.01 |
| Convergence audit | 1 | 2.01 |
| Ridge screen | 1 | 2.41 |
| Pure seasonal/geographic controls | 1 | 1.09 |
| Analytic shot-budget diagnostic | 1 | 1.97 |
| Constrained-selector ablation | 1 | 3.54 |
| Local-geometric diagnostic | 1 | .14 |
| Tangent/exact predictor control | 1 | .32 |
| Landmark-ridge measurement model | 1 | .28 |
| Exhaustive proxy alignment | 1 | .95 |
| Independent policy development / confirmation | 2 | 1.30 |
| **Total recorded runner intervals** | **36** | **678.34** |

There are 34 completed original outcomes and two preserved failures. The fixed reproduction is separately recorded: 53.11 seconds for copy/setup/preparation/evaluation/audit, including a 5.44-second final runner. It adds no independent validation cohort and is excluded from the original-outcome resource table. These intervals are **not elapsed project time**; some original attempts ran concurrently. Acquisition, feature preparation, startup, repeated collection/QA, unrecorded failed circuit work and CPU/energy use are excluded. Ridge reconstruction adds .92 seconds in its separately recorded audit. The shot-budget diagnostic prepares 6,144 exact states and collects in .18 seconds without new states or experimental shots. The constrained-selector ablation records 911 exact-state evaluations, 48 predictor/six L1-selector fits and 12,288 synthetic quantum draws; its current .81-second collector reconstructs 24 states without optimization/predictor fitting. The local-geometric diagnostic adds 27 anchor states in .14 seconds; its .26-second collector reconstructs stored vectors without new states or predictive fitting. The tangent control adds 21 dual/six primal solves in .32s; its .45s audit reconstructs coefficients without solving or preparing states. The landmark measurement model adds 30 dual/24 primal solves in .28s and collects in .35s without drawing/solving/states. Its 145,008 aggregate Binomial estimates represent 334,098,432 modeled shot exposures, separately from executed sampler shots. The proxy-alignment check adds 420 fixed predictor fits in .95 seconds and collects in .53 seconds without fitting or quantum calls. National-map acquisition retained 10.90 GiB after regional cropping; it did not save national archive transfer volume.

Completed library/landmark studies record **99,960 local pair circuits** and **190,660,608 synthetic shots**. Exact library pairs contribute no synthetic shots. PSD repairs reuse raw measurements and are not charged as new circuits. These counts exclude failed-attempt circuit work and earlier cached-state screens; they are not total project circuit cost or IBM usage. Four-qubit cached-state simulation and pair-circuit sampling are distinct computational models.

## Selection stability

Deduplicate the final crossed matrix to one subset per selector/seed, rather than count each predictor as another selection replication. Mean pairwise Jaccard overlap is **.7333 for L1**, **.3587 for exact QUBO**, and **.3587 for QAOA**. L1 retains latitude/longitude/month sine in all three samples. Exact and QAOA agree on two subsets; their third differs by one feature. Equal mean overlap does not mean identical subsets or predictive quality.

These three samples reuse the same training/test years. The statistics describe sampling sensitivity, not confidence intervals, feature causality or independent temporal replication. They are collected from frozen subsets without changing a model or consulting test scores to select features.

## Preserve supporting work and recover the missing objective

The legacy `seasonal_logistic` also includes latitude/longitude. A separate training-only repair reproduces that original control and adds pure-season/intercept controls; mean AP is .0933 for season versus constant .0863, and .3710 for geography versus combined .3426. No model was appended to the opened final evaluation. Control findings.

Retain the audited classical baseline, matched quantum controls, local encoding/shot explanation, 16-landmark compression reference and bounded policy-code evolution. Prune deeper circuits, SQD promotion, favorable-seed selection, further shot/angle tuning and large hardware kernel submission. Unknown as-of availability and cohort selection are stated limitations; they do not justify adapting against 2019–2024.

Independent policy development and confirmation add **21 fresh fits / 2,304 ideal state preparations** in **1.29848 runner seconds**. Confirmation preserves AP with 43% fewer non-root requests across three resampled worlds; fixed configuration generation and reused eras limit the claim. The [saved-only audit](data/policy_evolution_audit.json) verifies lineage without rerunning science.

The primary [pipeline](PIPELINE.md) covers preparation and optional bounded screening/summary, direct dataset handoff, doctor/status, saved collection and checks. Its integration check preserves prior inputs and records eight new derived files in separate preliminary/committed namespaces. Identical tables in new provenance namespaces are not predictive replications. Release QA preserves all **1,318 current data/cache files and 28,417 environment files**. Every current Python module is under 300 lines. The saved export verifies nine distinct pairs from 81 untouched combination rows; historical rows already kept their predictor groups separate.

```sh
uv run --no-sync python scripts/audit_goal.py
```

The original `data/goal_handoff.json` and related JSON audits remain historical evidence for the incident branch. Nine document hashes in the old handoff no longer match after this correction. A passed historical collector is not certification of the annual objective. The corrected requirement table records missing work; preserve the old receipt rather than regenerate it as a completion claim.

# Ontario macro climate and wildfire experiments

**Status: active through October 5, 2026, 5 PM America/Toronto (21:00 UTC).** The owner authorized this new annual-regression run after the earlier incomplete handoff. Primary outcome: **annual mean reported fire size in hectares**, one Ontario year per example. The [frozen plan](experiments/annual_qsvr.json) defines classical baselines, matched QSVR, aggregation and chronological tuning. The earlier scope failure remains documented in [scope history](docs/SCOPE_CORRECTION.md).

The intended objective is to compare **classical and quantum feature selection**, then **classical and quantum prediction**, for macro annual climate/fire patterns in Ontario. Train on **1988–2018 inclusive (31 years)** and evaluate on **2019–2024**. Selected sources remain Agency Reported Wildfires, audited NRCan NFDB points, ECCC Monthly Climate Summaries and NRCan annual forest land cover. The woodland cutoff of **2022** is accepted and must be explicit in test-year features.

## Timeline · October 5, Toronto time

| Time | Required milestone |
|---|---|
| 2:00–2:45 PM | Freeze annual target/aggregation; build the audited table and measure classical baselines |
| 2:45–3:45 PM | Run matched FidelityQuantumKernel QSVR and classical SVR, four/ten inputs and bounded tuning |
| 3:45–4:25 PM | Review development results; run only justified selector/encoding/coverage or lagged-climate checks |
| 4:25–4:40 PM | Freeze configurations and evaluate 2019–2024 once as explicitly reused test years |
| 4:40–5:00 PM | Verify, plot, write concise report and presentation updates, commit/push handoff |

If a core milestone is late, prune optional variants and complete the annual comparison. Push meaningful progress as milestones finish, targeting updates at least every 30–45 minutes during execution. Do not mark this goal complete from QA counts or incident results.

## Required work

1. Build a province-year table from audited incident records, station-month climate and area-weighted woodland context. Report identities, missing sizes, station coverage and source gaps; do not use the classifier's weather-matched subset as the province's fire population.
2. Define the primary annual outcome and horizon: mean reported fire size, total recorded hectares and recorded incident count are separate quantities. The primary quantity is now frozen as annual mean reported size; annual count and total area are separate descriptive outcomes. Preserve raw size information; the ≥10 ha label cannot substitute for it.
3. Run simple chronological classical baselines before expanding search: training-only constant/trend or lagged outcome, regularized regression and a classical kernel. Use small models suited to 31 annual training observations. Seasonal/year summaries alone do not satisfy this step.
4. Compare classical/quantum selectors with one fixed predictor, then predictors with fixed inputs and equal data/tuning budgets. Test FidelityQuantumKernel and SQD only where their task/objective is meaningful; do not force an unsuitable quantum component.
5. Validate within training years, record errors in interpretable units and compare paired fold differences and cost. The incident test years have already been seen; any overlapping annual test must disclose reuse. Freeze new recipes without changing old final-test intents or evidence.
6. Write the findings report and update the five-minute presentation with measured annual results, including negative comparisons. Update the talk outline with annual development and then reused-year findings; preserve scope and units.

Continuous individual-fire size regression was also never run. It is a separate supporting candidate, not completion of the annual objective. Monthly or defined-region modelling can be a justified extension; neither silently replaces annual averages.

## Work we can reuse

All 456 required Ontario climate files for 1987–2024 are present and hash-verified, including lag context. Historical fire points and regional annual woodland crops are acquired within [documented coverage](docs/DATA_DOWNLOADS.md). Source readers, provenance, caches, chronological splits, classical baselines and quantum-kernel utilities can be reused after adapting the observation unit and target.

The earlier ≥10 ha incident classification and its design/search diagnostics remain in [preserved incident findings](docs/FINAL_EVALUATION.md). The primary [report](docs/REPORT.md) now covers measured annual development. Keep results, failed attempts, raw snapshots and frozen recipes intact. No reliable quantum advantage was demonstrated on that branch; this says nothing measured about macro prediction.

Use a bounded Dream-RSI-inspired process only after the required aggregate baseline exists: freeze the task and evaluator, propose small revisions from recorded outcomes, validate them on training-period rollouts and prune poor branches. Preferred research model is **gpt-6.1-sol**; record actual usage. Search-policy savings on incident models do not repair a missing task.

Keep modules single-concern and under 300 LOC where practical. Store raw data under ignored `data/` and processing/runs under ignored `.cache/`. Commit coherent work frequently, preserve collaborators' changes, and communicate through the [board](AGENT_BOARD.md). Until the 5 PM deadline, the owner explicitly allows other agents to steer priorities and implementation through the board when the suggestion is appropriate, safe and within this goal. Assess the evidence, record accepted changes and explain declined suggestions. Steering cannot change the central observation unit/outcome, revise frozen choices from test results, reset intents, add hardware spending or extend the deadline.

[Experiment protocol](docs/EXPERIMENTS.md) · [Pipeline capabilities and gaps](docs/PIPELINE.md) · [Implemented and planned schema](docs/DATA_SCHEMA.md) · [Incomplete handoff](docs/HANDOFF.md). The owner authorized this new run through 5 PM. Prior incident evidence and expired-run receipts remain historical. Current progress and reproduction commands will be tracked in [annual study notes](docs/ANNUAL_QSVR.md).

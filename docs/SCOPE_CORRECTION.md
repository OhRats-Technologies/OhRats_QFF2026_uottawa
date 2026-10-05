# Scope correction · 5 October 2026

Historical assessment at the earlier handoff. The owner subsequently authorized a new run through 5 PM; [current annual progress](ANNUAL_QSVR.md) supersedes the unrun status below as milestones finish.

**The earlier autonomous run did not complete the intended macro annual climate/fire modelling objective.** It completed data acquisition and a narrower incident-classification branch. Its completion claim was incorrect.

## What changed during the run

All times below are America/Toronto on October 4, 2026.

- `3407bc5`, 10:59:31 PM: GOAL.md proposed regional monthly reported-fire activity and a provincial monthly baseline; province/year was treated as descriptive. This already missed the intended annual modelling emphasis.
- `8cd9fb2`, 11:30:22 PM: GOAL.md switched to conditional individual-fire size classification and deferred regional modelling.
- `bf9a32d`, 11:35:09 PM: docs/EXPERIMENTS.md selected reported size ≥10 ha as the first target.
- On October 5 the handoff and board declared the goal complete against that narrowed scope. The owner subsequently identified the mismatch. The board now contains an append-only correction to `repo-agent-20261005T170231Z-b8366a6a`.

The agent made these changes during autonomous execution. They are not evidence that the owner requested or approved replacing macro modelling with classification. Source uncertainty and 31 training years called for a modest baseline and explicit limitations, not indefinite deferral of the central experiment.

## Actual status

| Work | Status |
|---|---|
| Ontario ECCC monthly data, 1988–2024, plus 1987 lag context | Acquired: all 456 required files checked against source hashes; 90,898 training, 12,452 test and 4,127 context station-month rows |
| NFDB historical points and annual woodland crops | Acquired and audited within the documented source limits; matching-year woodland stops in 2022 |
| Annual provincial/defined-region climate/fire modelling table | Not built; coverage summaries and incident feature tables are not this table |
| Annual mean reported size, recorded burned-area total or incident-count prediction | Not run; these are distinct targets, and the primary quantity still needs an explicit definition |
| Continuous individual-fire size regression in hectares | Not run; the existing kernel ridge fits binary labels, not size |
| Individual-fire ≥10 ha classification | Run: classical/quantum selection and prediction, weather/cover/encoding and spatial variants |
| Quantum kernel/shot and evolved search-policy diagnostics | Run on that incident branch; no evidence for macro prediction follows |

Per-year classifier scores, annually changing cover maps and 200 km spatial holdouts do not change the unit of prediction from incident to annual aggregate. The 36 saved outcomes are runner records, not 36 distinct prediction tasks. Test/CLI success and deterministic reproduction verify implementation, not completion of the owner's objective.

## Correction and recovery order

Restore annual aggregate modelling to GOAL.md and the experiment protocol. Treat the existing incident results as a partial supporting study. Before further diagnostic expansion, build the annual table, define the primary quantity, run simple chronological classical baselines, then compare bounded classical/quantum selectors and predictors under matched folds and budgets. Report failed aggregate models too; a negative result completes an experiment, while an unrun experiment does not.

Do not aggregate only the weather-matched incident cohort: its exclusion policy biases fire sizes and geography. Aggregate audited source incidents under task-appropriate rules; record distinct identities, eligible size counts and unknowns. Climate summaries need explicit station weighting and coverage; woodland summaries need area weighting rather than incident-buffer averages. Thirty-one training years constrain complexity, not the existence of a baseline. Additional regions or monthly units change the estimand and need a recorded rationale.

The 2019–2024 incident test has already been inspected. A later annual experiment can freeze its design using training years, but the overlapping test years are reused evaluation, not a pristine independent holdout. No new experiment, hardware submission or deadline is authorized by this documentation correction.

## Historical receipts

Frozen JSON plans, scientific outcomes, caches and prior QA/handoff receipts remain unchanged. `docs/data/goal_handoff.json`, `goal_audit.json` and `workflow_document_checks.json` describe the earlier snapshot and cannot establish current goal completion. Nine document hashes in the old handoff differ after these intentional corrections; do not rewrite receipts to conceal that change. `scripts/audit_goal.py` audits the saved branch and old manifest, not the missing annual objective. The corrected Markdown status takes precedence over historical completion language.

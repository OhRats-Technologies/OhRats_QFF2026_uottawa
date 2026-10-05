# Feature selection and prediction protocol

The earlier scope assessment below describes the 1 PM run. The owner authorized a new annual study through 5 PM; [current annual implementation and measured progress](ANNUAL_QSVR.md) supersede its unrun status as milestones finish.

## Required objective and current evidence

**Annual macro modelling is required and unrun.** The prior incident-first protocol was an agent-made scope change, not completion of the owner objective. [Correction and provenance](SCOPE_CORRECTION.md). Existing JSON recipes below describe preserved incident experiments; new aggregate recipes are not yet implemented.

Start with a province-year modelling table and a frozen primary annual quantity. Mean reported fire size, total recorded hectares and incident count need separate labels and interpretations. With 31 training years, use small chronological baseline models and bounded kernels. Record negative results; do not defer the core experiment solely because flexible models would have few rows. Define climate station weighting/coverage and area-weighted woodland summaries before fitting. Use audited source incidents, not the weather-matched classifier subset.

Compare selectors with a fixed predictor and predictors with fixed inputs, equal folds, label budgets and tuning. Assess regression/count error in target units against simple annual baselines; incident average precision is not an aggregate metric. Freeze choices on training years. Overlapping 2019–2024 evaluation must disclose prior incident-test exposure. Preserve all old intents and results.

## Resolution and target

| Grain | Use | Decision gate |
|---|---|---|
| Province/year | Required macro annual modelling, not run | Freeze the annual quantity; start simple with 31 training years |
| Province/month | Descriptive coverage; possible extension | Does not replace the annual prediction task |
| Region/month | Optional separately justified modelling unit | Stable geometry, coverage and grouped temporal validation |
| Daily or 30 m cell | Future extension | Requires finer weather and defensible exposure/absence labels |

Ontario remains the initial scope. National/province distributions require downloading the corresponding provinces, not relabelling Ontario as Canada. Regions need an explicit versioned mapping or spatial definition. A bounding rectangle is not an Ontario mask. Count distinct incidents rather than update rows. An unobserved cell/month must remain unknown until reporting coverage justifies a zero label. The completed supporting branch uses conditional agency-reported size >=10 ha for eligible NFDB incidents. It does not predict annual means, counts or hectares, and its variants do not satisfy the required macro experiment. Continuous incident-size regression was not run either.

Monthly summaries are observed during a month and published later. Use lagged summaries for forecasting, and document unresolved publication latency. Prior-year cover still requires disturbance/publication checks. Final size can define an eventual-severity label but cannot enter its predictors.

During an authorized run, review coverage of the owner’s required tasks before each new branch. Reserve time for the annual baseline and report before optional refinements; repeated variants cannot substitute for another required prediction task.

## Preserved incident-branch comparisons

**Feature selection:** fix the predictor, folds, candidate features and feature count. Compare all features, a random subset, mutual information, L1 selection and a relevance/redundancy subset objective. Solve the **same subset objective** classically and with small simulated QAOA. On tiny instances, enumerate subsets to measure the optimality gap. Train-derived relevance/redundancy can be estimated only inside each training fold. Better optimization of this surrogate does not establish better prediction.

**Prediction:** freeze the selected columns. Compare a seasonal baseline, a regularized classical model, a tree model, an RBF kernel and a small quantum fidelity kernel appropriate to the chosen task. Match folds, feature counts, training examples and tuning budgets. Include a classical finite-feature control where feasible. Start quantum screens on a declared small subset because pairwise kernels and circuit evaluations can become expensive.

Only then compare combinations of selector and predictor. Keep the classical-solver/classical-predictor combination as a control for the quantum-selector/quantum-predictor combination. Do not change both stages and attribute a gain to either one independently.

Train 1988–2018, use expanding chronological validation folds within that period, and seal 2019–2024 during discovery. Audited NFDB/weather features span all requested training years; native woodland acquisition is complete through the product's 2022 cutoff. Fit all preprocessing, dimensionality reduction and selection within each fold. Keep every incident/update group together. Incident spatial controls and that branch’s single frozen final evaluation are complete; its adaptive reservations are closed. Annual aggregate training/evaluation was not performed. Retrospective map construction limits forecasting claims even when a prior-year or static map is selected; see [source assumptions](SOURCE_ASSUMPTIONS.md).

Choose the primary metric before screening: count deviance/MAE for counts, or average precision (AP) for rare-event classification. AP is not trapezoidal PR-AUC. Report probability error and reliability separately where probabilities exist; Brier alone does not certify calibration. The [fixed saved-probability report](PROBABILITY_REPORT.md) adds post-final descriptive bins without fitting a calibrator or choosing thresholds. Report paired differences across common seeds/folds, uncertainty, selection stability and elapsed time. Include preprocessing/tuning cost, circuit counts, shots and queue time where applicable. Reserve hardware for a small final implementability check with explicit authorization. A simulator score alone cannot establish quantum computational advantage.

## Discovery workflow

[Dream-RSI](https://arxiv.org/abs/2609.14858) evolves exploration policies using replay of recorded discovery trees. Its replay outcomes are available only for branches actually measured. Our adaptation records proposals and provenance; the [library follow-up](QISKIT_FOLLOWUP.md) also replays four fixed policies over measured encoding panels. Those flat panels were inspected and did not establish policy evolution. The later [independent policy-code study](POLICY_EVOLUTION.md) uses a new rule and fresh prospective trees, independently reviewed before reserved confirmation. It remains a bounded fixed-generator adaptation, not full architecture discovery.

The owner's [earlier RSI workflow](https://github.com/seofernando25/csi5341-vla-jepa/blob/a6427885b3a0bf12c218b455c44b7c468288f938/rsi/README.md) separates a frozen evaluator, bounded screening and later confirmation. We adopt those controls, not its robotics models or data. Preferred proposal/research model: **gpt-6.1-sol**. Record the actual model at execution. No API orchestrator has been launched.

Start with a frozen root protocol in `experiments/screen.json`. Every proposal states its hypothesis, mechanism, parent, cost estimate, controls and rejection criterion. Refine the strongest confirmed branch while reserving roughly one in four proposal slots for a distinct idea. Initial screen: at most eight reservations per frozen study, three common seeds and equal feature budgets. The 1,200-second per-attempt setting is a proposed execution cap; the runner now records measured outcomes and quality checks beside its reservations.

Record failed attempts and elapsed cost, then decide whether to reject, refine or confirm. Reuse a measured outcome only when data, code, folds, seed and evaluator match. Evaluate revised search choices on separate recorded histories when enough history exists. Improvement on replay is not a guarantee on new experiments. Stop a branch on leakage, invalid labels, unmatched controls or repeated failure to improve the quality/cost tradeoff. Never revise an evaluator to promote a candidate. Confirmation uses separate seeds with the same frozen protocol, followed by one final test evaluation.

Spatial sensitivity uses declared 200 km projected checkerboard cells and a 50 km guard, both orientations. Compare against a random time-only training sample with equal training count and identical validation fires; report geography effects separately from reduced training data. This is within-province interpolation, not an external-region certificate. Antecedent-weather baselines will use only station-month measurements through each training-fold end, with minimum-sample and fallback counts recorded. They are estimated training baselines, not official ECCC climate normals.

Encoding refinements are bounded by `experiments/historical_encoding.json`: four qubits, depth two, three scaling/bounding variants and fixed 128/256 row caps. All kernels share encoded inputs and training-only centering/variance normalization; RBF uses a single training-distance heuristic. Record previous adaptive angle choices, simulation costs and hypothetical hardware pair counts. A preprocessing gain must beat matched classical controls before expanding width/depth. The current screen retains classical predictors and prunes further quantum expansion pending confirmation.

The crossed diagnostic (`historical_woodland_combinations.json`) gives feature selection and prediction the same capped training-label budget, reusing matrices for identical selected subsets. Its frozen fresh-seed check is separate from the discovery seed group; reused chronological years are not independent temporal replication. See [quantum methods and cost](QUANTUM_METHODS.md) for the QUBO, exact-state versus synthetic-shot distinction, encoding and hardware-pair accounting. Keep the unconfirmed ZZ lead as a rejected result rather than selecting favorable seeds.

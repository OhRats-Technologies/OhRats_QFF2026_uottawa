# Remaining research for the hackathon

This is the completed coverage checklist for the October6 comprehensive followup. The previous381-fit closeout verified fixed comparisons; it did not exhaust tuning or architecture choices. Status changes require saved evidence and board updates, not a new claim of completion.

| Direction | Required work | Status |
|---|---|---|
| Expanded QSVR tuning | Nested training-only $C$/epsilon/bandwidth, anisotropic angles, depth, topology/order; matched RBF candidate budget and ridge controls | Measured first35,379 + distinct39,267 fits; wider C destabilizes results; further expansion pruned |
| QAOA exploration | Three starts per depth1–4,10/16/20 pools, bounded longer optimizations; original single-start control and honest convergence diagnostics | Measured108 runs/30,011 calls/189 fits; only4 converged; new3-job hardware grid complete |
| Selection objective | Bounded redundancy-weight ablation and objective/prediction alignment; exact, MI and random-feasible controls | Measured432 fits/12,960 calls; no robust predictive benefit |
| Shallower preparation | Basis/warm-start alternatives, small exact parity, support/initialization limits, actual native gate/depth costs | Measured54 searches/216 fits; native20-pool CZ4,860→1,237; noisy feasible fraction remains low |
| Hardware-in-the-loop search | Predeclared training diagnostics, actual parameter-grid counts, shot/charge ledger, separate frozen confirmation | Grid complete:3 jobs/39,936 shots/18 QPU seconds; choices frozen; four confirmation jobs/43,008 shots/20 QPU seconds complete |
| Real predictive confirmation | Measured kernel for predeclared tuned configuration and matched classical controls; retain every repair/acquisition arm | Complete:2 jobs/136,704 shots/44 QPU seconds;24 measured repairs; mixed/unstable errors |
| Sources and controls | Availability/exclusion decisions, independent cached numeric-decoding spot check, time/station controls | Measured65,445 control fits;12-source/2.33M-pixel independent decode spot check passes; source gaps disclosed |
| Findings and judge delivery | Comprehensive report, reproducible saved replay, diagrams/figures, concise presentation updates and scope/limit review | Complete:10 clean-tree replays,209 tests, browser QA, preserved final hashes, report and appendix |

[Findings in progress](RESEARCH_FINDINGS.md) links six full evidence bundles and source-free arithmetic collectors. These local milestones do not close the comprehensive goal. Review found that reversed chain/ring/product orderings are symmetry controls, not distinct geometries; the separate distinct-geometry plan removes those duplicates.

## Protocol before running

**Data boundary:** annual Ontario province-years,1988–2018 only. Use the pinned20-feature table, audited source dates/masks and old three chronological development folds. These folds have already been inspected. New tuning is development evidence, not independent confirmation. Original2019–2024 results and code pins remain unchanged; no new final-year reads.

**Predictive tuning:** weather4, fold-local MI4 from20 candidates and weather/forest8 panels. Every inner chronological split refits preprocessing and supervised selection. Explore $C\in\{0.1,1,10\}$ and $\epsilon\in\{0.05,0.2,0.5\}$. Quantum candidates cover global amplitudes $\pi/64,\pi/32,\pi/16,\pi/8$, two predeclared anisotropic patterns, depths1/2, product/linear/ring maps and canonical/reversed order. The intended72 circuit candidates ×9 SVR settings give648 candidates per panel; RBF receives72 log-spaced bandwidth multipliers ×the same nine SVR settings. Ridge receives a declared alpha grid. Report compute costs separately from equal candidate and label budgets. Freeze exact plan/code before execution, including tie breaks, fold sizes, baseline predictions and retry policy.

Use the optimized exact-statevector fidelity evaluator for broad local screening and check every circuit family against actual `FidelityQuantumKernel` compute–uncompute on a small fixed labels-free sample. Save selected fitted states, kernels and all search scores. Full20-input quantum regression is not automatically implied by20 selector bits; evaluate four/eight inputs first and document any resource-based pruning.

**Selector tuning:** retain the original objective and its exact solution. Three frozen starts per depth1–4, bounded160/240/320/400 evaluations, across the nine existing pool/fold cohorts. Record all traces, optimizer termination and global-reference gap. Compare valid sampled subsets under matched draws and fixed labels. SQD on a diagonal objective is the best observed cost; it cannot refine an unsampled subset. The separate weight/objective study must choose settings inside training folds rather than promote a validation oracle.

**Preparation:** replace the deep initializer only after proving what changes. A computational-basis start has exact cardinality and cheap preparation, but differs from a uniform Dicke state; its first cost phase is global and must not be counted as a useful optimized parameter. Check parity, reachable support, gate count and routing. Do not warm-start with the exact optimum and then credit the quantum circuit for discovering it.

**Hardware budget:** the last personal-instance snapshot had404/600 seconds remaining. Inspect live usage and active board reservations before submitting. Tentative fresh reserve: up to280 seconds across selector exploration, kernel-design diagnostics and separate confirmation; replace this with concrete per-job caps and a frozen acquisition ledger after local preflight. Leave unused budget when experiments do not warrant more. Preserve all old failure/intent records and use new namespaces. Avoid the known1,332-PUB packing failure; small shards retain their mapping and calibration. No blind retries, final-driven choices or undocumented backend switching.

## Quality and exit gates

Each direction ends with measured results or an evidence-backed pruning decision. A cap, a failure or unavailable source must be explained rather than hidden; it is not automatically successful coverage. Search outcomes include matched baseline error, per-fold differences, conditioning, sampler/optimizer resources and timing. Noise mitigation is distinct from logical QEC. No quantum speedup or forecast benefit follows from a simulator or a reused development lead.

Before closeout: check all rows, refresh/respond to the board, validate preserved final hashes, replay saved prediction equations from a clean tracked clone, inspect figures and secret scans, update the report/presentation and push the code. Keep modules focused, generally under300 lines; use uv/bun.

## Closeout evidence

[Comprehensive receipt](data/comprehensive_handoff.json) · [10-study clean-tree replay](data/comprehensive_clone_replay.json) · [Offline browser QA](data/comprehensive_browser_check.json) · [Tracked secret check](data/comprehensive_secret_check.json). Nine new jobs complete at82 charged QPU seconds; no new jobs remain queued. Personal usage268/600,332 seconds remain; unused reservations are released. Six original final artifacts and16 execution files match their historical pins. Current dependency manifests differ from that older execution, as already disclosed; this is not a fresh installation reproduction. All missing directions are measured or explicitly pruned in the findings; none is called successful merely because a cap or fixture test passed.

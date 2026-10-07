# Current game

The primary route now runs the [canvas engineering workbench](FIRELINE_CANVAS.md), with executable freeform builds, repair/replay, QAOA/SQD sampling and opt-in music. The following console description and verification commands are historical; its HTML front door is replaced. Saved evidence remains unchanged.

# QSVR: Fireline

Operate a model console: choose signals, compare selectors, inspect similarities, lock the model, reveal four years and explain its errors. The teal painted-metal chassis, copper cables, cartridges, dials and CRT surfaces follow the owner's two concept images. The two supplied essays inform the model-building loop; they are design references, not scientific evidence.

## Play and meaning

| Chapter | Action | What it teaches |
|---|---|---|
| Main menu | Continue or start a run | Progress is saved locally; sound is opt-in |
| Signal rack | Patch four of twenty signals | Candidate-pool width differs from downstream qubit count |
| Selector bay | Equip MI, exact QUBO, QAOA+SQD or uniform | Lower objective cost does not guarantee better predictions |
| Kernel geometry | Inspect saved matrices and linked model recipes | Circuit geometry controls similarity; C and epsilon affect the fitted SVR |
| Season results | Lock before revealing chronological labels | No model changes after seeing outcomes |
| Model insights | Inspect support-season contributions and rival errors | Intercept + dual weight × fidelity explains the prediction |

Beat the training-mean MAE over the four revealed years. RBF on the same features is a second comparison, not a deliberately weakened opponent. Outcomes are actual saved results: some recipes beat the mean in development; others lose. This does not establish independent generalization or quantum advantage.

All twenty signals come from the later annual pipeline: weather, forest/crown/species proxies and lagged reported fire area/count. The target is **Ontario annual mean reported hectares per size-observed fire**, not total provincial area, spread, containment or individual-fire prediction.

## Evidence contract

The committed `web/demo/console/evidence.json` contains 30 fitted states, 120 predictions and their training/cross matrices. `scripts/build_console.py` exports and checks three public evidence bundles: selector multistart, expanded tuning and distinct expanded tuning. The exporter reconstructs every saved QSVR prediction; it never fits a model or executes a circuit.

Three rounds use training 1988–2006, 1988–2010 and 1988–2014, then reveal development 2007–2010, 2011–2014 and 2015–2018. These years were already inspected. Sealed labels are a game interaction, not inaccessible data or a new blind evaluation. Same-year climate is retrospective; forest inputs include reconstructed prior epochs. The original six-year final artifacts and sixteen frozen execution files are unchanged.

- **Patch choices:** all four-signal patches have an actual saved QUBO objective. Only patches with saved regression states can advance to prediction. Unmeasured patches display “no saved prediction.”
- **Controls:** knobs cycle complete saved recipes. C, epsilon, angle scale, depth and topology can change together. This is not an isolated causal slider experiment, a live optimizer or fresh training. An inactive one-recipe dial must not imply a new fit.
- **Kernel inspection:** the separate four/ten-input bandwidth matrices illustrate geometry only. They never alter the locked four-input prediction.
- **RBF:** selector cartridges use their matched same-input control; tuned cartridges use the panel's tuned RBF on the same folds/features. They need not have identical C/epsilon.
- **SQD:** the selection Hamiltonian is diagonal. SQD returns the best sampled basis state, not an unsampled minimum or an advantage over exact enumeration of 4,845 feasible subsets.
- **Model insights:** contributions add in standardized `log1p` target space. Convert the sum once to hectares. Individual bars are **not additive hectares**. The epsilon tube also uses solver space.
- **Post-run distribution:** bars show MAE for this round's already measured recipes. Highlighted bars share the selected error. They are not a population estimate or an independent leaderboard.

Source SHA-256 hashes are embedded in the payload. The decorative pixel forest is drawn in code and is not a measured raster. The complete Ontario outline comes from the Statistics Canada 2021 boundary, displayed at uniform Web-Mercator scale with 4 projected-km simplification; source receipt: `docs/data/ontario_boundary_receipt.json`. Toronto/GTA are not cropped out.

## Viewing and checks

```sh
bun run web/presentation/serve.ts
bun web/demo/console/check.mjs
```

Open `/web/demo/`. No credentials, Python, fitting or QPU jobs are needed to play. The original fictional field strategy is retained at `/web/demo/field.html`. The obsolete model-lab walkthrough and its dedicated implementation have been deleted at the owner’s request.

`console/check.mjs` verifies all 120 coefficient reconstructions, progressive MAE, lock/reveal invariants and corrupt-save handling. `console/browser-check.mjs` checks six screens, three rounds, matrix inspections, keyboard/mobile interactions, reload persistence, opt-in sound and storage/canvas fallback using optional Playwright authoring tools. `web/presentation/portable-check.mjs` verifies the complete viewer from a tracked-file export. The latest receipt and contact sheet are `docs/data/qsvr_console_verification.json` and `docs/figures/qsvr-console.png`.

The scientific unittest suite has 221 passing checks. The repaired annual collector reconstructs 83 predictions and 24 kernel records while disclosing manifest drift; it does not relax training/evaluation environment checks. Human enjoyment and physical-device/assistive-technology compatibility remain unmeasured. Existing PDF/PPTX files keep their earlier snapshot.

Release `a7dc8eb` passed the clean tracked-tree viewer check: nine slides, five evidence views, the bonus field game, all six console screens and three console blocks, with no ignored inputs or project install. All six frozen annual public artifacts and sixteen execution-code files match their saved hashes.

The viewport update removes the body gutter and width cap; desktop uses the full browser height and mobile retains scrolling for controls. The old walkthrough is deleted, and current portability checks now cover the presentation and two game routes. Earlier five-view receipts are historical.

The game title is FIRELINE. The redundant bottom status strip is removed; development-block selection is inside Chapters. Current browser checks cover the title, absence of the strip and all three selectable blocks.

The locked-model screen returns directly to the latest results or insights, preserving revealed years and avoiding duplicate run history. Results include a progressive observed/QSVR/training-mean chart; only revealed values determine its scale. On-screen metric labels use ha/fire MAE. The owner-requested caveat banners are removed; scientific scope remains documented here. Kernel comparison hides unrelated support-season and tube displays. Ten-input matrices remain separate from the playable saved four-input models.

The follow-up copy pass removes repeated slogans, header branding, feature-group sublabels and the four-signals/four-qubits rail. The selected patch menu now shows a neutral choice for unmatched builds instead of implying Weather. Intercept clicks correctly show the intercept, keyboard focus survives selector/year/dial changes, and scene navigation resets the console scroll. Sticky actions and fitted year tabs are checked from 320px phones through short desktop windows. Numerical prediction checks still cover the same 120 saved values.

## Design research: build, run, diagnose, improve

The owner requests Zachtronics and game-design research. The current console has an engineering aesthetic but insufficient engineering agency: most edits select recorded builds, arbitrary patches cannot predict, reveals mainly advance a presentation, and the QUBO score is disconnected from an understandable play goal. Text trimming fixes readability, not this core loop.

Sources read:

- [Zachtronics: Opus Magnum](https://www.zachtronics.com/opus-magnum/): players construct machines and optimize different dimensions, including speed, simplicity and footprint.
- [Barth/Burns interview, Road to the IGF](https://www.gamedeveloper.com/business/road-to-the-igf-zachtronics-i-opus-magnum-i-): a small expressive toolset, emergent combinations, visible machinery and competing metrics support creative solutions. Optimization is optional rather than a compulsory reward treadmill.
- [Tynan Sylvester: Decision-based Gameplay Design](https://www.gamedeveloper.com/design/decision-based-gameplay-design): examine each actual decision and its tangible consequences; repeated obvious choices and long decision-free stretches weaken play.
- [Zachademics](https://zachtronics.com/zachademics/): iterative problem solving needs introduction and scaffolding; accessibility cannot be assumed from an educational theme.

Recommended prototype, not yet implemented:

1. One short engineering contract on one workbench. Assemble a working signal-to-prediction machine; avoid a mandatory six-page tour.
2. Allow every legal combination in the prototype to run. Use a small dedicated teaching sandbox if necessary; a recorded-state dropdown cannot supply open-ended construction. Keep that sandbox distinct from measured research results.
3. Show consequences while the machine runs: signals pulse through encoding, similarity routes influence the estimate, and predicted versus observed values visibly separate. Animation should explain the player's construction.
4. Give distinct improvement goals: error, construction cost and evaluation effort. Introduce one tradeoff at a time. Budget numbers must be explicit game rules, not invented QPU measurements.
5. Make failure repairable: retain the build, point to an observable symptom, permit one edit and immediate replay, and compare the previous attempt. No reset penalty or arbitrary timer.
6. Make QAOA/SQD an optional candidate-search tool with visible sampled subsets and effort. It must not become an automatic win button; lower subset energy does not ensure lower prediction error.

Success gate before further visual polish: a newcomer can explain the objective, make at least two different useful edits, observe why their outcomes differ, recover from a failed build and improve on a competing metric. Automated checks can verify these mechanics and rule out an obvious universally dominant build; human playtesting is needed to assess fun. The first prototype should demonstrate this loop before adding a campaign, upgrade tree or more screens. No new gameplay, fitting or hardware execution is claimed by this research note.

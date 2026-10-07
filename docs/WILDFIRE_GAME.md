# Fireline: Ontario wildfire strategy

Historical design and results for the removed twelve-front strategy prototype. Its route, implementation and dedicated checks are deleted. The current game is [canvas Fireline](FIRELINE_CANVAS.md); the measurements below describe the earlier snapshot.

**Historical positions and dated forest imagery provide context. Weather, pressure, fuel, exposure and suppression are fictional game quantities. Neither game score nor instrument fidelity measures forecast skill or quantum advantage.**

## Play and progression

Select a fire on the map or incident list. Its readout shows pressure after the next front and its contribution to reserve loss. Hover or keyboard-focus a response to compare immediate consequences; the one-front preview does not capture all later value of a crew.

| Decision | Cost and consequence |
|---|---|
| Dispatch crew | 2 supplies; subtracts 0.90 pressure per active front for two fronts. New dispatches during smoke take three. Two crews start the season. |
| Water drop | 4 supplies; removes 58% of pressure immediately, once per fire/front. |
| Advance front | Resolves damage, returns crews, adds 2 supplies up to 26, and reveals scheduled ignitions. Supplies start at 18. |
| Upgrade after fronts 4 / 8 | Choose one of three seeded offers: another crew, suppression 1.15, resupply 3, or water removal 70%. Each upgrade is available once. |

Survive twelve fronts with reserve above 40. The bottom milestone slots—or **Field guide → Your season build** on phones—review installed response/logistics effects without buying extra choices. The debrief plots the actual timeline, marks the loss threshold and shows the highest-impact front and three largest fire contributions. Percentages refer to cumulative simulated pressure impact before the reserve floor, not losses prevented by responses. It offers the same seed or a new season. Escape closes the report for map inspection; **Season report** reopens it.

Checkmarks identify contained fires; corner numbers count fronts until a crew returns. A diamond marks a crew still assigned at season end. Halos illustrate pressure, not burn footprints. **N** advances, **1/2** dispatch crew/water, and Enter/Space activates the focused control. Dialogs, editable controls and noise sliders ignore game shortcuts; held keys cannot skip fronts. Sound is opt-in, locally synthesized and stops on mute/hidden tabs. Unavailable audio leaves play usable.

When pointer hits overlap, a small **Nearby fires** chooser exposes names, pressure and containment without moving source locations. Opening/cancelling does not alter the save; choosing changes selection only. Keyboard marker activation remains direct. Decorative halos cannot intercept input. The [normal-motion review](data/busy_map_motion_review.json) found 15 covered centres in 32 inspections over eight fixed-policy seasons, although every tested marker had a reachable edge. The [regression check](data/marker_picker_verification.json) reproduces the old wrong-centre selection and verifies the chooser on an active late-season fire at three sizes. This is an interaction audit, not a physical-touch or enjoyment study.

Seeds, accepted moves, selection and instrument loadout save locally. Replay reconstructs resources and delayed effects; incompatible histories are ignored. New seasons reset upgrades and instrument credits. Noise dials and map context are not persisted. Rules/location-pool changes require a new save recipe.

New season spreads its next seed through the existing 32-bit space instead of incrementing it. The first 32 seasons from seed 2 now expose all four first-upgrade offer sets; the old adjacent sequence exposed one. Existing saves, fixed-seed scenarios and Replay seed are unchanged. [Native continuation/restart and variety checks](data/new_season_verification.json). This is observed variety, not a uniformity or human-enjoyment claim.

## Defined mechanics

For pressure $p$, fuel $f$, dryness $d$, wind $w$, rain $r$, and crew suppression $c$ (zero without an assigned crew):

$$g=0.12+0.22d+0.15w+0.18f-0.28r,$$

$$p'=\max(0,\min(9,p(1+g)-c)).$$

Pressure at or below 0.16 is contained and becomes zero. A fire contributes $0.68(p')^{1.2}e$ damage per front, with fictional exposure $e$. Reserve starts at 100 and subtracts cumulative damage, clamped to 0–100; reserve ≤40 loses. Score is rounded $10\times\text{reserve}+18\times\text{contained}+2\times\text{remaining supplies}$. The displayed per-fire loss precedes the combined reserve floor; finished seasons have no future-pressure estimate.

Weather and incident schedules are seeded before decisions. Actions do not consume environmental randomness; upgrade offers use a separate seed. Default seed 2 provides an approachable opening, not a scientific sample selection. These equations define a game, not calibrated fire dynamics or hectares.

## Geography and dated context

The official Ontario boundary includes Toronto/GTA, Ottawa and Windsor, as well as northern Ontario and provincial water. The 2021 woodland view uses nearest source pixels. Its optional legend explains every declared cover code; grey combines unclassified code 0 and nodata 255, **not absent vegetation**. Classes do not measure tree density.

The 66 spatially thinned game locations come from raw 2021 historical fire points inside the province and source forest classes 210/220/230. Recorded hectares do not determine game pressure, fuel, exposure or timing. Thinning makes markers usable; it is not statistical sampling, and coordinate/identity uncertainty remains. These are not real-time alerts or predicted hotspots.

Five additional official WMS windows show mean canopy height (2015), Lorey height (2015), recovery observed through 2017, water (2022) and fuel types (2026). Water is reprojected from its advertised Mercator service to the EPSG:3978 display. Styled colours remain visual context, not numerical predictors. Seven SCANFI height epochs, 1985–2015, use verified nearest 480 m samples and a fixed 0–30+ m display scale; source numbers are not clipped. Native SCANFI uses its own custom LCC, not the display CRS. Changing layers/epochs changes only the view. An optional 2015-minus-1985 height map shows offsetting estimated differences on a fixed ±10 m colour scale; it does not identify growth or fire effects.

Scenario provenance (`scenario.json`, deleted with the field game in `73536ad`) · [Layer manifest](../web/demo/assets/context/layers.json) · [Complete catalogue audit](FIRE_FEATURE_SPACE.md) · [Acquisition, CRS and height study](FOREST_CONTEXT.md).

## Quantum instruments: accepted peer steers

One research credit starts the season; fronts 4 and 8 each award another. Credits are separate from response supplies. Equipping a technique changes its local demonstration and comparison; it never changes fire response or the frozen annual models.

| Technique | Working mechanism | Limit |
|---|---|---|
| Echo / XpXm | Cancels static idle Z drift under ideal pulses | Does not undo damping; no device guarantee |
| Pauli twirling | Averages ± coherent Z rotations into transverse contraction | Removes directional bias, not average infidelity |
| Four-of-ten filter | Discards wrong-cardinality toy bitstrings | Paired flips can pass; fewer samples remain |
| Readout calibration | Inverts a known symmetric 8% assignment map | Entry perturbations and sampling error remain |
| PSD repair | Clips negative kernel eigenvalues | Classical repair, no ideal-data recovery guarantee |
| Rank-two repair | Retains two positive modes | Can discard signal and worsen matrix error |

The lens maps the selected fire to an **illustrative one-qubit angle**, not an entangled ZZ feature state. Damping scales transverse coordinates by $\sqrt{1-\gamma}$ and maps $z\mapsto(1-\gamma)z+\gamma$; dephasing scales transverse coordinates by $1-\lambda$. Static coherent drift is distinct from stochastic dephasing.

The instrument dialog compares the same pure input with/without equipped controls under declared idle/gate drift of 0.7/0.3 radians. Its x/y diagram omits z visually; fidelity $F=(1+\mathbf r_{\mathrm{in}}\cdot\mathbf r_{\mathrm{out}})/2$ uses all three components. The WebGL fallback instead shows an explicitly labelled x/z projection. Equipment announces fidelity, kept samples or matrix error, according to its mechanism.

The kernel instrument uses four training years from a saved four-qubit matrix, then adds synthetic readout/entry errors locally. Minimum eigenvalue and Frobenius distance describe the matrix, **not prediction error**. These mechanisms do not create a logical qubit, syndrome extraction or fault-tolerant QEC.

The feature bench starts with the predefined physical subset and uniformly samples new four-of-ten subsets using saved relevance/redundancy coefficients. It displays up to eight lowest-cost sampled states. The projected Hamiltonian is diagonal: SQD and classical sampled minima are equal. Enumeration of all 210 subsets is a separate exact reference. Inspect exposes bitstrings, labels, costs and redundancy coefficients; those coefficients are not a fidelity kernel. Browser arithmetic does not execute the SQD addon or reproduce the original QAOA draw stream. Lower proxy cost does not prove better prediction.

[Peer technical study](QSVR_QEC_ERROR_STUDY.md) · [IBM suppression course](https://quantum.cloud.ibm.com/learning/en/courses/tools-for-quantum-advantage/error-suppression) · [SQD qubit projection API](https://qiskit.github.io/qiskit-addon-sqd/apidocs/qiskit_addon_sqd.qubit.html).

## Pruning and measured findings

The historical paid-scouting prototype achieved mixed-response survival 74.8%, crews 9.4%, random response 0.4%, and zero water-only/idle wins over 500 seeds. Its earlier approximately 80%/12% synthetic-pool figures were provisional. [Historical balance](data/game_balance.json).

A [frozen matched audit](../experiments/game_scouting.json) used 500 new seeds: paid scouting survived 76.2%, no scouting 94.4%, decision-only scouting 84.0%, and unattainable free perfect fuel 87.6%. Paid/decision-only scouting lost 14.76/9.18 mean reserve versus no scouting. Even free information caused more early intervention under the fixed threshold policy; this diagnoses those policies, not optimal information value. We removed the weak paid action and convenience upgrade and exposed toy fuel directly. [Scouting evidence](data/game_scouting.json). Its runner refuses changed rule hashes; reproduce from pre-pruning commit `ae4cae4`.

The simplified v2 check gives mixed response **90.2%**, crews **10.6%**, random response **5.2%**, and zero water-only/idle wins on 500 fixed seeds. No difficulty parameter was tuned for those percentages. [V2 balance](data/game_balance_v2.json). This shows policy differentiation, not human enjoyment.

A [fixed upgrade review](../experiments/game_upgrade_tradeoffs.json) branches actual offered choices from identical front-4/front-8 checkpoints under crew-first and water-first heuristics: 32 new seeds, 128 checkpoints and 384 game branches in 0.026 seconds. At front 8, after the default supply upgrade, an extra crew versus stronger drops changes mean final reserve by **+3.41** for crew-first play and **−1.51** for water-first play. Crew capacity wins all 32 crew-first pairs; stronger drops win 31/32 water-first pairs. Those choices have policy-dependent consequences, not a universal ranking. All 32 consecutive seeds share offer sets, which limits this pilot's coverage and motivates a separate new-season variety review. [Paired results and saved-arithmetic checks](data/upgrade_tradeoff_review.json). These are toy counterfactuals, not optimal human policies or real suppression effects; rules and models are unchanged.

Run `bun web/demo/strategy/upgrade-audit.js .cache/judge-submission/upgrade-tradeoffs-replica` from the repository root using a new output directory. The runner verifies the committed plan and source hashes; it needs no project packages, credentials or scientific source cache.

The separate annual research remains frozen: 31 training years, six reused later years, same-year retrospective climate, and **no main model beats the training mean**. A training-only coarse-height pilot did not consistently help and was pruned from the predictive headline. Neither source integration nor improved kernel conditioning establishes an architectural breakthrough. [Context findings](FOREST_CONTEXT.md) · [Annual evidence](ANNUAL_FINAL.md).

## Verification and limits

The [whole-goal review](data/strategy_requirement_audit.json) covers catalogue, context, game, presentation and preserved science; the [completed handoff](data/strategy_goal_handoff.json) reviews all six owner deliverables and their limits. The [current interaction review](data/current_interaction_verification.json) records fourteen authoring runs, 67 enumerated cases and thirteen inspected screenshots against the current build. Earlier receipts retain their historical source pins.

Receipts below pin their own snapshots and scope. Historical checks do not certify every later change. Viewing/build instructions are in the [demo README](../web/demo/README.md).

| Evidence | What was checked |
|---|---|
| [Upgrade comparison](data/upgrade_choice_verification.json) | All three full tradeoffs visible without scrolling at fronts 4 and 8, three sizes; native choice hits and exact move replay. Compact layout removes the clipped third option. |
| [Short screens](data/short_viewport_verification.json) | Map-first welcome/continue/new-season entry; native touch and wheel scrolling to commands and back at 844×390 and 1024×600, exact move/save checks without locator auto-scroll |
| [Touch input](data/touch_input_verification.json) | Actual touch-emulated taps/drags, two ten-front move histories, late overlap choice and rotation. Pinned old 320 px layout places the slider behind Advance under minimum scrolling; opening controls now reveals a wider rail. Inspection preserves saves and proxy costs stay on one line. |
| [Tracked-tree viewing](data/current_view_portability.json) | Clean archive, slides/evidence/context and controls without project installation or ignored inputs; preserved PDF/PPTX bytes |
| [Previews](data/decision_preview_verification.json), [outcomes](data/front_outcome_verification.json), [risk](data/fire_risk_verification.json) | Actual clicks versus rule-clone forecasts, 41 resolved fronts, per-fire damage and saved history; clipping fixture separately identified |
| [Terminal report](data/terminal_report_verification.json), [focus](data/incident_focus_verification.json) | Win/loss, map inspection, report reopening, replay/reload and stable incident controls |
| [Ledger](data/upgrade_ledger_verification.json), [weather prompts](data/weather_prompt_verification.json) | All four response effects, both milestones, 12 seasons/three sizes; completed prompts stay corrected after continuation |
| [Season feedback](data/season_feedback_verification.json), [keyboard](data/game_keyboard_verification.json), [map status](data/map_status_verification.json), [legend](data/cover_legend_verification.json) | Actual shortcuts/guards, crew countdown and containment shapes, all palette labels/colours, context switching and unchanged state |
| [Qiskit comparison](data/instrument_diagnostic.json), [equipment](data/instrument_effect_verification.json) | 256 saved channel paths agree within 6.7×10⁻¹⁶; visible mechanism effects/focus at three sizes, no new circuits |
| [Bench inspection](data/bench_inspection_verification.json), [matrix layout](data/matrix_preview_verification.json) | All 210 proxy costs, cardinality, equal sampled minima and readable preview/inspector controls |
| [Fallbacks](data/render_fallback_verification.json), [audio](data/forest_audio_verification.json) | Forced GPU/font/storage/audio failures, reduced motion and hidden-tab branches; seven finite cue waveforms and immediate mute |
| [Prediction comparison](data/prediction_clarity_verification.json) | Six frozen years visible together in ha/fire at three sizes |

Touch checks use Chromium emulation, not a physical device; native select uses the authoring API and offscreen locators auto-scroll. The baseline does not rule out manually scrolling further.

No hardware is called by the demo. Human enjoyment, listening quality, actual five-minute rehearsal duration, native PowerPoint rendering and broad cross-platform behavior remain unmeasured. Forced authoring failures are not physical GPU/OS or assistive-device certification. Public visibility and submission remain separate team decisions.

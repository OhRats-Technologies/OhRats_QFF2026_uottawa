# Fireline / Inside QSVR

**Fireline** is a turn-based Ontario wildfire strategy game. Protect reserve through twelve weather fronts using two crews, limited supplies and two response upgrades. The season report shows the largest recorded impacts so you can replay the same weather with a different response. Pressure, weather and interventions are fictional; the map context and historical position seeds have documented sources.

## Open

```sh
bun run web/presentation/serve.ts
```

[Play Fireline](http://127.0.0.1:8790/web/demo/) · [Explore QSVR evidence](http://127.0.0.1:8790/web/demo/lab.html) · [Five-minute presentation](http://127.0.0.1:8790/web/presentation/)

Viewing uses Bun and committed assets. No Python environment, downloads, credentials or hardware are needed. Optional `--port=8791` leaves another viewer undisturbed.

## Play

| Choice | Consequence |
|---|---|
| Select a fire | See current/next-front pressure and its projected reserve loss |
| Dispatch crew · 2 supplies | Suppress pressure over two fronts; smoke delays new dispatches to three |
| Water drop · 4 supplies | Reduce pressure immediately, once per fire/front |
| Advance front | Resolve damage, return crews, resupply and reveal incoming fires |
| Upgrade after fronts 4 / 8 | Choose crew capacity, suppression, resupply or stronger water drops |

Survive with reserve above **40**. Hover or keyboard-focus a response/advance to preview its immediate consequence. Fuel/exposure are in the readout description; reserve-loss contributions precede the combined reserve floor. Fire controls retain focus while pressure rankings change. Escape closes a finished-season report for map inspection; **Season report** reopens it for replay/new season.

The bottom **4 / 8** slots open your response/logistics build: earned choices and current crew, supply and water effects. On phones, open **Field guide → Your season build**. This view reviews upgrades; it cannot buy extra choices.

Map checkmarks mean contained; corner numbers show fronts until a crew returns. Hover or keyboard-focus a marker for its status. At season end, an assigned crew shows a diamond instead of promising another front. Halos illustrate pressure, not mapped fire extent. The optional legend labels every source cover class; grey combines unclassified and missing values, not absent vegetation. [Palette/control checks](../../docs/data/cover_legend_verification.json) preserve the map pixels and game state.

Overlapping pointer hits open **Nearby fires** so you can select by name. Escape or a click outside closes it; keyboard activation still selects its focused marker directly. Decorative halos do not intercept clicks. [Overlap regression checks](../../docs/data/marker_picker_verification.json) preserve positions and accepted moves.

**Keyboard:** Tab navigates; Enter/Space activates the focused control. **N advances** from game controls; 1/2 dispatch crew/water. Key repeats, dialogs, editable controls and noise sliders do not trigger those shortcuts. [Actual-key/replay checks](../../docs/data/game_keyboard_verification.json) cover three viewport sizes. Sound is opt-in. Custom noise sliders support arrows, Page Up/Down, Home/End. Seeds and accepted moves save locally and reconstruct through the rules on resume; nothing is uploaded. New seasons reset responses and instrument loadout.

Dialogs expose names, and map/list fire buttons describe pressure and crew status. The selected-fire readout exposes fictional fuel/exposure and units beyond its hover tooltip. [Accessibility-tree and native-key check](../../docs/data/accessibility_context_verification.json) covers three sizes and continuation; physical screen-reader speech remains untested.

Water/front cues add locally synthesized textures. Mute stops scheduled notes; hidden tabs suppress cues without replaying them on return. Unavailable audio leaves the game playable.

## Read the instruments

- **Quantum lens:** the selected fire sets an illustrative one-qubit angle. Damping/dephasing contract its vector; optional ideal echo and Pauli-twirled drift show bounded local mechanisms. It is not an entangled ZZ state or a firefighting predictor. An SVG x/z projection preserves the same calculation when WebGL is unavailable.
- **Feature bench:** uniform draws sample four-of-ten subsets using saved relevance/redundancy coefficients. The diagonal projected Hamiltonian has the same SQD and classical sampled minimum. Inspect shows bit strings, feature names, costs and the separate exact minimum over all 210 subsets. Browser arithmetic does not execute the SQD addon or reproduce the original QAOA draw stream.
- **Instrument upgrades:** one credit starts the season; fronts 4/8 award another. The bench compares the same input with/without channel controls, alongside separate sample/kernel effects. Cardinality filtering, known-rate readout inversion and PSD/rank repair change only those toy displays. They confer no fire-response or measured predictive benefit. Matrix numbers use ink selected for their cell backgrounds; zero-credit descriptions remain readable while controls stay disabled. [Paired display check](../../docs/data/matrix_ink_verification.json) preserves all prior values, backgrounds and saves.

## Explore the preserved evidence

| View | What it shows |
|---|---|
| Data | Audited annual total/count/mean. The fixed 2021 context has 1,200 raw markers versus 1,194 accepted annual records |
| Features / SQD | A teaching basis from distinct saved selector outputs; separate from final QSVR's four predefined climate inputs |
| Encoding | Illustrative equatorial phase rotations, not real-year preprocessing or full entangled states |
| Similarity | Ten saved training matrices across widths/scales; controls select measured values without simulation |
| Prediction | Six frozen, reused-year estimates and recorded means, visible together on one scale in ha/fire |

Same-year climate is retrospective estimation. No main model beats the training mean; neither better conditioning nor the game establishes quantum advantage. See [the report](../../docs/REPORT.md) and [frozen evidence](../../docs/ANNUAL_FINAL.md).

## Context and verification

The full Ontario raster, five additional dated WMS layers and [seven height epochs](assets/context/height-series-v2.json) and an optional ’85–’15 estimated-height difference view are local assets. Colours are visual context, not game predictors; cover classes are not tree density, and fire dots are not predicted hotspots. [Game/source report](../../docs/WILDFIRE_GAME.md) · [Catalogue audit](../../docs/FIRE_FEATURE_SPACE.md) · [Acquisition and context pilot](../../docs/FOREST_CONTEXT.md).

| Scoped checks | Saved evidence |
|---|---|
| Current interaction review | [Fourteen authoring runs / 67 enumerated cases](../../docs/data/current_interaction_verification.json), with current source pins and thirteen inspected screenshots |
| Viewing and fallback | [Current clean tracked tree](../../docs/data/current_view_portability.json), [blocked WebGL/fonts/storage](../../docs/data/render_fallback_verification.json), [opt-in audio/mute](../../docs/data/forest_audio_verification.json) |
| Upgrade choices | [Full comparisons at both milestones](../../docs/data/upgrade_choice_verification.json), three sizes and native selections |
| Short screens | [Map-first entry and native scrolling](../../docs/data/short_viewport_verification.json), including Continue and New Season; [five compact desktop sizes](../../docs/data/short_laptop_verification.json) keep the default instruments/command bar on screen at 600px height |
| Touch input | [Phone taps, slider drags and rotated view](../../docs/data/touch_input_verification.json); Chromium emulation, not physical-device certification |
| Decisions and navigation | [Previews](../../docs/data/decision_preview_verification.json), [outcomes](../../docs/data/front_outcome_verification.json), [terminal report](../../docs/data/terminal_report_verification.json), [focus](../../docs/data/incident_focus_verification.json), [per-fire risk](../../docs/data/fire_risk_verification.json), [upgrade ledger](../../docs/data/upgrade_ledger_verification.json), [map status](../../docs/data/map_status_verification.json) |
| Instrument interpretation | [Qiskit channel comparison](../../docs/data/instrument_diagnostic.json), [visible upgrade effects](../../docs/data/instrument_effect_verification.json), [sampled objective inspection](../../docs/data/bench_inspection_verification.json), [matrix layout](../../docs/data/matrix_preview_verification.json) |
| Evidence comparison | [All six years at three sizes](../../docs/data/prediction_clarity_verification.json) |

Receipts pin their own source snapshots; historical checks are not a claim that every later revision was retested. Human enjoyment and actual five-minute rehearsal timing remain unmeasured. Forced rendering failures are not physical GPU/OS tests.

## Build / authoring

```sh
bun install --cwd web/demo --frozen-lockfile
bun run --cwd web/demo build
bun run --cwd web/demo test
```

The prebuilt Three.js bundle and license are committed. Browser `*-check.mjs` tools use the optional Codex-bundled Playwright authoring runtime; public viewing does not. `data.py --check` verifies the tracked teaching snapshot without fits/states. Map animation stops in hidden tabs; reduced motion retains static final values and omits action rings. Historical balance/scouting studies and their fixed-recipe reproduction are documented in the game report.

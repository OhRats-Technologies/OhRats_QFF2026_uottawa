# Fireline presentation

[Open the presentation](https://fireline.ohrats.party/presentation/) · [Play Fireline](https://fireline.ohrats.party/)

Seven main slides form the five-minute talk; two appendices support questions. Charts and controls share Fireline’s canvas artwork.

## Run locally

From the repository root:

```sh
bun run web/presentation/serve.ts
```

Open `http://127.0.0.1:8790/web/presentation/`. The same server serves the game at `/web/demo/`.

## Presenting

Use the arrow keys or Space to advance. **Home** returns to the opening; **End** goes to the conclusion. **N** opens notes and source links, **O** opens chapters, **B** opens Betty’s control briefing, **F** toggles fullscreen, and **Escape** closes overlays. On narrow screens, swipe or scroll through stacked panels. Hidden semantic buttons support keyboard and screen-reader access.

Two short demonstrations belong in the talk:

- Dataset slide: switch between pixels, recorded fire locations and the annual label arithmetic.
- Geometry slide: switch from π/4 to π/32 to show the saved change in fidelity geometry.

The [spoken outline](talk.md) follows the five-minute pacing. Detailed methods and source links remain in `slides.js`; they do not crowd the visible deck.

## Evidence and scope

`evidence.json` supplies audited source arithmetic, development errors, final predictions and actual kernel matrices. `assets/shot-sweep.json` supplies the twelve hardware-yield measurements and their Wilson intervals. The browser only reads these assets. It does not fit models, request hardware or change experimental results.

The hardware appendix labels costs by study. `assets/hardware-costs.json` binds its shot-sweep and repetition-study totals to the [hardware ledger](../../docs/data/hardware_accounting.json). Charged QPU seconds are distinct from elapsed queue/service time; [the accounting](../../docs/SELECTOR_HARDWARE.md#hardware-cost-accounting) identifies both records near 400 elapsed seconds.

Yield charts use labelled zero-based device-specific axes: Marrakesh 0–20%, Quebec 0–2.5%. Exact raw and DD/twirling percentages appear below each shot count. All Wilson intervals remain visible; compare printed values when comparing devices.

The target is **annual mean reported hectares per fire**, using same-year climate. Prediction-error scores are separately labelled **ha/fire, lower is better**. The six 2019–2024 years are reused evaluation. Forest pixels provide map context; the original final predictors use climate. Hardware yield is the share of usable four-feature subsets, not prediction accuracy.

The complete Ontario raster includes southern Ontario. Existing source/projection audits are preserved. Point glyphs show recorded locations, not fire perimeters or predicted hotspots. SQD samples and the circuit are labelled schematics; the phase sphere illustrates one qubit, not the full entangled state.

## Rendering modules

| File | Responsibility |
| --- | --- |
| `app.js` | Canvas lifecycle, input, navigation and entrance motion |
| `canvas/ui.js` | Shared Fireline paint, layout, text, maps and matrix textures |
| `canvas/chapters.js` | Question, dataset and feature selection |
| `canvas/comparisons.js` | Matched development and annual results |
| `canvas/diagnostics.js` | Encoding geometry and both appendices |
| `canvas/ending.js` | Findings and game handoff |
| `canvas/panels.js` | Canvas notes, chapter index and Betty briefing |

Reduced motion renders final values immediately. Other transitions fade the panels, grow comparison bars and crossfade between saved matrices. Displayed numbers always come from saved evidence.

## Browser verification

`check.mjs` uses Playwright from `RUNTIME_NODE_MODULES`. With the server running:

```sh
node web/presentation/check.mjs
```

The check covers all nine slides at five viewport sizes, footer hitboxes, keyboard/hash navigation, map tabs, all five angle settings, notes scrolling, actual chart values, animation completion and absence of browser errors. Screenshots and the receipt go under ignored `.cache/presentation-canvas/verified/`. Evidence and published PDF/PPTX hashes must remain unchanged.

`PRESENTATION_BASE` and `PRESENTATION_OUTPUT` can override the server and output directory. `portable-check.mjs` verifies a committed tracked-file export, including the game; run it after committing the intended snapshot.

## Offline snapshots

The existing [PDF](slides/ontario-wildfire.pdf) and [PowerPoint](slides/ontario-wildfire.pptx) retain their earlier design and scientific snapshot. This canvas redesign changes the live browser presentation. `export-slides.mjs` remains a separate native PowerPoint authoring tool; it does not export the new canvas artwork.

# Fireline canvas game

Completed implementation goal: replace the primary walkthrough with a full-window engineering workbench. Build → run → inspect → repair. Every legal 2–10-input build must execute, including combinations absent from the saved research recipes.

## Sandbox boundary

The browser uses public 1988–2018 development rows, fold-local median imputation/scaling, bounded angles, exact one-layer linear ZZ states, fidelity matrices and a classical epsilon-SVR dual solver. It never accesses credentials, hardware or the 2019–2024 research evaluation. Its adaptive play is a teaching sandbox, not additional predictive confirmation. Published scientific evidence stays unchanged.

The native JS gates are checked against Qiskit amplitudes and Gram matrices. The browser solver is checked against sklearn precomputed SVR on the same development fold. `bun test web/demo/canvas/engine.test.js` runs those checks; `uv run --no-sync python web/demo/canvas/validate.py` regenerates independent goldens. `scripts/build_canvas_data.py` exports public inputs and recorded selector objectives.

## Completion gates

- One canvas draws all visible menus, controls, instruments and help; no page gutters.
- Freeform builds, real width/angle/C/epsilon controls and run/repair/replay consequences.
- Clear, attainable accuracy and resource challenges; retain previous attempts.
- Full Ontario geography, tactile routing, meaningful animated matrices and encoding.
- Sampled-candidate selection with correct diagonal-SQD behavior.
- Cohesive original assets, opt-in composed music and action feedback.
- Pointer, touch, keyboard and accessible control mirror; resize and short/mobile layouts.
- Persistence, audio visibility lifecycle, numerical checks and clean tracked-file viewing.
- Final screen-by-screen audit removes redundant text and inert decoration masquerading as controls.

Implementation and review receipts will be added before closing the goal. No human playtest or fun assessment is implied by automated QA.

## Implemented workbench

All visible controls are painted on canvas. A hidden semantic control mirror provides focus/activation and announces actions; it is not an HTML visual skin. Twenty signals can form legal 2/4/6/10-input builds. Clicking a new signal at capacity replaces the oldest connection; dragging into the engine routes it. Width, angle, C and epsilon really change the calculation. Live preview matrices update on edits; results remain the last executed build.

Each season compares to the player's first engine: reduce MAE by 5%, or reduce qubit-pair effort by 25% within 5% extra error. This is a game contract, not a quantum-advantage criterion. The effort counter is input width times evaluated fidelity-pair count; it is not wall time or IBM usage. Runs preserve previous builds and a ghost prediction line. There are three inspected chronological development seasons and no punishing timer or puzzle gate.

The foundry uses a fixed ideal one-layer QAOA on the four-excitation sector of twenty candidate bits: uniform feasible initial amplitudes, diagonal phase separator and sequential XY ring mixer. It is not an optimized or hardware QAOA experiment. Uniform sampling is matched by shot count. Diagonal SQD retains the minimum-energy sampled basis state; MI/exact cartridges use recorded training selectors. None of these scores is predictive accuracy.

Visual assets and the composed opt-in music theme are documented in [ASSETS.md](../web/demo/canvas/ASSETS.md). The sphere uses the first qubit's reduced Bloch vector for the latest training-input state; its length can shrink under entanglement. The map is a complete Ontario context raster with 2021 reported fires, not predictions for a played development year.

## Final authoring review

| Requirement | Evidence |
| --- | --- |
| Fully canvas visible UI | One canvas paints menus, controls, panels, instruments and notes. HTML contains only the canvas and hidden accessibility semantics. |
| Executable construction | Arbitrary 2/4/6/10-input builds execute; current matrices change on edits. Width/angle/C/epsilon are independent controls. |
| Meaningful challenge | Accuracy/effort contracts, three chronological development seasons plus a fourth reused-year teaching season (see below), previous-build restore and ghost comparison. Mechanic tests find at least two useful repairs in each season. No compulsory puzzle, reflex runner or timer. |
| Correct quantum teaching | Qiskit amplitude/Gram goldens; sklearn SVR controls across all widths; independent Qiskit XY-mixer comparison. Diagonal SQD chooses an observed candidate. |
| Visual identity and assets | Original forest environment, code-native metal/CRT/cable details, actual full Ontario raster, computed matrices and reduced Bloch vector. |
| Music | Original opt-in Ember Relay theme; patch/run/win cues, mute and hidden-page suspension. Offline render is audible and unclipped. |
| Input and resilience | Pointer routing, touch patching, keyboard controls/focus, restore, reload, malformed and blocked storage checks. |
| Layout/copy review | 1920×1080,1440×900,1280×640,390×844,320×568,844×390. Final visual inspection repaired landscape overlap, short-window bank spacing, stale geometry, missing comparison legends and notes spacing. |
| Maintainability | Single-concern JS modules below 300 lines; no frontend install or build needed to play. Replaced HTML/CSS console code is removed; recorded evidence stays. |

Eight tests / 849 assertions pass. The extended checks exposed an intercept-bound error when every SVR coefficient was at a boundary; the browser solver was repaired and matches the independent controls within 0.1 ha/fire. The old game save key is superseded so those provisional calculations are not retained.

[Verification receipt](data/fireline_canvas_verification.json) · [Workbench](figures/fireline-canvas-workbench.png) · [Foundry](figures/fireline-canvas-foundry.png) · [Mobile](figures/fireline-canvas-mobile.png)

Automated checks verify working decisions, consequences and attainable repair goals. They do not establish that newcomers find the game fun; that requires a human playtest. Sound lifecycle QA dispatches visibility transitions deterministically, and an eight-second offline theme render checks signal level; it is not a listening panel.

The clean tracked export at `0c65d07` passes with no ignored inputs or project install: all nine presentation views, dated context layers, preserved downloads, field-mode round trip, canvas gameplay and interaction checks. External requests are blocked during verification. Browser sandbox calculations run; the frozen scientific pipeline and IBM hardware do not. The later closeout changes only documentation and coordination records.

## Obsolete field-mode removal

The owner requested deletion of the separate `field.html` strategy game. Its engine, bundle, Three.js dependency, menu link and dedicated checks are removed. Shared forest context and published historical receipts remain. The field-mode round trip in the earlier `0c65d07` verification describes that snapshot; current portable checks require the deleted route and bundle to return 404.

Clean tracked export at `57a1f80` passes: nine presentation views, six canvas viewport checks, drag/touch/keyboard, ten-input execution, restore, storage and audio lifecycle. Both old route and bundle return 404; no browser errors or failed local loads occur. Eight numerical/game tests retain 849 passing assertions. [Cleanup verification](data/field_removal_verification.json).

## Beatrice onboarding

First play and New Run open eight short canvas lessons before the workbench: mission, signals, angle encoding, C, epsilon, QAOA, SQD and the repair contract. Next/Back and Skip control pacing. Beatrice's guide, reached through **?** or the menu, has direct topic tabs. Existing saves and completed seasons survive; continuing an existing run bypasses the briefing.

Practice controls change only lesson diagrams. The angle example uses two single-qubit RY rotations and their exact overlap; it explains encoding without pretending a single Bloch sphere describes an entangled ZZ state. C/epsilon plots and QAOA bars are illustrative. Epsilon uses the engine's standardized log-target space. SQD is first introduced as classical diagonalization of a sampled Hamiltonian subspace, then specialized to this game's diagonal cost matrix.

Teaching definitions checked against IBM's [QAOA tutorial](https://qiskit.qotlabs.org/docs/tutorials/quantum-approximate-optimization-algorithm) and [SQD overview](https://qiskit.qotlabs.org/learning/courses/quantum-diagonalization-algorithms/sqd-overview). Beatrice is a fictional guide, not an NRCan representative. All visible art and UI remain canvas-rendered.

`canvas/onboarding-check.mjs` walks all eight lessons on five desktop/phone/landscape viewports, checks isolated practice state, automatic entry, new-run/reload/resume, topic navigation, keyboard/touch and Escape. It is included in the clean tracked-view verifier. Gameplay/math, storage and audio regression checks remain separate.

Clean tracked export at `facca21` passes the full viewer/game/briefing checks: eight tests and 849 assertions, eight lessons on five viewports, six gameplay layouts, input/restore/storage/audio, nine slide views and preserved downloads. No local-load or browser errors. [Onboarding receipt](data/fireline_onboarding_verification.json). Final visual review included phone SQD/QAOA diagrams and short landscape text; teaching effectiveness and enjoyment still require human playtesting.

## Betty's in-place tour

Owner feedback replaces the large opening lesson panel with the actual workbench, one amber-highlighted region and a compact Betty speech bubble. Next/Back/Skip are the only active controls. Eight steps point to the map, signal rack, angle, C, epsilon, foundry, sampled SQD shortlist and Run. The topic guide remains optional under **?**; first/new-run onboarding no longer uses that modal.

Mobile tours dock the bubble below a compact workbench; short landscape tours place it beside the workbench. Desktop placement chooses an adjacent area that does not cover the target. QAOA/SQD shows a fixed real browser-sampled foundry example without patching the player's build. The shortened encoder uses horizontal controls when vertical rows would overflow. Onboarding checks assert compact bubbles, non-overlap, locked inputs and preserved build state on all five viewports.

Clean tracked export at `7ca7ec3` passes: eight tour steps on five viewports with exposed targets and locked gameplay, six gameplay layouts, topic-guide replay without build reset, input/restore/storage/audio, nine slide views and preserved downloads. Eight numerical/game tests retain 849 passing assertions. No browser errors or failed local loads. [Tour verification](data/fireline_spotlight_verification.json) · [Desktop](figures/fireline-betty-tour.png) · [Phone](figures/fireline-betty-mobile.png). **? → Show Me** repeats the walkthrough on the current build.

## Betty motion and kernel colour key

Betty idles on whole sprite pixels: breathing, tail sway/thump, blinks, ear twitch, a periodic wave, helmet glint and pencil taps. A forward Next in the tour or topic guide starts a half-second hop; Back does not. When a step's text mentions fire, she raises a lit drip torch. Reduced motion holds the clock at zero, so she stays static. The kernel engine adds a 0 DIFFERENT → SAME 1 ramp using the cell colours, average off-diagonal similarity and a support-year key. Onboarding and gameplay layout checks pass on all five/six viewports with no browser errors.

## Tour glide, rack footer and cartridge notes

Tour Next eases the highlight and bubble to their new place and size over 0.42 s (`glide.js`); text fades in once the bubble settles, and reduced motion snaps. Bubble width follows its text (300–420 px). Rack rows now end above the footer buttons and page when cramped, fixing the wide-screen overlap of the last signal row with Subset Foundry; narrow paged racks shorten it to FOUNDRY. A sweep from 320 px to 2560×1440 finds no foundry overlaps. The foundry keeps a permanent note under its cartridges (`foundry-help.js`) that explains MI, EXACT (all 4,845 four-signal sets), QAOA + SQD or UNIFORM, changing with the loaded cartridge; candidate rows fit below it. Onboarding, layout and interaction checks pass with no browser errors.

## Music track, saved charts and removed links

MUSIC ON now streams the looped Pixel Firefront cover (`assets/music`) through the existing opt-in Web Audio lifecycle: nothing downloads before opt-in, hidden tabs pause it and the toggle mutes it. Ember Relay remains the procedural fallback when the file cannot load. `serve.ts` serves `.wav`. Restored saves no longer carry a stale run-animation clock, which had drawn season bars partial or inverted after Continue. The rack-to-engine and footer cables and the drag-to-link gesture are removed; signals patch by click, keyboard or touch, and the interaction check asserts that a drag does not link.

## Layout reliability

Menu artwork, title and sphere now fit their actual content areas. The decorative sphere sits below the button stack and disappears when a short viewport has no room. Encoder spheres use their panel's interior height. Tour highlights contain the complete control labels; dialogue retains its final text dimensions while moving, stays inside the viewport and avoids the active control and encoder heading. Reduced motion displays dialogue immediately. Saved builds and glide transitions remain intact.

Verification: 11 Bun tests / 889 assertions; eight onboarding steps across five layouts with both animated and reduced motion; six gameplay layouts with no overflow or browser errors. Checks inspect rendered animation bounds, not only destination rectangles. [Layout receipt](data/fireline_layout_verification.json) · [Angle walkthrough](figures/fireline-layout-angle.png).

## Short Betty dialogue

The in-place tour now has sixteen 10–25-word bubbles across eight topics. Text types at 38 characters/second; a click completes the line, and the next click advances. Click Betty's bubble or the drawn continue arrow. Back and Skip remain available; the page counter is removed. The arrow bounces only when the line is ready, and reduced motion displays text immediately. Short synthesized chirps follow the letters when sound is enabled; mute and hidden tabs silence them. No recorded character voices are used.

Verification: 16 tests / 943 assertions; sixteen bubbles on five layouts in animated and reduced-motion modes; browser checks of natural typing, click-to-complete, bubble progression, synthesized audio and mute. [Dialogue receipt](data/fireline_dialogue_verification.json) · [Betty](figures/fireline-betty-dialogue.png).

## Automatic season test

Opening Results tests a complete new or changed build automatically. Reopening an unchanged or restored result does not add a run. The footer now opens Results, and Betty describes that flow. The Build/Run/Repair placeholder is removed. Button arrows use shared canvas strokes with shadow, mint shaft and amber chevron instead of font glyphs.

Verification covers automatic calculation, changed-build evaluation, duplicate prevention, unchanged first-run challenge and reload; six gameplay layouts, five sixteen-bubble tours, input/restore/audio lifecycle and 16 tests / 943 assertions pass. [Automatic test receipt](data/fireline_automatic_test_verification.json).

## Live build testing

Complete input edits now test automatically after a 420 ms pause. Rapid changes coalesce; incomplete builds, open guides/foundries and unchanged saved results do not calculate. Automatic runs leave the editor visible. The initial and next-season starting builds also test automatically. Next replaces the footer action only when the current evaluated build meets the existing error/resource contract; editing hides stale victories immediately. Betty's instructions match this flow.

Verification: 18 tests / 951 assertions; live browser checks of automatic baseline, edit evaluation, staying in the editor, win gating, stale-victory removal and next-season baseline; six gameplay layouts, five sixteen-bubble tours and input/restore/audio lifecycle checks. [Live-test receipt](data/fireline_live_test_verification.json) · [Winning build](figures/fireline-live-win.png).

## Evaluation feedback and navigation

Results is view navigation only; its duplicate footer action is removed. The footer shows the current MAE when idle, an amber evaluating instrument during debounce/calculation, or Next Season/Finish for a current winning build. Progress lights sweep without claiming a percentage; reduced motion uses a static strip. Evaluating state is transient and announced to assistive technology, not saved as unfinished work.

Verification: 19 tests / 960 assertions; pending-state lifecycle and bounded animation checks; six gameplay layouts, five sixteen-bubble tours, live win/edit/next-season checks and visible evaluating-state verification. [Feedback receipt](data/fireline_evaluation_verification.json).

## Run log verdicts and season readability

The run log (`runlog.js`) states whether the last run beats the training mean and RBF on the same season (BEAT/BEHIND with the MAE difference) and shows contract progress: the first run sets a TARGET, later runs show error and effort change against the −5%/−25% thresholds. Desktop toasts sit in the free top-bar gap instead of covering panel titles. The selected season year gets a column wash with observed/model values above its bars. The onboarding check now waits for two painted frames after each click instead of a fixed 40 ms, removing most of a pre-existing race where controls were read from the previous frame.

## Season 4: reused 2019–2024 years

Owner-requested on October 7. After season 3, NEXT opens a fourth season trained on 1988–2018 and tested on the six reused 2019–2024 years from `docs/data/annual_reused_evaluation.csv`. Forest inputs end in 2018, so their eight rack buttons are disabled and builds keep or refill only the ten weather and two fire-memory signals; fire memory is the previous year's reported area and incident count, matching the training columns exactly. `scripts/canvas_final_season.py` rebuilds that season's foundry costs with the `selector_multistart` objective (mutual information, 3 neighbours, seed 137, redundancy weight 0.5) over the 495 available four-signal subsets; the same code reproduces the three saved seasons to within 2e-14. The QAOA mixer skips swaps into absent subsets. The season's training-mean MAE is 276.81 ha/fire, matching the frozen evaluation. This is teaching play on reused years, not research evidence. Seasons 1–3 data are unchanged; onboarding, layout and interaction checks pass.

## Reading the kernel engine

The angle section now continues with four short bubbles highlighting the kernel grid: rows/columns are years, cells compare year pairs, brightness shows encoded-state similarity, and regression learns from those similarities plus known fire sizes. Betty distinguishes similarity from fire risk and explains why indistinguishable or unrelated years leave little structure to learn. The optional Angle guide repeats the connection to the target. Twenty dialogue bubbles remain within 10–25 words each; the walkthrough verifier derives its beats from the lesson data instead of assuming two bubbles per topic.

Verification: all 20 bubbles pass animated and reduced-motion walkthroughs at five desktop/phone/short-landscape sizes, with no browser errors or target/bubble overlap. Dialogue and glide unit checks pass (8 tests, 102 assertions). See [receipt](data/fireline_kernel_teaching_verification.json) and [phone view](figures/fireline-kernel-teaching.png).

## Completed contract lock

A current winning result locks feature count, signals, angle, C, epsilon, foundry and previous-build restoration. The winning build remains inspectable; navigation, help, sound and Next/Finish remain available. The lock is derived from the saved current result, so reload preserves it and advancing a season clears it. Guide practice controls stay independent. `contract-lock-check.mjs` verifies real desktop/phone completion, disabled choices, persistence and next-season unlocking; four lock/automatic-test unit tests pass with 46 assertions. The general browser walkthrough now applies its foundry candidate before winning, rather than attempting edits after completion.

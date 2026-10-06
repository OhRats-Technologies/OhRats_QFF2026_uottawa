# Signal Run / Inside QSVR

**Signal Run** is a 55-second Three.js arcade: deliver twelve mint packets, avoid orange obstacles, and use a charged SQD pulse. Three hits lose the standard run; retry immediately. Practice has wider catches, no damage and extra time. Steer with arrows/A–D or pointer/touch drag; Space or the pulse button activates the shield. Escape pauses. Synthesized sound is opt-in.

The retained **Inside QSVR** walkthrough is at **http://127.0.0.1:8790/web/demo/lab.html**. Its five independent views explain annual data, features/SQD, phases, saved kernels and predictions. It provides a keyboard-accessible explanation without reflex play.

From the repository root:

```sh
bun run web/presentation/serve.ts
```

Open **http://127.0.0.1:8790/web/demo/** for the game. The committed bundle needs no install, CDN or credentials. In `lab.html`, use direct section navigation, arrows, or **N** for explanation. Custom input sliders support dragging, arrow keys, Home/End and Page Up/Down. Mobile and reduced motion preserve the same content.

## What is real / illustrative

The flight path, forest, collision damage and shield are fictional game rules, not Ontario geography, fire behaviour or predictive skill. Game packets cycle through four distinct saved selector outputs: a teaching basis, not the original QAOA draw stream. SQD displays the diagonal costs of collected candidates and selects their minimum; this is browser arithmetic, not a new Qiskit/addon execution. Classical minimum selection gives the same answer. The shield reward does not imply an algorithmic benefit. Final QSVR inputs remain the separate predefined four features.

The phase hoops are illustrative. Similarity-wall colours reuse the saved four-qubit π/4 training matrix; gameplay does not change kernels or models. The result screen compares frozen 2021 recorded/predicted means and states the unsuccessful later-year comparison. The opening map uses the corrected full Ontario boundary; grey means no mapped woodland class.

## Walkthrough controls

- **Data:** accepted annual total/count/mean values from the independent NFDB audit. The context map stays at 2021 when selecting another year; its 1,200 raw markers differ from 1,194 accepted annual records. Land-cover pixels are categorical, not tree density or predicted hotspots.
- **Features/SQD:** final QSVR used the predefined four climate inputs. A separate training-only selector study used actual qiskit-addon-sqd on a diagonal objective. Its first fold sampled 83/89 unique feasible subsets with uniform/QAOA draws. The four-state teaching matrix is constructed from distinct saved selector outputs, not the original draw stream. Its minimum illustrates why SQD adds no benefit beyond the best sampled subset. Browser arithmetic is not an addon execution.
- **Encoding:** illustrative standardized inputs rotate equatorial single-qubit phases. They are not real-year preprocessing or full entangled ZZ states. RZ changes relative phase here, not isolated computational-basis probabilities. Sliders do not change saved kernels or predictions.
- **Similarity:** selects among ten measured, rounded training matrices at four/ten inputs and five scales. This input-only diagnostic did not select a better predictor.
- **Prediction:** six frozen reused-year outcomes and model estimates. Reveal changes visibility only. Same-year climate is retrospective; no main model beats the training mean.

The [report](../../docs/REPORT.md), [SQD implementation](../../wildfire_lab/sqd_selection.py) and [presentation](../presentation/README.md) contain the source methods and receipts. `data.py --check` verifies the teaching snapshot against committed records and the original objective without fitting or states. It can rebuild `data.json` from tracked sources. Maps and measured matrices are reused from the presentation snapshot.

`check.mjs` is authoring QA using the Codex-bundled Playwright runtime. It checks source hashes, all 210 feasible objective values, saved results, custom controls, navigation, three viewport widths, reduced motion and denied private routes. Its browser receipts are ignored under `.cache/judge-submission/demo-browser/`. Public viewing needs only Bun and the committed files.

## Build / check

Browser viewing uses the prebuilt local bundle. To edit the game:

```sh
bun install --cwd web/demo --frozen-lockfile
bun run --cwd web/demo build
bun run --cwd web/demo test
```

Three.js is pinned in `bun.lock`; its license ships beside the bundle. Handwritten game modules have fewer than 300 lines each; the generated/minified dependency bundle is exempt. `game-check.mjs` uses the bundled authoring Playwright runtime for actual control-driven win/loss, collected-cost projection, pause/retry, sound toggle, touch-layout and reduced-motion checks. GPU rendering remains necessary; the walkthrough is the alternative when WebGL/reflex play is unsuitable. Reduced motion removes decorative animation, while flight still moves.

Design research: [Quantum Moves 2 creators](https://arxiv.org/abs/2004.03296) demonstrate interactive quantum-control play; this arcade does not reproduce that research. [Steve Swink’s Game Feel](https://www.gamedeveloper.com/design/game-feel-the-secret-ingredient) informed direct steering and immediate feedback. [Accessible Games challenge patterns](https://accessible.games/accessible-player-experiences/challenge-patterns/) informed practice, pause and rapid retry. The result is an educational arcade, not a citizen-science optimization experiment.

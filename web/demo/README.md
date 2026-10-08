# Fireline

[Play Fireline](https://fireline.ohrats.party/) · [Watch the presentation](https://fireline.ohrats.party/presentation/)

Choose 2–10 inputs, tune the encoding and improve a QSVR model across four seasons. Changes test automatically. Meet the accuracy or computation contract to unlock the next season; the winning choices then lock.

Betty, the pixel-art firefighter beaver, walks you through the actual workbench before first play. One UI region is highlighted at a time; her small speech bubble explains it beside the controls. Gameplay is locked until you finish or skip. The tour covers signals, angle, the kernel grid, C, epsilon, QAOA/SQD and automatic testing. New Run repeats the tour; existing runs resume directly. The **?** guide retains direct topic tabs; **Show Me** replays the visual tour without resetting your build.

Stuck on a season? **BETTY** gives short, specific hints checked against your current contract. She starts with the goal, then suggests one change at a time. After several help requests, **SHOW ME** lets her cursor connect a tested build for you. Rapid patching offers help once per season; Escape dismisses it. Hints use local browser calculations and never change your starting challenge.

## Run locally

From the repository root:

```sh
bun run web/presentation/serve.ts
```

Open `http://127.0.0.1:8790/web/demo/`. The same server serves the presentation at `/web/presentation/`. [Design and verification](../../docs/FIRELINE_CANVAS.md).

The first three seasons use public 1988–2018 development data and a 20-feature library. Season four uses the reused 2019–2024 years with weather and fire-memory inputs. QAOA/SQD explores four-feature subsets. These are local teaching calculations; game scores do not enter scientific results. Playing needs no Python, credentials or QPU access.

All visible UI renders on Canvas2D; semantic controls are hidden for keyboard/screen-reader access. Forest art, metal surfaces, CRT effects and music are documented in [assets](canvas/ASSETS.md). The opt-in track is **Pixel Firefront**; **Ember Relay** is its procedural fallback.

## Checks

```sh
bun test web/demo/canvas/*.test.js
```

Authoring browser QA uses `canvas/browser-check.mjs` and `canvas/interaction-check.mjs` with an external Playwright installation. They are not needed to play. Public input export: `uv run --no-sync python scripts/build_canvas_data.py`.

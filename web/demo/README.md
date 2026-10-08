# Fireline

A full-window canvas engineering game. Patch 2–10 signals, tune the encoding, run a QSVR engine, inspect its errors and repair it. Improve accuracy or use less computation. Previous builds stay available.

Betty, the pixel-art firefighter beaver, walks you through the actual workbench before first play. One UI region is highlighted at a time; her small speech bubble explains it beside the controls. Gameplay is locked until you finish or skip. Next/Back covers signals, angle, C, epsilon, QAOA/SQD and Run. New Run repeats the tour; existing runs resume directly. The **?** guide retains direct topic tabs; **Show Me** replays the visual tour without resetting your build.

Stuck on a season? **BETTY** gives short, specific hints checked against your current contract. She starts with the goal, then suggests one change at a time. After several help requests, **SHOW ME** lets her cursor connect a tested build for you. Rapid patching offers help once per season; Escape dismisses it. Hints use local browser calculations and never change your starting challenge.

```sh
bun run web/presentation/serve.ts
```

[Play](http://127.0.0.1:8790/web/demo/) · [Design and verification](../../docs/FIRELINE_CANVAS.md)

Twenty public Ontario features and three chronological 1988–2018 development seasons, plus a fourth teaching season replaying the reused 2019–2024 years (weather and fire-memory signals only; never research evidence), drive local browser calculations. QAOA/SQD explores sampled four-feature subsets. Published research and IBM evidence are unchanged; playing requires no Python, credentials or hardware access.

All visible UI renders on Canvas2D; semantic controls are hidden for keyboard/screen-reader access. Original forest art, metalwork, wiring, CRT effects and **Ember Relay** music are documented in [assets](canvas/ASSETS.md). Music is opt-in.

```sh
bun test web/demo/canvas/*.test.js
```

Authoring browser QA uses `canvas/browser-check.mjs` and `canvas/interaction-check.mjs` with an external Playwright installation. They are not needed to play. Public input export: `uv run --no-sync python scripts/build_canvas_data.py`.

import { controlMirror } from "./accessibility.js";
import { connectInput } from "./input.js";
import { Paint } from "./paint.js";
import { loadAssets } from "./assets.js";
import { Audio } from "./audio.js";
import {
  fresh,
  load,
  save,
  build,
  toggle,
  setWidth,
  record,
  angles,
  assessment,
} from "./session.js";
import { drawWorkbench } from "./workbench.js";
import { menu, foundry } from "./overlays.js";
import { drawGuide } from "./guide.js";
import { drawTour } from "./tour.js";
import { openBriefing, guideAction } from "./guide-flow.js";
import { run } from "./engine.js";
import { preview } from "./preview.js";
import { automaticTests, currentResult } from "./auto-test.js";
import { sampleCandidates } from "./foundry.js";
import { contractLocked, choiceAction } from "./contract-lock.js";
import { celebration } from "./celebrate.js";
import { SeasonMelt } from "./season-melt.js";
const canvas = document.querySelector("canvas"),
  ctx = canvas.getContext("2d"),
  p = new Paint(ctx),
  audio = new Audio(),
  melt = new SeasonMelt();
const data = await fetch("./canvas/data.json").then((r) => r.json()),
  assets = await loadAssets();
let s = load(),
  W,
  H,
  scale,
  hover = null,
  toastTimer,
  runningToken = 0,
  tourReceipt = null;
const reduce = matchMedia("(prefers-reduced-motion: reduce)").matches;
let geometry = preview(data, build(s), s.round);
const auto = automaticTests(() => s, () => action("auto-test"));
const a11y = document.querySelector("#controls"),
  status = document.querySelector("#status");
const mirror = controlMirror(p, a11y, audio, () => s);
function resize() {
  melt.cancel();
  W = Math.max(390, innerWidth);
  scale = innerWidth / W;
  H = innerHeight / scale;
  canvas.width = Math.round(innerWidth * Math.min(2, devicePixelRatio));
  canvas.height = Math.round(innerHeight * Math.min(2, devicePixelRatio));
  canvas.style.width = "100%";
  canvas.style.height = "100%";
}
function toast(text) {
  s.toast = text;
  clearTimeout(toastTimer);
  toastTimer = setTimeout(() => (s.toast = ""), 2200);
  status.textContent = text;
}
function dirty() {
  save(s);
}
async function action(type, value) {
  if (melt.active && !["sound", "auto-test"].includes(type)) return;
  if (
    s.running &&
    type !== "sound" &&
    type !== "help" &&
    !type.startsWith("guide-")
  )
    return;
  if (guideAction(s, type, value, status)) {
    dirty();
    auto.schedule();
    if (auto.pending) status.textContent = "Evaluating the current build.";
    return;
  }
  if (contractLocked(s) && choiceAction(type)) return;
  if (type === "start") {
    s.menu = false;
    if (!s.onboarded && !s.attempts) {
      openBriefing(s, status);
    }
    location.hash = "workbench";
  }
  if (type === "new") {
    s = fresh();
    s.menu = false;
    openBriefing(s, status);
    location.hash = "workbench";
  }
  if (type === "menu") {
    s.menu = true;
    location.hash = "main-menu";
  }
  if (type === "tab") {
    s.tab = value;
    if (value === "results" && s.features.length === s.width &&
      !currentResult(s)) type = "run";
  }
  if (type === "rack-page") s.rackPage = ((s.rackPage || 0) + 1) % value;
  if (type === "foundry") {
    s.foundry = !s.foundry;
    s.candidate = 0;
  }
  const open = data.rounds[s.round]?.available;
  if (type === "feature" && open && !open.includes(value)) {
    toast("Forest signals end in 2018. Use weather or fire memory.");
    return;
  }
  if (type === "feature") {
    if (!s.features.includes(value) && s.features.length === s.width) {
      const old = s.features.shift();
      toast(`${data.features[old].label} → ${data.features[value].label}`);
    }
    const effect = toggle(s, value);
    if (effect) audio.effect(effect);
  }
  if (type === "width") {
    setWidth(s, value);
    audio.effect("patch");
  }
  if (type === "angle") {
    s.angle =
      angles[
        Math.max(
          0,
          Math.min(angles.length - 1, angles.indexOf(s.angle) + value),
        )
      ];
    audio.effect("patch");
  }
  if (type === "strength" || type === "epsilon") {
    const values = type === "strength" ? [0.3, 1, 3, 10] : [0.05, 0.2, 0.5],
      key = type === "strength" ? "C" : "epsilon";
    s[key] =
      values[
        Math.max(0, Math.min(values.length - 1, values.indexOf(s[key]) + value))
      ];
    audio.effect("patch");
  }
  if (type === "sound") {
    try {
      await audio.toggle();
    } catch {
      toast("Audio unavailable. The game is ready.");
    }
  }
  if (type === "year") s.selectedYear = value;
  if (type === "restore" && s.previous) {
    Object.assign(s, s.previous.build);
    s.width = s.features.length;
    toast("Previous build restored. Run to compare.");
  }
  if (type === "next") {
    if (!assessment(s).won || !currentResult(s)) return;
    if (s.round < data.rounds.length - 1) {
      melt.start(canvas, reduce);
      s.round++;
      s.result = null;
      s.previous = null;
      s.sample = null;
      const open = data.rounds[s.round].available;
      if (open) {
        // Keep only signals this season provides, then refill the build.
        s.width = Math.min(s.width, open.length);
        s.features = s.features.filter((j) => open.includes(j));
        for (const j of open)
          if (s.features.length < s.width && !s.features.includes(j))
            s.features.push(j);
      }
      toast(
        open
          ? "Season 4: 2019–2024. Weather and fire-memory signals only."
          : "Next season. Build your starting engine.",
      );
    } else {
      s.finished = true;
      s.celebrate = true;
      audio.effect("win");
    }
  }
  if (type === "celebrate-done") {
    s.celebrate = false;
    s.menu = true;
    location.hash = "main-menu";
  }
  if (type === "sample" || type === "more-shots") {
    const method = type === "more-shots" ? s.sample?.method || "qaoa" : value;
    if (method === "mi" || method === "exact") {
      const f = data.rounds[s.round].selectors[method],
        mask = f.reduce((m, j) => m + (1 << j), 0);
      s.sample = {
        method,
        shots: 0,
        candidates: [
          { features: f, energy: data.rounds[s.round].objective[mask] },
        ],
      };
    } else
      s.sample = sampleCandidates(
        data.rounds[s.round].objective,
        type === "more-shots" ? 256 : 64,
        31 + s.attempts,
        method,
      );
    s.candidate = 0;
    audio.effect("run");
  }
  if (type === "candidate") s.candidate = value;
  if (type === "apply" && s.sample) {
    s.features = [...s.sample.candidates[s.candidate || 0].features];
    s.width = 4;
    s.foundry = false;
    toast("Subset patched. Open Results to compare.");
  }
  if ((type === "run" || type === "auto-test") && !s.help && s.features.length === s.width) {
    auto.cancel();
    const automatic = type === "auto-test";
    if (currentResult(s)) return;
    const spec = build(s),
      round = s.round,
      token = ++runningToken;
    s.running = true;
    if (!automatic) audio.effect("run");
    status.textContent = "Calculating quantum similarities and fitting SVR.";
    // Give the canvas time to show the relay before the small local calculation.
    await new Promise((resolve) => setTimeout(resolve, automatic || reduce ? 20 : 500));
    try {
      const start = performance.now(),
        result = run(data, spec, round);
      if (token !== runningToken) return;
      result.elapsedMs = performance.now() - start;
      record(s, result);
      s.runAt = reduce ? 0 : performance.now();
      if (!automatic) s.tab = "results";
      const a = assessment(s);
      if (a.won || !automatic) toast(a.won ? "CONTRACT COMPLETE" : "RUN SAVED");
      status.textContent = `Run saved: ${result.mae.toFixed(1)} hectares per fire MAE. RBF ${result.rbfMAE.toFixed(1)}; mean ${result.meanMAE.toFixed(1)}. ${a.won ? "Contract complete." : "Try another build."}`;
      if (a.won || !automatic) audio.effect(a.won ? "win" : "patch");
    } catch (error) {
      console.error(error);
      toast("Run could not finish. Your build is preserved.");
    }
    s.running = false;
  }
  geometry = preview(data, build(s), s.round);
  dirty();
  if (["start", "new", "feature", "width", "angle", "strength", "epsilon", "apply", "restore", "next"].includes(type)) {
    auto.schedule();
    if (auto.pending) status.textContent = "Evaluating the current build.";
  }
}
action.audio = audio;
action.rounds = data.rounds.length;
function draw(timestamp) {
  const dpr = Math.min(2, devicePixelRatio);
  ctx.setTransform(dpr * scale, 0, 0, dpr * scale, 0, 0);
  p.hits = [];
  p.choiceLocked = !s.help && contractLocked(s);
  const time = reduce ? 0 : timestamp / 1000;
  tourReceipt = null;
  if (s.help && s.guideIntro) {
    tourReceipt = drawTour(p, s, data, assets, action, W, H, time, geometry);
  } else {
    if (s.menu) menu(p, s, assets, action, W, H, time);
    else drawWorkbench(p, { ...s, evaluating: auto.pending || s.running },
      data, assets, action, W, H, time, hover, geometry);
    if (s.foundry) {
      p.hits = [];
      foundry(p, s, data, action, W, H);
    }
    if (s.help) {
      p.hits = [];
      drawGuide(p, s, action, W, H, time, assets);
    }
    if (s.celebrate) celebration(p, s, action, W, H, time);
  }
  melt.draw(ctx, timestamp);
  if (melt.active) p.hits = [];
  mirror();
  requestAnimationFrame(draw);
}
connectInput(
  canvas,
  p,
  () => ({ scale, W, state: s, point: () => hover, hover: (v) => (hover = v) }),
  action,
  dirty,
);
window.addEventListener("resize", resize);
window.addEventListener("hashchange", () => {
  if (location.hash === "#main-menu") s.menu = true;
  else if (location.hash === "#workbench") s.menu = false;
});
resize();
requestAnimationFrame(draw);
// Read-only state/geometry receipt for browser checks; no hidden gameplay actions.
window.fireline = {
  transition: () => ({ active: melt.active, reducedMotion: reduce }),
  snapshot: () => structuredClone({ ...s, running: !!s.running, evaluating: auto.pending || !!s.running }),
  tour: () => structuredClone(tourReceipt),
  controls: () =>
    p.hits.map(({ id, label, x, y, w, h, disabled }) => ({
      id,
      label,
      x,
      y,
      w,
      h,
      disabled,
    })),
  audio: () => ({
    enabled: audio.enabled,
    state: audio.ctx?.state,
    timer: !!audio.timer,
    playing: audio.playing,
    track: !!audio.music,
  }),
};

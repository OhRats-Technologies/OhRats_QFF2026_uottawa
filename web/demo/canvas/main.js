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
import { sampleCandidates } from "./foundry.js";
const canvas = document.querySelector("canvas"),
  ctx = canvas.getContext("2d"),
  p = new Paint(ctx),
  audio = new Audio();
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
const a11y = document.querySelector("#controls"),
  status = document.querySelector("#status");
const mirror = controlMirror(p, a11y, audio, () => s);
function resize() {
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
  if (
    s.running &&
    type !== "sound" &&
    type !== "help" &&
    !type.startsWith("guide-")
  )
    return;
  if (guideAction(s, type, value, status)) {
    dirty();
    return;
  }
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
  if (type === "tab") s.tab = value;
  if (type === "rack-page") s.rackPage = ((s.rackPage || 0) + 1) % value;
  if (type === "foundry") {
    s.foundry = !s.foundry;
    s.candidate = 0;
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
    if (s.round < 2) {
      s.round++;
      s.result = null;
      s.previous = null;
      s.sample = null;
      toast("Next season. Build your starting engine.");
    } else {
      s.finished = true;
      s.menu = true;
      location.hash = "main-menu";
      toast("All seasons complete.");
    }
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
    toast("Subset patched. Run it against your last build.");
  }
  if (type === "run" && !s.help && s.features.length === s.width) {
    const spec = build(s),
      round = s.round,
      token = ++runningToken;
    s.running = true;
    audio.effect("run");
    status.textContent = "Calculating quantum similarities and fitting SVR.";
    // Give the canvas time to show the relay before the small local calculation.
    await new Promise((resolve) => setTimeout(resolve, reduce ? 20 : 500));
    try {
      const start = performance.now(),
        result = run(data, spec, round);
      if (token !== runningToken) return;
      result.elapsedMs = performance.now() - start;
      record(s, result);
      s.runAt = reduce ? 0 : performance.now();
      s.tab = "results";
      const a = assessment(s);
      toast(a.won ? "CONTRACT COMPLETE" : "RUN SAVED");
      status.textContent = `Run saved: ${result.mae.toFixed(1)} hectares per fire MAE. RBF ${result.rbfMAE.toFixed(1)}; mean ${result.meanMAE.toFixed(1)}. ${a.won ? "Contract complete." : "Repair and run again."}`;
      audio.effect(a.won ? "win" : "patch");
    } catch (error) {
      console.error(error);
      toast("Run could not finish. Your build is preserved.");
    }
    s.running = false;
  }
  geometry = preview(data, build(s), s.round);
  dirty();
}
action.audio = audio;
function draw(timestamp) {
  const dpr = Math.min(2, devicePixelRatio);
  ctx.setTransform(dpr * scale, 0, 0, dpr * scale, 0, 0);
  p.hits = [];
  const time = reduce ? 0 : timestamp / 1000;
  tourReceipt = null;
  if (s.help && s.guideIntro) {
    tourReceipt = drawTour(p, s, data, assets, action, W, H, time, geometry);
  } else {
    if (s.menu) menu(p, s, assets, action, W, H, time);
    else drawWorkbench(p, s, data, assets, action, W, H, time, hover, geometry);
    if (s.foundry) {
      p.hits = [];
      foundry(p, s, data, action, W, H);
    }
    if (s.help) {
      p.hits = [];
      drawGuide(p, s, action, W, H, time, assets);
    }
  }
  const drag = currentDrag();
  if (
    drag &&
    Math.hypot(drag.point.x - drag.start.x, drag.point.y - drag.start.y) > 16
  )
    p.cable(drag.start.x, drag.start.y, drag.point.x, drag.point.y, time);
  mirror();
  requestAnimationFrame(draw);
}
const currentDrag = connectInput(
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
  snapshot: () => structuredClone({ ...s, running: !!s.running }),
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
  }),
};

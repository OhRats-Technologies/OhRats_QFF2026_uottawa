import { createRequire } from "node:module";
import { mkdirSync, writeFileSync } from "node:fs";
import assert from "node:assert/strict";
const require = createRequire(import.meta.url),
  { chromium } = require(`${process.env.RUNTIME_NODE_MODULES}/playwright`),
  out = process.env.FIRELINE_OUTPUT || ".cache/fireline-canvas";
mkdirSync(out, { recursive: true });
const b = await chromium.launch({ channel: "chrome", headless: true });
const c = await b.newContext({
    viewport: { width: 1440, height: 900 },
    hasTouch: true,
  }),
  page = await c.newPage(),
  errors = [];
page.on("pageerror", (e) => errors.push(e.message));
await page.goto(
  `${process.env.FIRELINE_BASE || "http://127.0.0.1:8790"}/web/demo/`,
);
await page.waitForFunction(() => window.fireline);
// A strong first engine keeps later ten-input trials below the contract, so
// restoration is exercised before choices lock. Completed locks have their own check.
await page.evaluate(async () => {
  const { fresh } = await import("./canvas/session.js"), s = fresh();
  s.features = [7, 11, 16, 17];
  localStorage.setItem("fireline-canvas-v2", JSON.stringify(s));
});
await page.reload();
await page.waitForFunction(() => window.fireline);
async function target(id) {
  await page.waitForFunction(
    (id) => window.fireline.controls().some((h) => h.id === id && !h.disabled),
    id,
  );
  const h = await page.evaluate(
    (id) => window.fireline.controls().find((h) => h.id === id),
    id,
  );
  const scale = await page.evaluate(
    () => innerWidth / Math.max(390, innerWidth),
  );
  return { x: (h.x + h.w / 2) * scale, y: (h.y + h.h / 2) * scale };
}
async function click(id) {
  const p = await target(id);
  await page.mouse.click(p.x, p.y);
  await page.waitForTimeout(60);
}
await click("continue");
if (await page.evaluate(() => window.fireline.snapshot().guideIntro))
  await click("guide-skip");
await page.waitForFunction(() => window.fireline.snapshot().attempts === 1 && !window.fireline.snapshot().running);
// Dragging a signal onto the engine must not patch it; a click does.
const source = await target("signal-5");
await page.mouse.move(source.x, source.y);
await page.mouse.down();
await page.mouse.move(900, 210, { steps: 10 });
await page.mouse.up();
await page.waitForTimeout(200);
assert.ok(!(await page.evaluate(() => window.fireline.snapshot().features)).includes(5));
await click("signal-5");
await page.waitForFunction(() =>
  window.fireline.snapshot().features.includes(5),
);
await page.locator('[data-id="signal-12"]').focus();
await page.keyboard.press("Enter");
await page.waitForFunction(() =>
  window.fireline.snapshot().features.includes(12),
);
await click("width-10");
for (const id of [
  "signal-0",
  "signal-4",
  "signal-6",
  "signal-8",
  "signal-10",
  "signal-11",
])
  await click(id);
await page.waitForFunction(
  () =>
    window.fireline.snapshot().result?.build.features.length === 10 &&
    !window.fireline.snapshot().running,
);
const first = await page.evaluate(() => window.fireline.snapshot().result);
// Rapid patching now offers Betty help once; dismiss it before continuing the input audit.
await page.waitForFunction(() => window.fireline.coach().open);
await click("coach-close");
await click("angle-up");
await page.waitForFunction(
  () =>
    window.fireline.snapshot().attempts === 3 &&
    !window.fireline.snapshot().running,
);
await click("undo");
const restored = await page.evaluate(() => window.fireline.snapshot());
assert.deepEqual(restored.features, first.build.features);
assert.equal(restored.angle, first.build.angle);
await click("sound");
await page.waitForFunction(() => window.fireline.audio().state === "running");
// Dispatch visibility transitions to verify the explicit lifecycle handler deterministically.
await page.evaluate(() => {
  Object.defineProperty(document, "hidden", {
    configurable: true,
    value: true,
  });
  document.dispatchEvent(new Event("visibilitychange"));
});
await page.waitForFunction(
  () =>
    window.fireline.audio().state === "suspended" &&
    !window.fireline.audio().playing,
);
await page.evaluate(() => {
  Object.defineProperty(document, "hidden", {
    configurable: true,
    value: false,
  });
  document.dispatchEvent(new Event("visibilitychange"));
});
await page.waitForFunction(
  () =>
    window.fireline.audio().state === "running" &&
    window.fireline.audio().playing,
);
await click("sound");
await page.waitForFunction(
  () =>
    !window.fireline.audio().enabled &&
    window.fireline.audio().state === "suspended",
);
await click("help");
await page.keyboard.press("Escape");
await page.waitForFunction(() => !window.fireline.snapshot().help);
await page.setViewportSize({ width: 390, height: 844 });
const t = await target("tab-rack");
await page.touchscreen.tap(t.x, t.y);
await page.waitForFunction(() => window.fireline.snapshot().tab === "rack");
const sig = await target("signal-19");
await page.touchscreen.tap(sig.x, sig.y);
await page.waitForFunction(() =>
  window.fireline.snapshot().features.includes(19),
);
await page.evaluate(() => localStorage.setItem("fireline-canvas-v2", "{bad"));
await page.reload();
await page.waitForFunction(() => window.fireline);
assert.equal(await page.evaluate(() => window.fireline.snapshot().attempts), 0);
await page.addInitScript(() => {
  Storage.prototype.getItem = () => {
    throw new Error("blocked");
  };
  Storage.prototype.setItem = () => {
    throw new Error("blocked");
  };
});
await page.reload();
await page.waitForFunction(() => window.fireline);
await click("continue");
await click("guide-skip");
await page.waitForFunction(
  () =>
    window.fireline.snapshot().attempts === 1 &&
    !window.fireline.snapshot().running,
);
const music = await page.evaluate(async () => {
  const { Audio } = await import("./canvas/audio.js"),
    a = new Audio(),
    c = new OfflineAudioContext(1, 48000 * 8, 48000);
  a.ctx = c;
  a.master = c.createGain();
  a.master.gain.value = 0.5;
  a.master.connect(c.destination);
  a.enabled = true;
  const notes = [
    62, 69, 72, 76, 74, 69, 67, 65, 62, 69, 71, 76, 74, 72, 69, 67,
  ];
  notes.forEach((n, i) =>
    a.tone(440 * 2 ** ((n - 69) / 12), (i * 60000) / 78 / 2000, 0.65, 0.035),
  );
  [38, 38, 43, 45].forEach((n, i) =>
    a.tone(
      440 * 2 ** ((n - 69) / 12),
      (i * 4 * 60000) / 78 / 2000,
      1.35,
      0.065,
      "sine",
    ),
  );
  const buffer = await c.startRendering(),
    v = buffer.getChannelData(0);
  let peak = 0,
    sum = 0;
  for (const x of v) {
    peak = Math.max(peak, Math.abs(x));
    sum += x * x;
  }
  return { peak, rms: Math.sqrt(sum / v.length), seconds: 8 };
});
assert.ok(music.peak < 0.98 && music.rms > 0.001);
assert.deepEqual(errors, []);
const receipt = {
  dragDoesNotLink: true,
  keyboardPatch: true,
  tenInputRun: true,
  rapidClickHintDismissal: true,
  previousBuildRestore: true,
  optInMusicMute: true,
  simulatedVisibilitySuspendResume: true,
  touchPatch: true,
  corruptAndBlockedStorage: true,
  music,
  errors,
};
writeFileSync(
  `${out}/interaction-receipt.json`,
  JSON.stringify(receipt, null, 2) + "\n",
);
console.log(JSON.stringify(receipt));
await b.close();

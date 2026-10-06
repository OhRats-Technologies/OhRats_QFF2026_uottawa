// Touch-emulated input, not just a narrow desktop viewport or physical-device claim.
import assert from "node:assert/strict";
import fs from "node:fs/promises";
import { createHash } from "node:crypto";
import { execFileSync } from "node:child_process";
import { createRequire } from "node:module";
import { createRun, action, advance, active, available, forecast } from "./rules.js";
import { upgradeChoices, applyUpgrade } from "./upgrades.js";

const source = JSON.parse(await fs.readFile("web/demo/assets/context/scenario.json", "utf8"));
const hash = bytes => createHash("sha256").update(bytes).digest("hex");
const require = createRequire(`${process.env.RUNTIME_NODE_MODULES}/../package.json`);
const { chromium } = require("playwright");
const browser = await chromium.launch({ headless: true, channel: "chrome", args: ["--mute-audio"] });
const out = ".cache/judge-submission/touch-controls";
await fs.mkdir(out, { recursive: true });
const snapshot = page => page.evaluate(() => JSON.parse(localStorage.getItem("fireline-season")));
const results = [], errors = [];

async function gesture(cdp, start, finish) {
  const point = (x, y) => [{ x, y, id: 0, radiusX: 8, radiusY: 8, force: 1 }];
  await cdp.send("Input.dispatchTouchEvent", { type: "touchStart", touchPoints: point(...start) });
  for (let i = 1; i <= 6; i++) {
    await cdp.send("Input.dispatchTouchEvent", { type: "touchMove", touchPoints: point(
      start[0] + (finish[0] - start[0]) * i / 6,
      start[1] + (finish[1] - start[1]) * i / 6) });
    await new Promise(resolve => setTimeout(resolve, 20));
  }
  await cdp.send("Input.dispatchTouchEvent", { type: "touchEnd", touchPoints: [] });
}

async function baselineOcclusion() {
  const commit = "2da8cd8";
  const paths = ["web/demo/index.html", "web/demo/assets/strategy.js",
    "web/demo/strategy/styles/instruments.css"];
  const bytes = Object.fromEntries(paths.map(path =>
    [path, execFileSync("git", ["show", `${commit}:${path}`])]));
  const page = await browser.newPage({ viewport: { width: 320, height: 568 },
    hasTouch: true, isMobile: true, deviceScaleFactor: 3, reducedMotion: "reduce" });
  page.setDefaultTimeout(10000);
  await page.route("https://**/*", route => route.abort());
  await page.route("**/web/demo/**", route => {
    const path = new URL(route.request().url()).pathname.slice(1);
    const key = path === "web/demo/" ? "web/demo/index.html" : path;
    return bytes[key] ? route.fulfill({ body: bytes[key], contentType:
      key.endsWith(".html") ? "text/html" : key.endsWith(".css") ? "text/css" : "text/javascript" })
      : route.continue();
  });
  await page.goto("http://127.0.0.1:8790/web/demo/?qa=touch-baseline#season=7");
  await page.locator("#start").tap();
  const before = await snapshot(page);
  await page.locator("#lens-toggle").tap();
  await page.locator("#damping").scrollIntoViewIfNeeded();
  const rail = await page.locator("#damping .slider-rail").boundingBox();
  const hits = await page.evaluate(rail => [.1, .9].map(t =>
    document.elementFromPoint(rail.x + rail.width * t, rail.y + rail.height / 2)?.id), rail);
  assert.deepEqual(hits, ["advance", "advance"]);
  assert.deepEqual(await snapshot(page), before);
  await page.screenshot({ path: `${out}/320-baseline-occlusion.png` });
  await page.close();
  return { commit, viewport: [320, 568], rail, hit_ids: hits, save_unchanged: true,
    wrong_target_gesture_not_dispatched: true,
    source_sha256: Object.fromEntries(paths.map(path => [path, hash(bytes[path])])),
    scope: "Minimum authoring scroll leaves the old rail behind the sticky Advance button; manual additional scrolling was not ruled out." };
}

async function inspectTouch(page, cdp, width, height) {
  const before = await snapshot(page);
  await page.locator("#lens-toggle").tap();
  await page.locator("#damping").scrollIntoViewIfNeeded();
  const rail = await page.locator("#damping .slider-rail").boundingBox();
  const min = Number(await page.locator("#damping").getAttribute("aria-valuemin"));
  const max = Number(await page.locator("#damping").getAttribute("aria-valuemax"));
  const scroll = await page.evaluate(() => scrollY);
  const y = rail.y + rail.height / 2;
  const hitSlider = await page.evaluate(({ rail, y }) => [.1, .9].every(t =>
    document.elementFromPoint(rail.x + rail.width * t, y)?.closest("#damping")), { rail, y });
  assert.equal(hitSlider, true, `${width}: opened controls remain behind another element`);
  assert.deepEqual(await snapshot(page), before);
  await gesture(cdp, [rail.x + rail.width * .1, y], [rail.x + rail.width * .9, y]);
  const value = Number(await page.locator("#damping").getAttribute("aria-valuenow"));
  if (Math.abs(value - (min + (max - min) * .9)) > .011) {
    await page.screenshot({ path: `${out}/${width}-slider-failure.png` });
    const hit = await page.evaluate(({ rail, y }) => ({
      atStart: document.elementFromPoint(rail.x + rail.width * .1, y)?.outerHTML.slice(0, 180),
      atEnd: document.elementFromPoint(rail.x + rail.width * .9, y)?.outerHTML.slice(0, 180),
      slider: document.querySelector("#damping").getBoundingClientRect().toJSON(),
      lastEvents: touchQA.slice(-3), scrollY, viewport: { width: innerWidth, height: innerHeight },
    }), { rail, y });
    console.log(JSON.stringify({ width, rail, hit, value }));
  }
  assert.ok(Math.abs(value - (min + (max - min) * .9)) <= .011, `Touch drag gave ${value}`);
  assert.equal(await page.evaluate(() => scrollY), scroll);
  assert.deepEqual(await snapshot(page), before);
  await page.screenshot({ path: `${out}/${width}-controls.png` });
  await page.locator("#lens-toggle").tap();
  await page.locator("#sample").tap();
  const cost = await page.locator("#energy").evaluate(node => ({
    height: node.getBoundingClientRect().height, fontSize: parseFloat(getComputedStyle(node).fontSize),
  }));
  assert.ok(cost.height <= cost.fontSize * 1.6, `${width}: proxy cost wraps into multiple lines`);
  await page.locator("#matrix-mode").tap();
  await page.locator("#bench-dialog[open]").waitFor();
  await page.locator("#bench-close").tap();
  assert.deepEqual(await snapshot(page), before);
  await page.locator("#layer").selectOption("height-change");
  await page.locator("#legend-toggle").tap();
  assert.equal(await page.locator("#map-legend").isVisible(), true);
  await page.locator("#legend-toggle").tap();
  await page.locator("#layer").selectOption("cover");
  assert.deepEqual(await snapshot(page), before);
  assert.equal(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth), true);
  return { width, height, slider_value: value, slider_scroll_unchanged: true,
    slider_rail_width: rail.width, inspection_save_unchanged: true, native_select_via_authoring_api: true };
}

try {
  const baseline = await baselineOcclusion();
  for (const [width, height, reducedMotion] of [[390, 844, "no-preference"], [320, 568, "reduce"]]) {
    const page = await browser.newPage({ viewport: { width, height }, hasTouch: true,
      isMobile: true, deviceScaleFactor: 3, reducedMotion });
    page.setDefaultTimeout(10000);
    page.on("pageerror", error => errors.push(error.message));
    await page.route("https://**/*", route => route.abort());
    await page.addInitScript(() => {
      globalThis.touchQA = [];
      document.addEventListener("pointerdown", e => touchQA.push({ type: e.pointerType,
        target: e.target.closest("button,[role=slider]")?.id || e.target.tagName }), true);
    });
    const cdp = await page.context().newCDPSession(page);
    await page.goto(`http://127.0.0.1:8790/web/demo/?qa=touch-${width}#season=7`);
    await page.locator("#start").tap();
    const beforeSwipe = await snapshot(page);
    const beforeScroll = await page.evaluate(() => scrollY);
    await gesture(cdp, [width - 8, Math.min(height - 160, 380)], [width - 8, 120]);
    await page.waitForFunction(previous => scrollY > previous, beforeScroll);
    assert.deepEqual(await snapshot(page), beforeSwipe);
    const inspections = [await inspectTouch(page, cdp, width, height)];
    console.log(`${width}: touch slider and read-only inspections passed.`);
    const state = createRun(7, source.pool), moves = [];
    while (state.status === "playing" && state.turn < 10) {
      if (state.upgradePending) {
        const choices = upgradeChoices(state);
        const choice = choices.find(item => item.id === "network") ?? choices[0];
        await page.locator(`[data-upgrade="${choice.id}"]`).tap();
        assert.equal(applyUpgrade(state, choice.id), true);
        moves.push({ type: "upgrade", id: choice.id });
      }
      async function respond(fire, kind) {
        await page.locator(`[data-incident="${fire.id}"]`).tap();
        await page.locator(`[data-action="${kind}"]`).tap();
        assert.equal(action(state, fire.id, kind), true);
        moves.push({ type: "action", id: fire.id, kind });
      }
      const fires = active(state).sort((a, b) => b.size - a.size);
      for (const fire of fires) if (!fire.crew && available(state) && state.supplies >= 2) await respond(fire, "crew");
      for (const fire of fires) if (forecast(state, fire) > 1.1 && state.supplies >= 4) await respond(fire, "water");
      await page.locator("#advance").tap();
      assert.equal(advance(state), true);
      moves.push({ type: "advance" });
    }
    assert.equal(state.turn, 10);
    assert.equal(state.status, "playing");
    assert.deepEqual((await snapshot(page)).moves, moves);
    await page.locator("#map-frame").scrollIntoViewIfNeeded();
    // Fire 2 is contained, so select its map marker rather than the active-only list.
    const contained = await page.locator('[data-fire="2"]').boundingBox();
    await page.touchscreen.tap(contained.x + contained.width / 2, contained.y + contained.height / 2);
    if (await page.locator("#nearby-fires").evaluate(d => d.open))
      await page.locator('[data-pick-fire="2"]').tap();
    assert.equal((await snapshot(page)).selected, 2);
    const beforePicker = await snapshot(page);
    const box = await page.locator('[data-fire="13"]').boundingBox();
    await page.touchscreen.tap(box.x + box.width / 2, box.y + box.height / 2);
    await page.locator("#nearby-fires[open]").waitFor();
    assert.deepEqual(await snapshot(page), beforePicker);
    await page.locator('[data-pick-fire="13"]').tap();
    assert.equal((await snapshot(page)).selected, 13);
    assert.deepEqual((await snapshot(page)).moves, moves);
    assert.equal(await page.locator("#nearby-fires").evaluate(d => d.open), false);
    assert.equal(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth), true);
    console.log(`${width}: ten-front touch history and overlap selection passed.`);
    await page.screenshot({ path: `${out}/${width}-late.png`, fullPage: true });
    if (width === 390) {
      const beforeRotate = await snapshot(page);
      await page.setViewportSize({ width: 844, height: 390 });
      inspections.push(await inspectTouch(page, cdp, 844, 390));
      assert.deepEqual(await snapshot(page), beforeRotate);
      await page.screenshot({ path: `${out}/landscape.png`, fullPage: true });
    }
    const events = await page.evaluate(() => touchQA);
    assert.ok(events.length > 25 && events.every(event => event.type === "touch"));
    results.push({ width, height, reduced_motion: reducedMotion, seed: 7, completed_fronts: 10,
      accepted_moves: moves.length, move_replay_exact: true, touch_events: events.length,
      every_observed_pointer_was_touch: true, vertical_page_swipe: true,
      late_overlap_selection: 13, inspections });
    await cdp.detach();
    await page.close();
  }
  assert.deepEqual(errors, []);
  const hashes = {};
  for (const name of ["rules.js", "scenario.js", "upgrades.js", "session.js", "slider.js", "marker-picker.js",
    "main.js", "touch-check.mjs"]) {
    const path = `web/demo/strategy/${name}`, bytes = await fs.readFile(path);
    hashes[path] = hash(bytes);
    if (["rules.js", "scenario.js", "upgrades.js", "session.js"].includes(name))
      assert.equal(hash(bytes), hash(execFileSync("git", ["show", `HEAD:${path}`])));
  }
  for (const path of ["web/demo/index.html", "web/demo/assets/strategy.js", "web/demo/assets/context/scenario.json",
    "web/demo/strategy/styles/instruments.css", "web/demo/strategy/styles/responsive.css"])
    hashes[path] = hash(await fs.readFile(path));
  await fs.writeFile(`${out}/receipt.json`, JSON.stringify({ checked_utc: new Date().toISOString(),
    status: "passed", baseline, source_sha256: hashes, results, errors, predictor_fits: 0,
    quantum_circuit_executions: 0, hardware_jobs: 0,
    scope: "Chromium mobile touch emulation on a Mac: actual taps and CDP touch gestures, two ten-front histories and portrait-to-landscape resize. Offscreen locators auto-scroll; native select uses authoring API. No physical touch, OS picker, human enjoyment or broad device certification.",
  }, null, 2) + "\n");
  console.log("Touch taps, captured slider drags, exact move replay and active overlap choice pass in phone/landscape views.");
} finally { await browser.close(); }

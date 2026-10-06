// Actual late-season overlap regression; preserve source positions and moves.
import assert from "node:assert/strict";
import fs from "node:fs/promises";
import { createHash } from "node:crypto";
import { execFileSync } from "node:child_process";
import { createRequire } from "node:module";
import { createRun, action, advance, active, available, forecast } from "./rules.js";
import { upgradeChoices, applyUpgrade } from "./upgrades.js";

const hash = bytes => createHash("sha256").update(bytes).digest("hex");
const source = JSON.parse(await fs.readFile("web/demo/assets/context/scenario.json", "utf8"));
const baselineCommit = "079c8e4";
const baselineMarkers = execFileSync("git", ["show", `${baselineCommit}:web/demo/strategy/styles/map-markers.css`]);
const baselineBundle = execFileSync("git", ["show", `${baselineCommit}:web/demo/assets/strategy.js`]);
const require = createRequire(`${process.env.RUNTIME_NODE_MODULES}/../package.json`);
const { chromium } = require("playwright");
const browser = await chromium.launch({ headless: true, channel: "chrome", args: ["--mute-audio"] });
const out = ".cache/judge-submission/marker-picker";
await fs.mkdir(out, { recursive: true });
const results = [], errors = [], pinned = {};
const snapshot = page => page.evaluate(() => JSON.parse(localStorage.getItem("fireline-season")));
try {
  for (const [width, height, baseline] of [[390, 844, true], [1280, 720, false], [1024, 768, false], [390, 844, false]]) {
    const page = await browser.newPage({ viewport: { width, height }, reducedMotion: "no-preference" });
    page.on("pageerror", error => errors.push(error.message));
    await page.route("https://**/*", route => route.abort());
    if (baseline) await page.route("**/web/demo/assets/strategy.js", route => route.fulfill({
      body: baselineBundle, contentType: "text/javascript" }));
    if (baseline) await page.route("**/web/demo/strategy/styles/map-markers.css", route => route.fulfill({
      body: baselineMarkers, contentType: "text/css" }));
    await page.goto(`http://127.0.0.1:8790/web/demo/?qa=picker-${width}-${baseline}#season=7`);
    await page.locator("#start").click();
    const state = createRun(7, source.pool);
    while (state.status === "playing" && state.turn < 10) {
      if (state.upgradePending) {
        const choices = upgradeChoices(state);
        const choice = choices.find(item => item.id === "network") ?? choices[0];
        await page.locator(`[data-upgrade="${choice.id}"]`).click();
        assert.equal(applyUpgrade(state, choice.id), true);
      }
      async function respond(fire, kind) {
        await page.locator(`[data-incident="${fire.id}"]`).click();
        await page.locator(`[data-action="${kind}"]`).click();
        assert.equal(action(state, fire.id, kind), true);
      }
      const fires = active(state).sort((a, b) => b.size - a.size);
      for (const fire of fires) if (!fire.crew && available(state) && state.supplies >= 2) await respond(fire, "crew");
      for (const fire of fires) if (forecast(state, fire) > 1.1 && state.supplies >= 4) await respond(fire, "water");
      await page.locator("#advance").click();
      assert.equal(advance(state), true);
    }
    assert.equal(state.turn, 10);
    assert.equal(state.status, "playing");
    assert.equal(state.incidents.find(fire => fire.id === 13).status, "burning");
    await page.locator("#map-frame").scrollIntoViewIfNeeded();
    await page.locator('[data-fire="2"]').press("Enter");
    const before = await snapshot(page);
    const hit = await page.locator('[data-fire="13"]').evaluate(node => {
      const box = node.getBoundingClientRect(), x = box.x + 15, y = box.y + 15;
      return { x, y, top: Number(document.elementFromPoint(x, y)?.closest("[data-fire]")?.dataset.fire) };
    });
    assert.notEqual(hit.top, 13);
    await page.mouse.click(hit.x, hit.y);
    if (baseline) {
      assert.equal(await page.locator("#nearby-fires").count(), 0);
      assert.equal((await snapshot(page)).selected, hit.top);
      results.push({ width, baseline: true, desired: 13, selected: hit.top, reproduced_wrong_center_selection: true });
      await page.close();
      continue;
    }
    await page.locator("#nearby-fires[open]").waitFor();
    assert.deepEqual(await snapshot(page), before);
    const offered = await page.locator("[data-pick-fire]").evaluateAll(nodes => nodes.map(node => Number(node.dataset.pickFire)));
    assert.ok(offered.includes(13) && offered.includes(hit.top));
    assert.ok(await page.locator("[data-pick-fire]").first().evaluate(node => node === document.activeElement));
    const frame = await page.locator("#nearby-fires").evaluate(node => {
      const box = node.getBoundingClientRect();
      return { left: box.left, right: box.right, top: box.top, bottom: box.bottom,
        overflow: node.scrollWidth > node.clientWidth };
    });
    assert.ok(frame.left >= 0 && frame.right <= width && frame.top >= 0 && frame.bottom <= height);
    assert.equal(frame.overflow, false);
    await page.keyboard.press("n");
    assert.deepEqual(await snapshot(page), before);
    await page.screenshot({ path: `${out}/${width}.png`, fullPage: false });
    await page.keyboard.press("Escape");
    await page.waitForFunction(id => document.activeElement?.dataset.fire === String(id), hit.top);
    assert.deepEqual(await snapshot(page), before);
    await page.mouse.click(hit.x, hit.y);
    await page.locator('[data-pick-fire="13"]').press("Enter");
    await page.waitForFunction(() => document.activeElement?.dataset.fire === "13");
    assert.equal(await page.locator("#nearby-fires").evaluate(node => node.open), false);
    const selected = await snapshot(page);
    assert.equal(selected.selected, 13);
    assert.deepEqual(selected.moves, before.moves);
    assert.deepEqual(selected.techniques, before.techniques);
    await page.locator('[data-fire="2"]').press("Enter");
    await page.mouse.click(hit.x, hit.y);
    await page.locator("#nearby-fires[open]").waitFor();
    await page.mouse.click(width - 2, 2);
    assert.equal(await page.locator("#nearby-fires").evaluate(node => node.open), false);
    await page.locator('[data-fire="13"]').press("Enter");
    assert.equal((await snapshot(page)).selected, 13);
    assert.equal(await page.locator("#nearby-fires").evaluate(node => node.open), false);
    await page.mouse.click(hit.x, hit.y);
    await page.locator("#nearby-fires[open]").waitFor();
    await page.setViewportSize({ width, height: height - 10 });
    await page.waitForFunction(() => !document.querySelector("#nearby-fires").open);
    for (const fire of state.incidents) {
      const marker = page.locator(`[data-fire="${fire.id}"]`);
      assert.ok(Math.abs(await marker.evaluate(node => parseFloat(node.style.left)) - fire.x * 100) < 1e-8);
      assert.ok(Math.abs(await marker.evaluate(node => parseFloat(node.style.top)) - fire.y * 100) < 1e-8);
      assert.equal(await marker.evaluate(node => getComputedStyle(node, "::after").pointerEvents), "none");
    }
    results.push({ width, height, seed: 7, status: state.status, completed_fronts: 10, selected_status: "burning", offered, frame,
      pointer_choice: 13, keyboard_direct: true, escape_outside_focus: true, resize_closes: true,
      moves_unchanged: true, source_positions_unchanged: true, coordinate_percent_tolerance: 1e-8 });
    await page.close();
  }
  assert.deepEqual(errors, []);
  for (const name of ["web/demo/strategy/rules.js", "web/demo/strategy/scenario.js", "web/demo/strategy/upgrades.js",
    "web/demo/strategy/session.js", "web/demo/assets/context/scenario.json"]) {
    const bytes = await fs.readFile(name);
    assert.equal(hash(bytes), hash(execFileSync("git", ["show", `HEAD:${name}`])));
    pinned[name] = hash(bytes);
  }
  for (const name of ["web/demo/strategy/marker-picker.js", "web/demo/strategy/map.js",
    "web/demo/strategy/styles/marker-picker.css", "web/demo/strategy/styles/map-markers.css", "web/demo/strategy/picker-check.mjs", "web/demo/strategy.css", "web/demo/assets/strategy.js"])
    pinned[name] = hash(await fs.readFile(name));
  await fs.writeFile(`${out}/receipt.json`, JSON.stringify({ checked_utc: new Date().toISOString(), status: "passed",
    baseline_commit: baselineCommit, baseline_bundle_sha256: hash(baselineBundle), baseline_markers_sha256: hash(baselineMarkers), source_sha256: pinned,
    results, errors, predictor_fits: 0, quantum_circuit_executions: 0, hardware_jobs: 0,
    scope: "Actual four control-driven ten-front histories reproduces wrong mobile center selection on the pinned old bundle, then verifies named overlap choice at three sizes. Opening/cancel leaves saves unchanged; choosing changes selection only. No marker relocation, rule change, physical touch or human enjoyment claim.",
  }, null, 2) + "\n");
  console.log("Old center-selection defect reproduced; pointer chooser and direct keyboard selection pass in three views.");
} finally { await browser.close(); }

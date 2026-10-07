import assert from "node:assert/strict";
import { createRequire } from "node:module";
import { mkdirSync, writeFileSync } from "node:fs";
const require = createRequire(import.meta.url),
  { chromium } = require(`${process.env.RUNTIME_NODE_MODULES}/playwright`),
  out = process.env.FIRELINE_OUTPUT || ".cache/fireline-live-test";
mkdirSync(out, { recursive: true });
const browser = await chromium.launch({ channel: "chrome", headless: true });
try {
  const page = await browser.newPage({ viewport: { width: 900, height: 700 }, reducedMotion: process.env.FIRELINE_MOTION === "animate" ? "no-preference" : "reduce" });
  const errors = [];
  page.on("pageerror", (e) => errors.push(e.message));
  await page.goto(`${process.env.FIRELINE_BASE || "http://127.0.0.1:8790"}/web/demo/`);
  await page.waitForFunction(() => window.fireline);
  const click = async (id) => {
    await page.locator(`[data-id="${id}"]`).evaluate((el) => el.click());
    await page.waitForTimeout(40);
  };
  await click("continue"); await click("guide-skip");
  await page.waitForFunction(() => window.fireline.snapshot().attempts === 1);
  assert.equal(await page.evaluate(() => window.fireline.snapshot().tab), "rack");
  assert.ok(!(await page.evaluate(() => window.fireline.controls())).some((h) => h.id === "next"));
  await click("tab-kernel");
  const choice = await page.evaluate(async () => {
    const { run } = await import("./canvas/engine.js"),
      { build } = await import("./canvas/session.js"),
      data = await fetch("./canvas/data.json").then((r) => r.json()),
      s = window.fireline.snapshot();
    return [Math.PI / 32, Math.PI / 8, Math.PI / 4, Math.PI / 2].find((angle) =>
      run(data, { ...build(s), angle }, 0).mae <= s.starts[0].mae * 0.95);
  });
  assert.ok(choice, "A reachable winning angle exists");
  const angles = [Math.PI / 32, Math.PI / 16, Math.PI / 8, Math.PI / 4, Math.PI / 2],
    delta = angles.indexOf(choice) - 1;
  for (let i = 0; i < Math.abs(delta); i++) await click(delta > 0 ? "angle-up" : "angle-down");
  assert.equal(await page.evaluate(() => window.fireline.snapshot().evaluating), true);
  assert.ok(!(await page.evaluate(() => window.fireline.controls())).some((h) => h.id === "run"), "No redundant Results footer action");
  assert.ok((await page.locator("#status").textContent()).includes("Evaluating"));
  await page.screenshot({ path: `${out}/evaluating.png` });
  await page.waitForFunction(() => window.fireline.snapshot().attempts === 2 && !window.fireline.snapshot().running);
  assert.equal(await page.evaluate(() => window.fireline.snapshot().tab), "kernel");
  assert.ok((await page.evaluate(() => window.fireline.controls())).some((h) => h.id === "next"));
  await page.waitForTimeout(600);
  assert.equal(await page.evaluate(() => window.fireline.snapshot().attempts), 2);
  await page.screenshot({ path: `${out}/live-win.png` });
  for (let i = 0; i < Math.abs(delta); i++) await click(delta > 0 ? "angle-down" : "angle-up");
  assert.ok(!(await page.evaluate(() => window.fireline.controls())).some((h) => h.id === "next"), "Editing hides stale victory immediately");
  await page.waitForFunction(() => window.fireline.snapshot().attempts === 3 && !window.fireline.snapshot().running);
  assert.ok(!(await page.evaluate(() => window.fireline.controls())).some((h) => h.id === "next"));
  for (let i = 0; i < Math.abs(delta); i++) await click(delta > 0 ? "angle-up" : "angle-down");
  await page.waitForFunction(() => window.fireline.snapshot().attempts === 4 && !window.fireline.snapshot().running);
  await click("next");
  await page.waitForFunction(() => window.fireline.snapshot().round === 1 && window.fireline.snapshot().attempts === 5);
  assert.ok(!(await page.evaluate(() => window.fireline.controls())).some((h) => h.id === "next"));
  assert.deepEqual(errors, []);
  writeFileSync(`${out}/receipt.json`, JSON.stringify({ automaticBaseline: true,
    inputChangeTestsWithoutNavigation: true, staysInEditor: true,
    coalescedEdits: true, winningBuildShowsNext: true, staleVictoryHiddenOnEdit: true,
    nextSeasonAutomaticallyTests: true, noDuplicateRuns: true, visibleEvaluatingState: true, noDuplicateResultsAction: true, errors }, null, 2) + "\n");
  console.log("Live input evaluation, win gating and automatic next-season baseline passed.");
} finally { await browser.close(); }

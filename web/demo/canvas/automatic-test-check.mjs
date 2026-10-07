import assert from "node:assert/strict";
import { createRequire } from "node:module";
import { mkdirSync, writeFileSync } from "node:fs";
const require = createRequire(import.meta.url),
  { chromium } = require(`${process.env.RUNTIME_NODE_MODULES}/playwright`),
  out = process.env.FIRELINE_OUTPUT || ".cache/fireline-auto-test";
mkdirSync(out, { recursive: true });
const browser = await chromium.launch({ channel: "chrome", headless: true });
try {
  const page = await browser.newPage({ viewport: { width: 900, height: 700 }, reducedMotion: "reduce" });
  const errors = [];
  page.on("pageerror", (e) => errors.push(e.message));
  await page.goto(`${process.env.FIRELINE_BASE || "http://127.0.0.1:8790"}/web/demo/`);
  await page.waitForFunction(() => window.fireline);
  const click = async (id) => {
    await page.locator(`[data-id="${id}"]`).evaluate((el) => el.click());
    await page.waitForTimeout(70);
  };
  await click("continue");
  await click("guide-skip");
  await click("tab-results");
  await page.waitForFunction(() => window.fireline.snapshot().attempts === 1 && !window.fireline.snapshot().running);
  const first = await page.evaluate(() => window.fireline.snapshot());
  await click("tab-rack");
  await click("tab-results");
  await click("tab-results");
  assert.equal(await page.evaluate(() => window.fireline.snapshot().attempts), 1, "Unchanged build does not rerun");
  await click("tab-kernel");
  await click("angle-up");
  await click("tab-results");
  await page.waitForFunction(() => window.fireline.snapshot().attempts === 2 && !window.fireline.snapshot().running);
  const next = await page.evaluate(() => window.fireline.snapshot());
  assert.notEqual(first.result.build.angle, next.result.build.angle);
  assert.equal(next.starts[0].mae, first.starts[0].mae, "First run challenge stays fixed");
  assert.ok((await page.evaluate(() => window.fireline.controls())).every((h) => !/[→←▶◀↔]/.test(h.label)));
  await page.screenshot({ path: `${out}/automatic-results.png` });
  await page.reload();
  await page.waitForFunction(() => window.fireline);
  await click("continue");
  await click("tab-results");
  assert.equal(await page.evaluate(() => window.fireline.snapshot().attempts), 2, "Restored result does not duplicate");
  assert.deepEqual(errors, []);
  writeFileSync(`${out}/receipt.json`, JSON.stringify({ openingResultsRuns: true,
    changedBuildRecalculates: true, unchangedAndRestoredDoNotRepeat: true,
    preservedBaseline: true, drawnButtonArrows: true, errors }, null, 2) + "\n");
  console.log("Automatic Results, duplicate protection, persistence and arrows passed.");
} finally { await browser.close(); }

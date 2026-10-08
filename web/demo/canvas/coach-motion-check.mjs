import assert from "node:assert/strict";
import { createRequire } from "node:module";
import { mkdirSync } from "node:fs";
const require = createRequire(import.meta.url),
  { chromium } = require(`${process.env.RUNTIME_NODE_MODULES}/playwright`),
  out = process.env.FIRELINE_OUTPUT || ".cache/fireline-coach-motion";
mkdirSync(out, { recursive: true });
const browser = await chromium.launch({ channel: "chrome", headless: true });
try {
  for (const [width, height] of [[1440, 900], [390, 844], [844, 390]]) {
    const page = await browser.newPage({ viewport: { width, height }, reducedMotion: "no-preference" });
    const errors = []; page.on("pageerror", (e) => errors.push(e.message));
    await page.goto(`${process.env.FIRELINE_BASE || "http://127.0.0.1:8790"}/web/demo/`);
    await page.waitForFunction(() => window.fireline);
    const click = async (id) => {
      await page.locator(`[data-id="${id}"]`).evaluate((el) => el.click());
      await page.waitForTimeout(50);
    };
    await click("continue"); await click("guide-skip");
    await page.waitForFunction(() => !window.fireline.snapshot().evaluating);
    await click("hint"); await page.waitForFunction(() => !window.fireline.coach().busy);
    await page.waitForTimeout(800);
    await click("coach-next");
    assert.equal(await page.evaluate(() => window.fireline.coach().page), 0, "First click completes the line");
    await click("coach-next");
    assert.equal(await page.evaluate(() => window.fireline.coach().page), 1);
    assert.equal(await page.locator('[data-id="coach-solve"]').count(), 0);
    while (await page.evaluate(() => window.fireline.coach().depth) < 4) {
      await click("coach-next"); await click("coach-next");
    }
    await click("coach-solve");
    await page.waitForFunction(() => window.fireline.coach().cursor?.startsWith("signal-"));
    await page.waitForTimeout(120);
    assert.equal(await page.evaluate(() => window.fireline.coach().targetVisible), true);
    await page.screenshot({ path: `${out}/cursor-${width}.png` });
    await click("coach-close");
    const stopped = await page.evaluate(() => window.fireline.snapshot());
    await page.waitForTimeout(600);
    assert.deepEqual(await page.evaluate(() => window.fireline.snapshot().features), stopped.features);
    assert.equal(await page.evaluate(() => window.fireline.snapshot().coaching), false);
    await click("hint"); await page.waitForFunction(() => !window.fireline.coach().busy);
    assert.ok(await page.evaluate(() => window.fireline.coach().depth >= 4));
    await click("coach-solve");
    await page.waitForFunction(() => window.fireline.coach().cursor === "epsilon-up");
    await page.waitForTimeout(100);
    assert.equal(await page.evaluate(() => window.fireline.coach().targetVisible), true);
    await page.screenshot({ path: `${out}/tuning-${width}.png` });
    await page.waitForFunction(() => window.fireline.coach().complete);
    await click("coach-close");
    await click("hint"); await page.waitForFunction(() => window.fireline.coach().complete);
    assert.equal(await page.locator('[data-id="coach-solve"]').count(), 0, "Completed contracts stay locked");
    assert.deepEqual(errors, []);
    await page.close();
    console.log(`${width}×${height}: animated cursor, cancel, sequential hints and completed lock pass.`);
  }
} finally { await browser.close(); }

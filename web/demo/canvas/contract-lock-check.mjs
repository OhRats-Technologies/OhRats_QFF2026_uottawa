import assert from "node:assert/strict";
import { createRequire } from "node:module";
const require = createRequire(import.meta.url),
  { chromium } = require(`${process.env.RUNTIME_NODE_MODULES}/playwright`);
const browser = await chromium.launch({ channel: "chrome", headless: true });
try {
  for (const width of [1440, 390]) {
    const page = await browser.newPage({ viewport: { width, height: 900 }, reducedMotion: "reduce" });
    const errors = [];
    page.on("pageerror", (e) => errors.push(e.message));
    const click = async (id) => {
      await page.locator(`[data-id="${id}"]`).evaluate((el) => el.click());
      await page.waitForTimeout(80);
    };
    const settled = (attempts) => page.waitForFunction((n) =>
      window.fireline.snapshot().attempts === n && !window.fireline.snapshot().evaluating, attempts);
    await page.goto(`${process.env.FIRELINE_BASE || "http://127.0.0.1:8790"}/web/demo/`);
    await page.waitForFunction(() => window.fireline);
    await click("continue"); await click("guide-skip"); await settled(1);
    await click("signal-0");
    while (!(await page.evaluate(() => window.fireline.controls().some((h) => h.id === "signal-5"))))
      await click("rack-page");
    await click("signal-5"); await settled(2);
    const won = await page.evaluate(() => window.fireline.snapshot());
    assert.ok(await page.locator('[data-id="next"]').isEnabled());
    for (const id of ["signal-0", "width-2", "foundry", "undo"])
      assert.ok(await page.locator(`[data-id="${id}"]`).isDisabled(), id);
    await click("signal-0"); await click("undo");
    assert.deepEqual(await page.evaluate(() => window.fireline.snapshot().features), won.features);
    if (width < 920) await click("tab-kernel");
    for (const id of ["angle-up", "strength-up", "epsilon-up"])
      assert.ok(await page.locator(`[data-id="${id}"]`).isDisabled(), id);
    await click("angle-up");
    assert.equal(await page.evaluate(() => window.fireline.snapshot().angle), won.angle);
    await page.reload(); await page.waitForFunction(() => window.fireline); await click("continue");
    assert.ok(await page.locator('[data-id="angle-up"]').isDisabled());
    await click("next"); await settled(3);
    assert.equal(await page.evaluate(() => window.fireline.snapshot().round), 1);
    assert.ok(await page.locator('[data-id="angle-up"]').isEnabled());
    assert.deepEqual(errors, []);
    await page.close();
    console.log(`${width}px: winning choices locked, reload preserved, next season unlocked.`);
  }
} finally { await browser.close(); }

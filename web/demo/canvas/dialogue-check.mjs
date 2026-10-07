import assert from "node:assert/strict";
import { createRequire } from "node:module";
import { mkdirSync, writeFileSync } from "node:fs";
const require = createRequire(import.meta.url),
  { chromium } = require(`${process.env.RUNTIME_NODE_MODULES}/playwright`),
  out = process.env.FIRELINE_OUTPUT || ".cache/fireline-dialogue-voice";
mkdirSync(out, { recursive: true });
const browser = await chromium.launch({ channel: "chrome", headless: true });
try {
  const page = await browser.newPage({ viewport: { width: 900, height: 700 } });
  const errors = [];
  page.on("pageerror", (e) => errors.push(e.message));
  await page.addInitScript(() => {
    window.bettyTones = 0;
    const original = AudioContext.prototype.createOscillator;
    AudioContext.prototype.createOscillator = function () {
      const oscillator = original.call(this), start = oscillator.start.bind(oscillator);
      oscillator.start = (...args) => { window.bettyTones++; start(...args); };
      return oscillator;
    };
  });
  await page.goto(`${process.env.FIRELINE_BASE || "http://127.0.0.1:8790"}/web/demo/`);
  await page.waitForFunction(() => window.fireline);
  const click = async (id) => {
    const hit = await page.evaluate((id) => window.fireline.controls().find((h) => h.id === id), id);
    await page.mouse.click(hit.x + hit.w / 2, hit.y + hit.h / 2);
    await page.waitForTimeout(50);
  };
  await click("menu-sound");
  await click("continue");
  await page.waitForTimeout(550);
  const first = await page.evaluate(() => window.fireline.tour());
  assert.ok(first.typing && first.visible.length > 0);
  await page.waitForTimeout(350);
  const later = await page.evaluate(() => window.fireline.tour());
  assert.ok(later.visible.length > first.visible.length);
  const tones = await page.evaluate(() => window.bettyTones);
  assert.ok(tones > 0 && tones < 15, `Bounded voice: ${tones}, ${JSON.stringify(await page.evaluate(() => window.fireline.audio()))}`);
  await click("guide-next");
  assert.equal(await page.evaluate(() => window.fireline.tour().typing), false);
  assert.equal(await page.evaluate(() => window.fireline.snapshot().guidePage), 0);
  await click("guide-dialogue");
  assert.equal(await page.evaluate(() => window.fireline.snapshot().guidePage), 1);
  await page.waitForFunction(() => window.fireline.tour()?.typing === false, null, { timeout: 8000 });
  const final = await page.evaluate(() => window.fireline.tour());
  assert.equal(final.visible, final.text, "Natural typing finishes");
  const a = final.target, b = final.bubble;
  assert.ok(a.x + a.w <= b.x || b.x + b.w <= a.x ||
    a.y + a.h <= b.y || b.y + b.h <= a.y, "Bubble leaves map exposed");
  await page.screenshot({ path: `${out}/betty-dialogue.png` });
  await click("guide-skip");
  await click("sound");
  await click("help");
  await click("guide-tour");
  const muted = await page.evaluate(() => window.bettyTones);
  await page.waitForTimeout(900);
  assert.equal(await page.evaluate(() => window.bettyTones), muted);
  assert.deepEqual(errors, []);
  writeFileSync(`${out}/receipt.json`, JSON.stringify({
    progressiveText: true, clickCompletesBeforeAdvance: true,
    bubbleClickAdvances: true, naturallyCompletes: true,
    synthesizedChirps: tones, muteStopsChirps: true, errors,
  }, null, 2) + "\n");
  console.log("Betty text, click progression, synthesis and mute checks passed.");
} finally { await browser.close(); }

import assert from "node:assert/strict";
import { createRequire } from "node:module";
import { readFileSync, mkdirSync, writeFileSync } from "node:fs";
import { fresh, build, record, assessment } from "./session.js";
import { run } from "./engine.js";
import { FULL_HELP_DEPTH } from "./coach-copy.js";
const require = createRequire(import.meta.url),
  { chromium } = require(`${process.env.RUNTIME_NODE_MODULES}/playwright`),
  data = JSON.parse(readFileSync(new URL("./data.json", import.meta.url))),
  out = process.env.FIRELINE_OUTPUT || ".cache/fireline-coach",
  base = process.env.FIRELINE_BASE || "http://127.0.0.1:8790";
mkdirSync(out, { recursive: true });
const browser = await chromium.launch({ channel: "chrome", headless: true }), receipts = [];
async function open(width, height, state, motion = "reduce") {
  const page = await browser.newPage({ viewport: { width, height }, reducedMotion: motion });
  page.errors = [];
  page.on("pageerror", (e) => page.errors.push(e.message));
  page.on("request", (r) => { if (!r.url().startsWith(base)) page.errors.push(`External request: ${r.url()}`); });
  if (state) await page.addInitScript((s) => localStorage.setItem("fireline-canvas-v2", JSON.stringify(s)), state);
  await page.goto(`${base}/web/demo/`); await page.waitForFunction(() => window.fireline);
  await click(page, "continue");
  if (await page.evaluate(() => window.fireline.snapshot().guideIntro)) await click(page, "guide-skip");
  return page;
}
async function click(page, id) {
  await page.locator(`[data-id="${id}"]`).evaluate((el) => el.click());
  await page.waitForTimeout(45);
}
const ready = (page) => page.waitForFunction(() => window.fireline.coach().open &&
  !window.fireline.coach().busy && !window.fireline.coach().solving && !window.fireline.coach().waiting);
const settled = (page) => page.waitForFunction(() => !window.fireline.snapshot().evaluating &&
  !window.fireline.transition().active);
async function revealHelp(page) {
  while (await page.evaluate(() => window.fireline.coach().depth) < FULL_HELP_DEPTH) {
    assert.equal(await page.locator('[data-id="coach-solve"]').count(), 0, "Early hints never offer the whole solution");
    const text = await page.evaluate(() => window.fireline.coach().text);
    assert.ok(text.split(/\s+/).length >= 10 && text.split(/\s+/).length <= 25);
    await click(page, "coach-next");
  }
  assert.equal(await page.locator('[data-id="coach-solve"]').count(), 1);
}
async function useHint(page, screenshot) {
  await click(page, "hint"); await ready(page);
  const plan = await page.evaluate(() => window.fireline.coach());
  assert.ok(plan.recommendation);
  assert.equal(plan.depth, 0, "Every season starts with a gentle first hint");
  const first = await page.evaluate(() => window.fireline.snapshot().starts);
  const before = await page.evaluate(() => window.fireline.snapshot());
  await click(page, "coach-next");
  await page.screenshot({ path: `${out}/nudge-${screenshot}.png` });
  await revealHelp(page);
  assert.deepEqual(build(await page.evaluate(() => window.fireline.snapshot())), build(before),
    "Hints never silently apply the answer");
  assert.equal(await page.evaluate(() => window.fireline.coach().page), FULL_HELP_DEPTH);
  await page.screenshot({ path: `${out}/${screenshot}.png` });
  await click(page, "coach-solve");
  await page.waitForFunction(() => window.fireline.coach().complete === true, null, { timeout: 15000 });
  const s = await page.evaluate(() => window.fireline.snapshot());
  assert.deepEqual(build(s), plan.recommendation.build);
  assert.deepEqual(s.starts, first, "Advisor trials never alter the first-run contract");
  assert.ok(assessment(s).won);
  await click(page, "coach-close");
  assert.ok(await page.locator('[data-id="next"]').isEnabled());
  assert.deepEqual(page.errors, []);
  return { round: s.round, checked: plan.checked, mae: s.result.mae, inputs: s.features, won: true };
}
try {
  for (const [width, height] of [[1440, 900], [390, 844]]) {
    const page = await open(width, height); await settled(page);
    for (let round = 0; round < 4; round++) {
      const r = await useHint(page, `hint-${width}-season-${round + 1}`);
      receipts.push({ width, ...r });
      await click(page, "next"); await settled(page);
    }
    assert.equal(await page.evaluate(() => window.fireline.snapshot().celebrate), true);
    await page.close();
  }
  for (let round = 0; round < 4; round++) {
    const s = fresh(); s.round = round; s.onboarded = true;
    record(s, run(data, build(s), round));
    const available = data.rounds[round].available || data.features.map((_, i) => i);
    Object.assign(s, { features: round % 2 ? [] : available.slice(0, 10), width: round % 2 ? 4 : 10,
      angle: Math.PI / 2, C: 10, epsilon: 0.5 });
    const page = await open(844, 390, s);
    const r = await useHint(page, `arbitrary-season-${round + 1}`);
    receipts.push({ width: 844, arbitrary: true, ...r }); await page.close();
  }
  const empty = fresh(); empty.onboarded = true; empty.features = [];
  const initial = await open(390, 844, empty);
  await click(initial, "hint"); await ready(initial);
  assert.equal(await initial.evaluate(() => window.fireline.coach().baseline), true);
  await revealHelp(initial);
  await click(initial, "coach-solve");
  await initial.waitForFunction(() => window.fireline.coach().complete, null, { timeout: 15000 });
  assert.equal(await initial.evaluate(() => window.fireline.snapshot().attempts), 2,
    "Betty establishes a real baseline then solves against it");
  assert.deepEqual(initial.errors, []); await initial.close();
  const page = await open(1280, 640); await settled(page);
  for (let i = 0; i < 7; i++) await click(page, i % 2 ? "width-10" : "width-6");
  await ready(page);
  assert.ok(await page.evaluate(() => window.fireline.coach().recommendation));
  await click(page, "coach-close");
  await page.waitForTimeout(1200);
  assert.equal(await page.evaluate(() => window.fireline.coach().open), false, "Spam offer does not nag repeatedly");
  await click(page, "foundry"); await click(page, "hint"); await ready(page);
  assert.ok(await page.evaluate(() => window.fireline.coach().winner));
  assert.equal(await page.evaluate(() => window.fireline.coach().depth), 1, "Reopening asks for the next hint");
  await page.keyboard.press("Escape");
  assert.equal(await page.evaluate(() => window.fireline.coach().open), false, "Escape dismisses help");
  await page.reload(); await page.waitForFunction(() => window.fireline);
  await click(page, "continue"); await click(page, "hint"); await ready(page);
  assert.equal(await page.evaluate(() => window.fireline.coach().depth), 2, "Hint progress survives reload");
  assert.equal(await page.locator('[data-id="coach-solve"]').count(), 0);
  assert.deepEqual(page.errors, []); await page.close();
  writeFileSync(`${out}/receipt.json`, JSON.stringify({ receipts, rapidClickOffer: true,
    foundryHint: true, contractPreserved: true, gradualHints: true, savedHintProgress: true,
    fullHelpAfterRequests: FULL_HELP_DEPTH + 1, noExternalRequests: true }, null, 2) + "\n");
  console.log(JSON.stringify(receipts));
} finally { await browser.close(); }

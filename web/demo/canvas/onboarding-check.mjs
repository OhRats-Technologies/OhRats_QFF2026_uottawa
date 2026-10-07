import { createRequire } from "node:module";
import { mkdirSync, writeFileSync } from "node:fs";
import assert from "node:assert/strict";
const require = createRequire(import.meta.url),
  { chromium } = require(`${process.env.RUNTIME_NODE_MODULES}/playwright`);
const out = process.env.FIRELINE_OUTPUT || ".cache/fireline-onboarding";
mkdirSync(out, { recursive: true });
const browser = await chromium.launch({ channel: "chrome", headless: true }),
  checks = [];
for (const [width, height] of [
  [1440, 900],
  [1280, 640],
  [390, 844],
  [320, 568],
  [844, 390],
]) {
  const context = await browser.newContext({
    viewport: { width, height },
    reducedMotion: "reduce",
    hasTouch: width < 500,
  });
  const page = await context.newPage(),
    errors = [];
  page.on("pageerror", (e) => errors.push(e.message));
  await page.goto(
    `${process.env.FIRELINE_BASE || "http://127.0.0.1:8790"}/web/demo/`,
  );
  await page.waitForFunction(() => window.fireline);
  const click = async (id) => {
    await page.waitForFunction(
      (id) =>
        window.fireline.controls().some((h) => h.id === id && !h.disabled),
      id,
    );
    const h = await page.evaluate(
      (id) => window.fireline.controls().find((h) => h.id === id),
      id,
    );
    const scale = width / Math.max(390, width);
    if (width < 500)
      await page.touchscreen.tap(
        (h.x + h.w / 2) * scale,
        (h.y + h.h / 2) * scale,
      );
    else
      await page.mouse.click((h.x + h.w / 2) * scale, (h.y + h.h / 2) * scale);
    await page.waitForTimeout(40);
  };
  await click("continue");
  assert.equal(
    await page.evaluate(() => window.fireline.snapshot().guideIntro),
    true,
  );
  const initial = await page.evaluate(() => window.fireline.snapshot());
  for (let step = 0; step < 8; step++) {
    assert.equal(
      await page.evaluate(() => window.fireline.snapshot().guideStep),
      step,
    );
    const hits = await page.evaluate(() => window.fireline.controls());
    assert.ok(
      hits.every((h) => h.id.startsWith("guide-")),
      "Workbench must not remain active under onboarding",
    );
    const H = height / (width / Math.max(390, width)),
      W = Math.max(390, width);
    assert.ok(
      hits.every(
        (h) => h.x >= 0 && h.y >= 0 && h.x + h.w <= W + 1 && h.y + h.h <= H + 1,
      ),
    );
    const tour = await page.evaluate(() => window.fireline.tour());
    assert.ok(tour.target.w > 0 && tour.target.h > 0);
    assert.ok(
      tour.bubble.w * tour.bubble.h < W * H * 0.42,
      "Tour must remain compact",
    );
    const overlap =
      Math.max(
        0,
        Math.min(tour.target.x + tour.target.w, tour.bubble.x + tour.bubble.w) -
          Math.max(tour.target.x, tour.bubble.x),
      ) *
      Math.max(
        0,
        Math.min(tour.target.y + tour.target.h, tour.bubble.y + tour.bubble.h) -
          Math.max(tour.target.y, tour.bubble.y),
      );
    assert.equal(
      overlap,
      0,
      `Dialogue ${width} step ${step}: ${JSON.stringify(tour)}`,
    );
    // Clicking the highlighted real UI is inert until the briefing finishes.
    await page.mouse.click(
      (tour.target.x + tour.target.w / 2) * (width / W),
      (tour.target.y + tour.target.h / 2) * (width / W),
    );
    assert.equal(
      await page.evaluate(() => window.fireline.snapshot().attempts),
      0,
    );
    await page.screenshot({ path: `${out}/lesson-${width}-${step}.png` });
    if (step < 7) await click("guide-next");
  }
  const before = await page.evaluate(() => window.fireline.snapshot());
  for (const key of [
    "features",
    "width",
    "round",
    "sample",
    "C",
    "epsilon",
    "angle",
    "attempts",
    "history",
  ])
    assert.deepEqual(before[key], initial[key]);
  await click("guide-next");
  assert.equal(
    await page.evaluate(() => window.fireline.snapshot().onboarded),
    true,
  );
  await click("help");
  await click("guide-topic-6");
  assert.ok(
    (await page.locator("#status").textContent()).includes(
      "Sample-based Quantum Diagonalization",
    ),
  );
  await page.screenshot({ path: `${out}/guide-sqd-${width}.png` });
  await click("guide-topic-5");
  await page.screenshot({ path: `${out}/guide-qaoa-${width}.png` });
  await page.locator('[data-id="guide-topic-3"]').focus();
  await page.keyboard.press("Enter");
  assert.equal(
    await page.evaluate(() => window.fireline.snapshot().guideStep),
    3,
  );
  await page.keyboard.press("Escape");
  assert.equal(
    await page.evaluate(() => window.fireline.snapshot().help),
    false,
  );
  await click("help");
  await click("guide-tour");
  assert.equal(
    await page.evaluate(() => window.fireline.snapshot().guideIntro),
    true,
  );
  await click("guide-skip");
  assert.deepEqual(
    await page.evaluate(() => window.fireline.snapshot().features),
    initial.features,
  );
  await page.reload();
  await page.waitForFunction(() => window.fireline);
  await click("continue");
  assert.equal(
    await page.evaluate(() => window.fireline.snapshot().help),
    false,
  );
  await click("menu");
  await click("new");
  assert.equal(
    await page.evaluate(() => window.fireline.snapshot().guideIntro),
    true,
  );
  await page.keyboard.press("Escape");
  assert.equal(
    await page.evaluate(() => window.fireline.snapshot().menu),
    true,
  );
  await click("continue");
  await click("guide-skip");
  assert.equal(
    await page.evaluate(() => window.fireline.snapshot().help),
    false,
  );
  assert.equal(errors.length, 0);
  checks.push({
    width,
    height,
    lessons: 8,
    automaticStart: true,
    isolatedDemo: true,
    realUIHighlights: true,
    compactUnobstructedBubble: true,
    guideTabs: true,
    keyboard: true,
    newRun: true,
    resume: true,
    touch: width < 500,
    errors,
  });
  await context.close();
}
await browser.close();
writeFileSync(
  `${out}/receipt.json`,
  JSON.stringify({ status: "passed", checks }, null, 2) + "\n",
);
console.log(JSON.stringify(checks));

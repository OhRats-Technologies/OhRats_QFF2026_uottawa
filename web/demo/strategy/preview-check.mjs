// What-if projections must agree with accepted clicks without saving preview moves.
import fs from "node:fs/promises";
import assert from "node:assert/strict";
import { createRequire } from "node:module";
import { createRun } from "./rules.js";
import { responsePreview, previewText } from "./preview.js";

const source = JSON.parse(
  await fs.readFile("web/demo/assets/context/scenario.json", "utf8"),
);
const fixture = createRun(2, source.pool);
const original = JSON.stringify(fixture);
for (const kind of [null, "crew", "water", "unknown"])
  responsePreview(fixture, kind);
assert.equal(JSON.stringify(fixture), original);
const blocked = structuredClone(fixture);
blocked.upgradePending = true;
assert.equal(responsePreview(blocked), null);
blocked.upgradePending = false;
blocked.status = "lost";
assert.equal(responsePreview(blocked), null);
const endangered = structuredClone(fixture);
endangered.damage = 59;
endangered.integrity = 41;
assert.equal(responsePreview(endangered).status, "lost");
assert.match(previewText(responsePreview(endangered)), /line breaks/);

const require = createRequire(
  `${process.env.RUNTIME_NODE_MODULES}/../package.json`,
);
const { chromium } = require("playwright");
const output = ".cache/judge-submission/strategy-preview";
await fs.mkdir(output, { recursive: true });
const browser = await chromium.launch({ headless: true, channel: "chrome" });
const page = await browser.newPage({
  viewport: { width: 1280, height: 720 },
  reducedMotion: "reduce",
});
const errors = [];
page.on("pageerror", (error) => errors.push(error.message));
const comparisons = [];
for (const kind of [null, "crew", "water"]) {
  await page.goto(
    `http://127.0.0.1:8790/web/demo/?qa=preview-${kind}#season=2`,
    { waitUntil: "domcontentloaded" },
  );
  await page.locator("#start").click();
  const before = await page.evaluate(() =>
    localStorage.getItem("fireline-season"),
  );
  const button = page.locator(kind ? `[data-action="${kind}"]` : "#advance");
  const expected = responsePreview(fixture, kind);
  await button.hover();
  assert.equal(
    await page.locator("#action-feedback").textContent(),
    previewText(expected),
  );
  await button.focus();
  assert.equal(
    await button.getAttribute("aria-describedby"),
    "action-feedback",
  );
  assert.equal(
    await page.locator("#action-feedback").textContent(),
    previewText(expected),
  );
  assert.equal(
    await page.evaluate(() => localStorage.getItem("fireline-season")),
    before,
  );
  if (kind) await button.click();
  await page.locator("#advance").click();
  assert.equal(
    await page.locator("#integrity").textContent(),
    String(Math.round(expected.reserve)),
  );
  assert.equal(
    await page.locator("#supplies").textContent(),
    String(expected.supplies),
  );
  const saved = JSON.parse(
    await page.evaluate(() => localStorage.getItem("fireline-season")),
  );
  assert.equal(saved.moves.length, kind ? 2 : 1);
  comparisons.push({
    kind: kind ?? "advance",
    expected,
    acceptedMoves: saved.moves.length,
  });
}

const layouts = [];
for (const [width, height] of [
  [1280, 720],
  [1024, 768],
  [390, 844],
]) {
  await page.setViewportSize({ width, height });
  await page.goto(
    `http://127.0.0.1:8790/web/demo/?qa=preview-layout-${width}#season=2`,
    { waitUntil: "domcontentloaded" },
  );
  await page.locator("#start").click();
  await page.locator('[data-action="crew"]').focus();
  await page.locator('[data-action="water"]').press("ArrowLeft");
  assert.match(
    await page.locator("#action-feedback").textContent(),
    /After this front/,
  );
  const layout = await page.evaluate(() => {
    const operations = document.querySelector(".operations");
    const feedback = document.querySelector("#action-feedback");
    const button = document.querySelector('[data-action="water"]');
    const outline = getComputedStyle(button);
    const ring =
      parseFloat(outline.outlineWidth) + parseFloat(outline.outlineOffset);
    return {
      horizontalOverflow: document.documentElement.scrollWidth > innerWidth + 1,
      feedbackOverflow: feedback.scrollWidth > feedback.clientWidth + 1,
      operationsScroll: operations.scrollHeight - operations.clientHeight,
      focusRingUnclipped:
        button.getBoundingClientRect().right + ring <=
        (getComputedStyle(operations).overflowX === "visible"
          ? innerWidth
          : operations.getBoundingClientRect().right) + 1,
    };
  });
  assert.equal(layout.horizontalOverflow, false);
  assert.equal(layout.feedbackOverflow, false);
  assert.equal(layout.focusRingUnclipped, true);
  if (width > 760) {
    assert.ok(layout.operationsScroll <= 1);
  }
  await page.screenshot({
    path: `${output}/${width}-${height}.png`,
    fullPage: width < 760,
  });
  layouts.push({ width, height, ...layout });
}
assert.deepEqual(errors, []);
await browser.close();
await fs.writeFile(
  `${output}/receipt.json`,
  JSON.stringify(
    {
      comparisons,
      layouts,
      errors,
      stateAndSaveImmutability: true,
      blockedAndTerminalFixtures: true,
      lossWarning: true,
      scope:
        "One-front toy-rule projection agrees with subsequent control clicks; no scientific prediction or policy-quality claim.",
    },
    null,
    2,
  ) + "\n",
);
console.log(JSON.stringify({ comparisons, layouts, errors }));

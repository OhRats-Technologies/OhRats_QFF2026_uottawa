// Focused authoring QA: forced no-GPU/storage/fonts and render scheduling branches.
import fs from "node:fs/promises";
import assert from "node:assert/strict";
import { createRequire } from "node:module";
import { createRun } from "./rules.js";

const require = createRequire(
  `${process.env.RUNTIME_NODE_MODULES}/../package.json`,
);
const { chromium } = require("playwright");
const output = ".cache/judge-submission/strategy-render";
await fs.mkdir(output, { recursive: true });
const source = JSON.parse(
  await fs.readFile("web/demo/assets/context/scenario.json", "utf8"),
);
const browser = await chromium.launch({ headless: true, channel: "chrome" });
const cases = [];
for (const noGPU of [true, false]) {
  const page = await browser.newPage({
    viewport: { width: 1280, height: 720 },
    reducedMotion: "reduce",
  });
  const errors = [],
    requests = [];
  page.on("pageerror", (error) => errors.push(error.message));
  page.on("request", (request) => requests.push(request.method()));
  await page.route(/fonts\.(googleapis|gstatic)\.com/, (route) =>
    route.abort(),
  );
  await page.addInitScript((noGPU) => {
    window.__mapFrames = 0;
    window.__qaHidden = false;
    Object.defineProperty(document, "hidden", { get: () => window.__qaHidden });
    Object.defineProperty(window, "localStorage", {
      get: () => {
        throw new DOMException("Storage disabled");
      },
    });
    const clear = CanvasRenderingContext2D.prototype.clearRect;
    CanvasRenderingContext2D.prototype.clearRect = function (...args) {
      if (this.canvas.id === "map-effects") window.__mapFrames++;
      return clear.apply(this, args);
    };
    if (noGPU) {
      const original = HTMLCanvasElement.prototype.getContext;
      HTMLCanvasElement.prototype.getContext = function (type, ...args) {
        return type.startsWith("webgl")
          ? null
          : original.call(this, type, ...args);
      };
    }
  }, noGPU);
  await page.goto("http://127.0.0.1:8790/web/demo/#season=2", {
    waitUntil: "domcontentloaded",
  });
  await page.locator("#start").click();
  assert.equal(await page.locator("#sphere svg").count(), Number(noGPU));
  assert.equal(await page.locator("#sphere canvas").count(), Number(!noGPU));
  await page.waitForTimeout(150);
  const staticStart = await page.evaluate(() => window.__mapFrames);
  await page.waitForTimeout(200);
  assert.equal(await page.evaluate(() => window.__mapFrames), staticStart);

  if (noGPU) {
    const state = createRun(2, source.pool),
      fire = state.incidents.find((f) => f.id === state.selected);
    const theta = Math.PI * (0.15 + 0.7 * Math.tanh(fire.size / 2));
    const phi = fire.x * Math.PI * 2;
    const expected = [
      Math.sin(theta) * Math.cos(phi),
      Math.sin(theta) * Math.sin(phi),
      Math.cos(theta),
    ];
    const actual = JSON.parse(
      await page.locator("#sphere").getAttribute("data-vector"),
    );
    assert.ok(
      actual.every((value, i) => Math.abs(value - expected[i]) < 1e-12),
    );
    await page.locator("#lens-toggle").click();
    await page.locator("#damping").press("End");
    await page.waitForTimeout(60);
    assert.deepEqual(
      JSON.parse(await page.locator("#sphere").getAttribute("data-vector")),
      [0, 0, 1],
    );
    assert.equal(await page.locator("#fallback-tip").getAttribute("cy"), "30");
    assert.match(
      await page.locator("#fallback-description").textContent(),
      /Probability of zero 1.000/,
    );
    await page.locator("#lens-toggle").click();
  }
  await page.locator('[data-action="water"]').click();
  assert.equal(await page.locator("#supplies").textContent(), "14");
  await page.locator("#advance").click();
  assert.equal(await page.locator("#front-number").textContent(), "2 / 12");
  await page.waitForTimeout(150);
  assert.ok((await page.evaluate(() => window.__mapFrames)) > staticStart);
  const responseFrames = await page.evaluate(() => window.__mapFrames);
  await page.waitForTimeout(200);
  assert.equal(await page.evaluate(() => window.__mapFrames), responseFrames);

  await page.emulateMedia({ reducedMotion: "no-preference" });
  await page.waitForTimeout(120);
  const liveStart = await page.evaluate(() => window.__mapFrames);
  await page.waitForTimeout(150);
  assert.ok((await page.evaluate(() => window.__mapFrames)) > liveStart);
  await page.evaluate(() => {
    window.__qaHidden = true;
    document.dispatchEvent(new Event("visibilitychange"));
  });
  const hiddenStart = await page.evaluate(() => window.__mapFrames);
  await page.waitForTimeout(250);
  assert.equal(await page.evaluate(() => window.__mapFrames), hiddenStart);
  await page.evaluate(() => {
    window.__qaHidden = false;
    document.dispatchEvent(new Event("visibilitychange"));
  });
  await page.waitForTimeout(120);
  assert.ok((await page.evaluate(() => window.__mapFrames)) > hiddenStart);
  await page.emulateMedia({ reducedMotion: "reduce" });
  await page.waitForTimeout(150);
  await page.screenshot({
    path: `${output}/${noGPU ? "svg-fallback" : "webgl"}.png`,
  });
  assert.deepEqual(errors, []);
  assert.ok(requests.every((method) => method === "GET"));
  const geometry = await page.evaluate(() => ({
    overflow: document.documentElement.scrollWidth > innerWidth,
    operationsScroll:
      document.querySelector(".operations").scrollHeight -
      document.querySelector(".operations").clientHeight,
  }));
  assert.equal(geometry.overflow, false);
  assert.ok(geometry.operationsScroll <= 1);
  cases.push({
    noGPU,
    fontsBlocked: true,
    storageBlocked: true,
    reducedMotionStatic: true,
    liveEmbers: true,
    forcedVisibilityBranchStopsAndResumes: true,
    responseAndAdvanceWork: true,
    fallbackChannelChecked: noGPU,
    ...geometry,
    errors,
  });
  await page.close();
}
await browser.close();
await fs.writeFile(
  `${output}/receipt.json`,
  JSON.stringify(
    {
      cases,
      scope:
        "Forced browser failure and visibility branches; not physical GPU loss or operating-system tab scheduling.",
    },
    null,
    2,
  ) + "\n",
);
console.log(JSON.stringify(cases));

// Focused authoring QA for laptop-height operations, using visible controls.
import fs from "node:fs/promises";
import assert from "node:assert/strict";
import { createRequire } from "node:module";
import { createHash } from "node:crypto";
import { execFileSync } from "node:child_process";

const require = createRequire(
  `${process.env.RUNTIME_NODE_MODULES}/../package.json`,
);
const { chromium } = require("playwright");
const output = ".cache/judge-submission/strategy-compact";
await fs.mkdir(output, { recursive: true });
const browser = await chromium.launch({ headless: true, channel: "chrome" });
const page = await browser.newPage();
const errors = [];
page.on("pageerror", (error) => errors.push(error.message));
const baselineCommit = "4735884";
const compactPath = "web/demo/strategy/styles/compact.css";
const oldStyle = execFileSync("git", ["show", `${baselineCommit}:${compactPath}`]);
const baseline = await browser.newPage({ viewport: { width: 1024, height: 600 } });
await baseline.route("**/strategy/styles/compact.css", route => route.fulfill({ body: oldStyle, contentType: "text/css" }));
await baseline.goto("http://127.0.0.1:8790/web/demo/?qa=compact-before");
await baseline.locator("#start").click();
const before = await baseline.locator("#advance").evaluate(element => ({ bottom: element.getBoundingClientRect().bottom, height: innerHeight }));
assert.ok(before.bottom > before.height, "Pinned old command bar should be clipped");
await baseline.screenshot({ path: `${output}/before-1024-600.png` });
await baseline.close();
const views = [];
for (const [width, height] of [
  [1024, 600],
  [1280, 600],
  [1280, 720],
  [1024, 768],
  [1440, 820],
]) {
  await page.setViewportSize({ width, height });
  await page.goto(`http://127.0.0.1:8790/web/demo/?qa=compact-${width}`, {
    waitUntil: "domcontentloaded",
  });
  await page.locator("#start").click();
  const bounds = await page.evaluate(() => {
    const operations = document.querySelector(".operations");
    const visible = ["#sphere", "#matrix", "#lab-open", "#advance"].every(
      (selector) => {
        const box = document.querySelector(selector).getBoundingClientRect();
        return (
          box.left >= 0 &&
          box.top >= 0 &&
          box.right <= innerWidth &&
          box.bottom <= innerHeight
        );
      },
    );
    return {
      visible,
      scroll: operations.scrollHeight - operations.clientHeight,
      horizontalOverflow: document.documentElement.scrollWidth > innerWidth + 1,
    };
  });
  assert.equal(bounds.visible, true);
  assert.equal(bounds.horizontalOverflow, false);
  assert.ok(
    bounds.scroll <= 1,
    `Operations require scrolling at ${width}×${height}`,
  );
  await page.locator("#sample").click();
  await page.locator("#sample").click();
  const matrixLayout = await page.evaluate(() => {
    const matrix = document.querySelector("#matrix").getBoundingClientRect();
    const readout = document.querySelector(".matrix-readout").getBoundingClientRect();
    const cells = [...document.querySelectorAll("#matrix .projected-cell")];
    return {
      cellsContained: cells.every((cell) => {
        const box = cell.getBoundingClientRect();
        return box.left >= matrix.left - 1 && box.right <= matrix.right + 1;
      }),
      separated: readout.left >= matrix.right,
      densePreview: document.querySelector("#matrix").classList.contains("dense-preview"),
      cells: cells.length,
    };
  });
  assert.equal(matrixLayout.cellsContained, true);
  assert.equal(matrixLayout.separated, true);
  assert.equal(matrixLayout.densePreview, true);
  await page.locator("#matrix-mode").click();
  assert.match(
    await page.locator("#matrix").getAttribute("aria-label"),
    /Hamiltonian/,
  );
  assert.equal(
    await page.locator("#bench-dialog").evaluate((dialog) => dialog.open),
    true,
  );
  await page.locator("#bench-close").click();
  await page.locator("#lab-open").click();
  assert.equal(
    await page.locator("#instrument-dialog").evaluate((dialog) => dialog.open),
    true,
  );
  await page.locator("#instrument-close").click();
  await page.screenshot({ path: `${output}/${width}-${height}.png` });
  views.push({ width, height, ...bounds, matrixLayout });
}
assert.deepEqual(errors, []);
const sources = [compactPath, "web/demo/strategy/styles/base.css", "web/demo/strategy/styles/responsive.css",
  "web/demo/index.html", "web/demo/assets/strategy.js", "web/demo/strategy/compact-check.mjs"];
const sha = bytes => createHash("sha256").update(bytes).digest("hex");
const source_sha256 = Object.fromEntries(await Promise.all(sources.map(async path => [path, sha(await fs.readFile(path))])));
await fs.writeFile(
  `${output}/receipt.json`,
  JSON.stringify({ checked_utc: new Date().toISOString(), status: "passed", source_sha256,
    baseline: { commit: baselineCommit, compact_css_sha256: sha(oldStyle), ...before }, views, errors,
    scope: "Pinned before-style clipping and current Chromium layout/control checks at five desktop sizes. Default instruments and command bar fit; expanded details may scroll. Narrow phone flow is separate. Not physical-device, human enjoyment or full platform certification." }, null, 2) + "\n",
);
console.log(JSON.stringify({ views, errors }));
await browser.close();

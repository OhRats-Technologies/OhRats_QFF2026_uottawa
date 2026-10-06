// Source and real-control inspection QA; no fitted predictor or quantum execution.
import fs from "node:fs/promises";
import assert from "node:assert/strict";
import { createRequire } from "node:module";
import { cost } from "./bench.js";

const require = createRequire(
  `${process.env.RUNTIME_NODE_MODULES}/../package.json`,
);
const { chromium } = require("playwright");
const data = JSON.parse(await fs.readFile("web/demo/data.json", "utf8"));
const objectives = [];
for (let a = 0; a < 7; a++)
  for (let b = a + 1; b < 8; b++)
    for (let c = b + 1; c < 9; c++)
      for (let d = c + 1; d < 10; d++)
        objectives.push(cost([a, b, c, d], data.record));
assert.equal(objectives.length, 210);
assert.ok(
  Math.abs(Math.min(...objectives) - data.record.exact_objective) < 1e-12,
);
const output = ".cache/judge-submission/bench-inspection";
await fs.mkdir(output, { recursive: true });
const browser = await chromium.launch({ headless: true, channel: "chrome" });
const page = await browser.newPage();
const errors = [],
  views = [];
page.on("pageerror", (error) => errors.push(error.message));
for (const [width, height] of [
  [1280, 720],
  [390, 844],
]) {
  await page.setViewportSize({ width, height });
  await page.goto(`http://127.0.0.1:8790/web/demo/?qa=bench-${width}`, {
    waitUntil: "domcontentloaded",
  });
  await page.locator("#start").click();
  const front = await page.locator("#front-number").textContent();
  await page.locator("#matrix").press("Space");
  assert.equal(
    await page.locator("#bench-dialog").evaluate((dialog) => dialog.open),
    true,
  );
  assert.equal(await page.locator("#front-number").textContent(), front);
  await page.locator("#bench-draw").click();
  assert.equal(await page.locator("#sample-count").textContent(), "5");
  const sqd = Number(await page.locator("#bench-sqd").textContent());
  assert.equal(
    sqd,
    Number(await page.locator("#bench-classical").textContent()),
  );
  assert.equal(
    Number(await page.locator("#bench-exact").textContent()),
    Number(data.record.exact_objective.toFixed(6)),
  );
  const bits = await page.locator(".bench-basis-row code").allTextContents();
  assert.equal(bits.length, 5);
  assert.ok(
    bits.every(
      (bit) =>
        /^[01]{10}$/.test(bit) &&
        [...bit].filter((value) => value === "1").length === 4,
    ),
  );
  const values = await page
    .locator("#bench-visual tbody tr")
    .evaluateAll((rows) =>
      rows.map((row) =>
        [...row.querySelectorAll("td")].map((cell) => Number(cell.textContent)),
      ),
    );
  assert.equal(values.length, 5);
  for (let a = 0; a < values.length; a++)
    for (let b = 0; b < values.length; b++) {
      if (a !== b) assert.equal(values[a][b], 0);
    }
  assert.ok(Math.abs(values[0][0] - sqd) <= 0.0005);
  await page.screenshot({ path: `${output}/hamiltonian-${width}.png` });
  await page.locator("#bench-redundancy").click();
  assert.equal(await page.locator("#bench-visual tbody tr").count(), 10);
  assert.equal(await page.locator(".bench-feature-key").count(), 10);
  await page.screenshot({ path: `${output}/redundancy-${width}.png` });
  const overflow = await page
    .locator("#bench-dialog")
    .evaluate((dialog) => dialog.scrollWidth > dialog.clientWidth + 1);
  assert.equal(overflow, false);
  await page.keyboard.press("Escape");
  assert.equal(
    await page.locator("#bench-dialog").evaluate((dialog) => dialog.open),
    false,
  );
  views.push({
    width,
    height,
    basis_states: bits.length,
    equal_sampled_minima: true,
    no_dialog_horizontal_overflow: true,
  });
}
assert.deepEqual(errors, []);
const result = {
  exhaustive_objective_values: objectives.length,
  views,
  errors,
  predictor_fits: 0,
  quantum_states: 0,
  hardware_jobs: 0,
};
await fs.writeFile(
  `${output}/receipt.json`,
  JSON.stringify(result, null, 2) + "\n",
);
console.log(JSON.stringify(result));
await browser.close();

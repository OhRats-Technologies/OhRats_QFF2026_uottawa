// Check displayed source semantics and actual legend controls, not tree density.
import assert from "node:assert/strict";
import fs from "node:fs/promises";
import { createHash } from "node:crypto";
import { execFileSync } from "node:child_process";
import { createRequire } from "node:module";
import { coverClasses } from "./cover-legend.js";

const hash = bytes => createHash("sha256").update(bytes).digest("hex");
const map = JSON.parse(await fs.readFile("web/presentation/assets/map.json", "utf8"));
const schema = await fs.readFile("docs/DATA_SCHEMA.md", "utf8");
const definition = schema.split("The inspected ZIP legend defines: ")[1].split(" Codes are categories")[0];
const sourceNames = Object.fromEntries([...definition.matchAll(/`(\d+)` ([^;]+?)(?:;|\. )/g)]
  .map(([, code, name]) => [code, name]));
const normal = text => text.toLowerCase().replace(/[\s/]/g, "");
assert.deepEqual(coverClasses.flatMap(row => row.codes).sort((a, b) => a - b),
  Object.keys(map.legend).map(Number).sort((a, b) => a - b));
for (const row of coverClasses) {
  for (const code of row.codes) assert.equal(row.color, map.legend[code]);
  if (row.codes.length === 1) assert.equal(normal(row.name), normal(sourceNames[row.codes[0]]));
  else assert.deepEqual(row.codes, [0, 255]);
}
const pinned = {};
for (const name of ["web/presentation/assets/map.json", "web/presentation/assets/ontario-cover.png",
  "web/demo/strategy/rules.js", "web/demo/strategy/scenario.js", "web/demo/strategy/session.js"]) {
  const bytes = await fs.readFile(name);
  assert.equal(hash(bytes), hash(execFileSync("git", ["show", `HEAD:${name}`])));
  pinned[name] = hash(bytes);
}
const require = createRequire(`${process.env.RUNTIME_NODE_MODULES}/../package.json`);
const { chromium } = require("playwright");
const browser = await chromium.launch({ headless: true, channel: "chrome", args: ["--mute-audio"] });
const out = ".cache/judge-submission/cover-legend";
await fs.mkdir(out, { recursive: true });
const results = [], errors = [];
try {
  const page = await browser.newPage({ reducedMotion: "reduce" });
  page.on("pageerror", error => errors.push(error.message));
  await page.route("https://**/*", route => route.abort());
  for (const [width, height] of [[1280, 720], [1024, 768], [390, 844]]) {
    await page.setViewportSize({ width, height });
    await page.goto(`http://127.0.0.1:8790/web/demo/?qa=legend-${width}#season=2`);
    await page.locator("#start").click();
    const snapshot = await page.evaluate(() => localStorage.getItem("fireline-season"));
    assert.equal(await page.locator("#map-legend").isVisible(), false);
    await page.locator("#legend-toggle").press("Enter");
    assert.equal(await page.locator("#legend-toggle").getAttribute("aria-expanded"), "true");
    assert.equal(await page.locator("#legend-toggle").getAttribute("aria-controls"), "map-legend");
    assert.equal(await page.locator("[data-cover-codes]").count(), 13);
    for (const row of coverClasses) {
      const node = page.locator(`[data-cover-codes="${row.codes.join(",")}"]`);
      assert.equal((await node.textContent()).trim(), row.name);
      const rgb = row.color.match(/\w\w/g).map(v => parseInt(v, 16));
      assert.equal(await node.locator("i").evaluate(n => getComputedStyle(n).backgroundColor), `rgb(${rgb.join(", ")})`);
    }
    const frame = await page.locator("#map-legend").evaluate(node => {
      const r = node.getBoundingClientRect();
      return { left: r.left, right: r.right, top: r.top, bottom: r.bottom,
        overflow: node.scrollWidth > node.clientWidth };
    });
    assert.ok(frame.left >= 0 && frame.right <= width && frame.top >= 0 && frame.bottom <= height);
    assert.equal(frame.overflow, false);
    assert.match(await page.locator("#map-legend small").textContent(), /not no vegetation/);
    await page.screenshot({ path: `${out}/${width}.png`, fullPage: width < 760 });
    const checked = [];
    for (const key of ["canopy", "lorey", "recovery", "water", "fuel", "height", "height-change"]) {
      await page.locator("#layer").selectOption(key);
      assert.equal(await page.locator("[data-cover-codes]").count(), 0);
      await page.waitForFunction(() => [...document.querySelectorAll("#map-legend img")]
        .every(image => image.complete && image.naturalWidth > 0));
      if (key === "height")
        for (const year of [1985, 1990, 1995, 2000, 2005, 2010, 2015]) {
          await page.locator(`[data-epoch="${year}"]`).click();
          assert.match(await page.locator("#layer-caption").textContent(), new RegExp(String(year)));
        }
      if (key === "height-change") {
        assert.match(await page.locator("#layer-caption").textContent(), /2015 − 1985/);
        assert.match(await page.locator("#map-legend small").textContent(), /do not identify growth/);
        assert.equal(await page.locator("#height-epochs").isVisible(), false);
        await page.waitForFunction(() => {
          const image = document.querySelector("#map-image");
          return image.complete && image.naturalWidth === 1118 && image.naturalHeight === 1200;
        });
        const r = await page.locator("#map-legend").boundingBox();
        assert.ok(r.x >= 0 && r.x + r.width <= width);
        await page.screenshot({ path: `${out}/change-${width}.png`, fullPage: width < 760 });
      }
      checked.push(key);
    }
    await page.locator("#layer").selectOption("cover");
    assert.equal(await page.locator("[data-cover-codes]").count(), 13);
    await page.locator("#legend-toggle").press("Enter");
    assert.equal(await page.locator("#map-legend").isVisible(), false);
    assert.equal(await page.locator("#legend-toggle").evaluate(n => n === document.activeElement), true);
    assert.equal(await page.evaluate(() => localStorage.getItem("fireline-season")), snapshot);
    assert.equal(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth), true);
    results.push({ width, height, frame, checked_other_layers: checked,
      height_epochs: 7, legend_groups: 13, source_codes: 14, save_unchanged: true });
  }
  assert.deepEqual(errors, []);
  for (const name of ["web/demo/strategy/cover-legend.js", "web/demo/strategy/context.js",
    "web/demo/strategy/legend-check.mjs", "web/demo/strategy/styles/map-controls.css", "web/demo/assets/strategy.js",
    "web/demo/strategy/main.js", "web/demo/assets/context/height-change.json",
    "web/demo/assets/context/height-change.png", "web/demo/assets/context/height-change-legend.png"])
    pinned[name] = hash(await fs.readFile(name));
  await fs.writeFile(`${out}/receipt.json`, JSON.stringify({ checked_utc: new Date().toISOString(),
    status: "passed", source_sha256: pinned, schema_sha256: hash(Buffer.from(schema)), results, errors,
    predictor_fits: 0, quantum_circuit_executions: 0, hardware_jobs: 0, downloads: 0,
    scope: "Every declared cover class/colour matches the palette/schema. Actual keyboard toggle and three-size framing; eight contexts and seven height epochs preserve the entire game save. The signed comparison loads its 1118x1200 map, hides the epoch strip, and explains estimated differences. No native reclassification, source accuracy, biological change, tree density or predictive improvement is established.",
  }, null, 2) + "\n");
  console.log("14 source codes in 13 groups, correct palette/labels, eight contexts and unchanged saves pass in three views.");
} finally { await browser.close(); }

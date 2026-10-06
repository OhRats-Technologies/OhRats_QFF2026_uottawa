// Native coordinates/gestures: no locator auto-scroll hides a short-screen defect.
import assert from "node:assert/strict";
import fs from "node:fs/promises";
import { execFileSync } from "node:child_process";
import { createHash } from "node:crypto";
import { createRequire } from "node:module";
const require = createRequire(`${process.env.RUNTIME_NODE_MODULES}/../package.json`);
const { chromium } = require("playwright");
const browser = await chromium.launch({ headless: true, channel: "chrome" });
const out = ".cache/judge-submission/short-viewport";
await fs.mkdir(out, { recursive: true });
const hash = bytes => createHash("sha256").update(bytes).digest("hex");
const save = page => page.evaluate(() => localStorage.getItem("fireline-season"));
const scroll = page => page.evaluate(() => scrollY);
const errors = [], results = [];

async function nativeClick(page, selector, touch) {
  const box = await page.locator(selector).boundingBox();
  const point = { x: box.x + box.width / 2, y: box.y + box.height / 2 };
  assert.equal(await page.evaluate(({ selector, point }) => Boolean(
    document.elementFromPoint(point.x, point.y)?.closest(selector)), { selector, point }), true,
  `${selector}: native hit point is outside the viewport or occluded`);
  if (touch) await page.touchscreen.tap(point.x, point.y);
  else await page.mouse.click(point.x, point.y);
}
async function pan(page, cdp, touch, delta, x = 8) {
  const height = page.viewportSize().height;
  if (!touch) {
    await page.mouse.move(x, height / 2);
    await page.mouse.wheel(0, delta);
  } else {
    const start = delta > 0 ? height - 45 : 45;
    const end = delta > 0 ? 45 : height - 45;
    const points = y => [{ x, y, id: 0, radiusX: 7, radiusY: 7, force: 1 }];
    await cdp.send("Input.dispatchTouchEvent", { type: "touchStart", touchPoints: points(start) });
    for (let i = 1; i <= 8; i++) {
      await cdp.send("Input.dispatchTouchEvent", { type: "touchMove",
        touchPoints: points(start + (end - start) * i / 8) });
      await new Promise(resolve => setTimeout(resolve, 30));
    }
    await cdp.send("Input.dispatchTouchEvent", { type: "touchEnd", touchPoints: [] });
  }
  await page.waitForTimeout(250);
}
async function createPage(width, height, touch) {
  const page = await browser.newPage({ viewport: { width, height }, hasTouch: touch,
    isMobile: touch, reducedMotion: "reduce" });
  page.setDefaultTimeout(10000);
  page.on("pageerror", error => errors.push(error.message));
  await page.route("https://**/*", route => route.abort());
  return page;
}

try {
  const baselineCommit = "0cd319a", baseline = await createPage(844, 390, true);
  const baselineStyles = execFileSync("git", ["ls-tree", "-r", "--name-only", baselineCommit,
    "--", "web/demo/strategy/styles", "web/demo/strategy.css"], { encoding: "utf8" }).trim().split("\n");
  const baselineFiles = ["web/demo/index.html", "web/demo/assets/strategy.js", ...baselineStyles];
  const bytes = Object.fromEntries(baselineFiles.map(path =>
    [path, execFileSync("git", ["show", `${baselineCommit}:${path}`])]));
  await baseline.route("**/web/demo/**", route => {
    const path = new URL(route.request().url()).pathname.slice(1);
    const key = path === "web/demo/" ? "web/demo/index.html" : path;
    return bytes[key] ? route.fulfill({ body: bytes[key],
      contentType: key.endsWith(".html") ? "text/html" : "text/javascript" }) : route.continue();
  });
  await baseline.goto("http://127.0.0.1:8790/web/demo/?qa=short-before#season=7");
  await baseline.locator("#welcome[open]").waitFor();
  const baselineBefore = await save(baseline);
  await nativeClick(baseline, "#start", true);
  const oldScroll = await scroll(baseline);
  assert.ok(oldScroll > 200);
  assert.equal(await save(baseline), baselineBefore);
  await baseline.screenshot({ path: `${out}/before-844.png` });
  await baseline.close();
  for (const [width, height, touch] of [[844, 390, true], [1024, 600, false]]) {
    const page = await createPage(width, height, touch);
    const cdp = await page.context().newCDPSession(page);
    await page.goto(`http://127.0.0.1:8790/web/demo/?qa=short-${width}#season=7`);
    await page.locator("#welcome[open]").waitFor();
    const before = await save(page);
    await nativeClick(page, "#start", touch);
    assert.equal(await scroll(page), 0);
    assert.equal(await page.evaluate(() => document.activeElement.id), "game-title");
    assert.equal(await save(page), before);
    await page.screenshot({ path: `${out}/${width}-entry.png` });
    if (touch) await pan(page, cdp, touch, 800);
    const commandScroll = await scroll(page);
    if (touch) assert.ok(commandScroll > 0);
    else assert.equal(commandScroll, 0, 'Short laptop command must work without scrolling');
    await nativeClick(page, "#advance", touch);
    const after = JSON.parse(await save(page));
    assert.deepEqual(after.moves, [{ type: "advance" }]);
    await pan(page, cdp, touch, -800);
    assert.equal(await scroll(page), 0);
    await nativeClick(page, "#guide-open", touch);
    await page.locator("#guide[open]").waitFor();
    await nativeClick(page, "#guide-close", touch);
    assert.equal(await save(page), JSON.stringify(after));
    assert.equal(await scroll(page), 0);
    assert.equal(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth), true);
    await page.screenshot({ path: `${out}/${width}-returned-map.png` });
    // Use a normal reload to exercise real continuation rather than QA's fresh-start mode.
    await page.goto("http://127.0.0.1:8790/web/demo/#season=7");
    await page.locator("#welcome[open]").waitFor();
    assert.equal((JSON.parse(await save(page))).moves.length, 1);
    await nativeClick(page, "#start", touch);
    assert.equal(await scroll(page), 0);
    assert.equal((JSON.parse(await save(page))).moves.length, 1);
    await page.reload();
    await page.locator("#welcome[open]").waitFor();
    await pan(page, cdp, touch, 800, width / 2);
    await nativeClick(page, "#fresh", touch);
    const fresh = JSON.parse(await save(page));
    assert.deepEqual(fresh.moves, []);
    assert.equal(fresh.seed, 588686121); // Fixed next-season vector for seed 7.
    assert.equal(await scroll(page), 0);
    assert.equal(await page.evaluate(() => document.activeElement.id), "game-title");
    results.push({ width, height, input: touch ? "touch" : "mouse/wheel", initial_scroll: 0,
      initial_focus: "game-title", native_command_scroll: commandScroll,
      exact_accepted_moves: after.moves, returned_to_map_scroll: 0, guide_save_unchanged: true,
      continuation_moves_preserved: true, fresh_seed: fresh.seed, fresh_moves: fresh.moves,
      locator_auto_scroll: false });
    await cdp.detach();
    await page.close();
  }
  assert.deepEqual(errors, []);
  const sources = ["web/demo/index.html", "web/demo/assets/strategy.js", "web/demo/strategy/main.js",
    "web/demo/strategy/short-viewport-check.mjs", "web/demo/strategy/styles/base.css",
    "web/demo/strategy/styles/compact.css", "web/demo/strategy/styles/responsive.css"];
  const hashes = {};
  for (const path of sources) hashes[path] = hash(await fs.readFile(path));
  await fs.writeFile(`${out}/receipt.json`, JSON.stringify({ checked_utc: new Date().toISOString(),
    status: "passed", baseline: { commit: baselineCommit, scroll_after_start: oldScroll,
      source_sha256: Object.fromEntries(baselineFiles.map(path => [path, hash(bytes[path])])) },
    source_sha256: hashes, results, errors, predictor_fits: 0, quantum_circuit_executions: 0,
    hardware_jobs: 0, scope: "Chromium on a Mac, emulated touch landscape and mouse/wheel short laptop. Native coordinate hits and gestures, no locator auto-scroll. Not a physical-device or assistive-technology study." }, null, 2) + "\n");
  console.log("Map-first entry and exact saves pass; laptop commands need no scroll, landscape touch uses native scrolling.");
} finally { await browser.close(); }

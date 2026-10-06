// Visible incident status follows the accepted game history, not colour alone.
import assert from "node:assert/strict";
import fs from "node:fs/promises";
import { createHash } from "node:crypto";
import { execFileSync } from "node:child_process";
import { createRequire } from "node:module";
import { replay } from "./session.js";
import { markerDescription } from "./marker-description.js";

const hash = bytes => createHash("sha256").update(bytes).digest("hex");
const source = JSON.parse(await fs.readFile("web/demo/assets/context/scenario.json", "utf8"));
const pinned = {};
for (const file of ["rules.js", "scenario.js", "upgrades.js", "session.js"]) {
  const name = `web/demo/strategy/${file}`, bytes = await fs.readFile(name);
  assert.equal(hash(bytes), hash(execFileSync("git", ["show", `HEAD:${name}`])));
  pinned[name] = hash(bytes);
}
const terminal = markerDescription({ id: 3, name: "Fixture", status: "burning", size: 2, crew: 1 }, true);
assert.equal(terminal.badge, "◇");
assert.match(terminal.aria, /season ended/);
assert.doesNotMatch(terminal.aria, /returns in/);
const require = createRequire(`${process.env.RUNTIME_NODE_MODULES}/../package.json`);
const { chromium } = require("playwright");
const browser = await chromium.launch({ headless: true, channel: "chrome", args: ["--mute-audio"] });
const out = ".cache/judge-submission/map-status";
await fs.mkdir(out, { recursive: true });
const results = [], errors = [];
try {
  const page = await browser.newPage();
  page.on("pageerror", error => errors.push(error.message));
  await page.route("https://**/*", route => route.abort());
  for (const [width, height, motion] of [[1280, 720, "reduce"], [1024, 768, "reduce"],
    [390, 844, "reduce"], [1280, 720, "no-preference"]]) {
    await page.setViewportSize({ width, height });
    await page.emulateMedia({ reducedMotion: motion });
    await page.goto(`http://127.0.0.1:8790/web/demo/?qa=map-state-${width}-${motion}#season=2`);
    await page.locator("#start").click();
    await page.evaluate(() => { window.__initialMarkers = [...document.querySelectorAll("[data-fire]")]; });
    const savedState = async () => replay(JSON.parse(await page.evaluate(() => localStorage.getItem("fireline-season"))), source.pool).state;
    async function inspect(id) {
      const fire = (await savedState()).incidents.find(item => item.id === id);
      const marker = page.locator(`[data-fire="${id}"]`);
      await marker.press("Enter");
      assert.equal(await marker.evaluate(node => node === document.activeElement), true);
      assert.equal(await marker.evaluate(node => window.__initialMarkers.includes(node)), true);
      assert.equal(await marker.locator(".fire-number").textContent(), fire.status === "contained" ? "✓" : String(id));
      assert.equal(await marker.locator(".fire-crew").isVisible(), fire.crew > 0);
      if (fire.crew) assert.equal(await marker.locator(".fire-crew").textContent(), String(fire.crew));
      const description = await marker.getAttribute("aria-label");
      assert.ok(description.includes(fire.status));
      if (fire.crew) assert.ok(description.includes(`returns in ${fire.crew} front`));
      await page.waitForFunction(id => Number(getComputedStyle(document.querySelector(`[data-fire="${id}"] .fire-name`)).opacity) > 0.99, id);
      const framing = await marker.evaluate(node => {
        const marker = node.getBoundingClientRect(), label = node.querySelector(".fire-name").getBoundingClientRect();
        return { width: marker.width, height: marker.height, labelLeft: label.left, labelRight: label.right };
      });
      assert.equal(framing.width, 30);
      assert.equal(framing.height, 30);
      assert.ok(framing.labelLeft >= 0 && framing.labelRight <= width, JSON.stringify(framing));
      if (motion === "reduce")
        assert.equal(await marker.evaluate(node => getComputedStyle(node, "::after").animationName), "none");
      await marker.hover();
      await page.waitForFunction(id => Number(getComputedStyle(document.querySelector(`[data-fire="${id}"] .fire-name`)).opacity) > 0.99, id);
      assert.equal(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth), true);
      return { front: fire.history.length, crew: fire.crew, status: fire.status, description, framing };
    }
    await page.locator('[data-fire="3"]').press("Enter");
    await page.locator('[data-action="crew"]').click();
    const countdown = [await inspect(3)];
    for (let front = 0; front < 2; front++) {
      await page.locator('[data-fire="1"]').press("Enter");
      await page.locator('[data-action="water"]').click();
      await page.locator("#advance").click();
      countdown.push(await inspect(3));
    }
    assert.deepEqual(countdown.map(item => item.crew), [2, 1, 0]);
    let state = await savedState();
    while (state.incidents[0].status === "burning") {
      assert.equal(state.status, "playing");
      assert.equal(state.upgradePending, false);
      await page.locator('[data-fire="1"]').press("Enter");
      await page.locator('[data-action="water"]').click();
      state = await savedState();
      if (state.incidents[0].status === "burning") await page.locator("#advance").click();
      state = await savedState();
      assert.ok(state.turn <= 3);
    }
    const contained = await inspect(1);
    assert.equal(contained.status, "contained");
    assert.equal(await page.locator('[data-action="water"]').isDisabled(), true);
    await page.screenshot({ path: `${out}/${width}-${motion}.png`, fullPage: width < 760 });
    results.push({ width, height, motion, countdown, contained });
  }
  assert.deepEqual(errors, []);
  const hashes = { ...pinned };
  for (const name of ["web/demo/strategy/map.js", "web/demo/strategy/marker-description.js",
    "web/demo/strategy/map-status-check.mjs", "web/demo/strategy/styles/map-markers.css", "web/demo/assets/strategy.js"])
    hashes[name] = hash(await fs.readFile(name));
  await fs.writeFile(`${out}/receipt.json`, JSON.stringify({ checked_utc: new Date().toISOString(),
    status: "passed", source_sha256: hashes, results, errors, predictor_fits: 0,
    qiskit_circuit_executions: 0, hardware_jobs: 0,
    scope: "Actual crew countdown, water containment, stable keyboard marker nodes, hover/focus descriptions and fixed hit areas at three sizes plus normal motion. Terminal description uses a separate bounded fixture. No rules/source-position/save-format changes; effects are illustrative, not real fire footprints.",
  }, null, 2) + "\n");
  console.log("Crew countdown 2→1→0, distinct containment, stable marker focus and framing pass across four views.");
} finally {
  await browser.close();
}

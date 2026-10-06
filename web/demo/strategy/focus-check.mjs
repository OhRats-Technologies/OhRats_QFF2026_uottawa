// Actual keyboard controls plus isolated pressure-order/containment DOM fixtures.
import assert from "node:assert/strict";
import fs from "node:fs/promises";
import { createHash } from "node:crypto";
import { execFileSync } from "node:child_process";
import { createRequire } from "node:module";

const hash = bytes => createHash("sha256").update(bytes).digest("hex");
const require = createRequire(`${process.env.RUNTIME_NODE_MODULES}/../package.json`);
const { chromium } = require("playwright");
const browser = await chromium.launch({ headless: true, channel: "chrome" });
const out = ".cache/judge-submission/incident-focus";
await fs.mkdir(out, { recursive: true });
const errors = [], results = [];
const beforeCommit = "16e346a";
const originalBundle = execFileSync("git", ["show", `${beforeCommit}:web/demo/assets/strategy.js`]);
try {
  const page = await browser.newPage({ reducedMotion: "reduce" });
  page.on("pageerror", error => errors.push(error.message));
  await page.route("https://**/*", route => route.abort());
  await page.route("**/assets/strategy.js", route => route.fulfill({
    contentType: "application/javascript", body: originalBundle,
  }));
  await page.goto("http://127.0.0.1:8790/web/demo/?qa=focus-before#season=2");
  await page.locator("#start").click();
  await page.locator('[data-incident="2"]').press("Enter");
  const before = await page.evaluate(() => ({
    focused_tag: document.activeElement.tagName,
    selected: JSON.parse(localStorage.getItem("fireline-season")).selected,
  }));
  assert.equal(before.focused_tag, "BODY");
  assert.equal(before.selected, 2);
  await page.unroute("**/assets/strategy.js");
  for (const [width, height] of [[1280, 720], [1024, 768], [390, 844]]) {
    await page.setViewportSize({ width, height });
    await page.goto(`http://127.0.0.1:8790/web/demo/?qa=focus-${width}#season=2`);
    await page.locator("#start").click();
    const chip = page.locator('[data-incident="2"]');
    const node = await chip.elementHandle();
    for (const key of ["Enter", "Space"]) {
      await chip.press(key);
      assert.equal(await node.evaluate(element => element === document.activeElement), true);
      assert.equal(await chip.getAttribute("aria-pressed"), "true");
      const saved = JSON.parse(await page.evaluate(() => localStorage.getItem("fireline-season")));
      assert.equal(saved.selected, 2);
      assert.deepEqual(saved.moves, []);
    }
    const orderBefore = await page.locator("[data-incident]").evaluateAll(nodes => nodes.map(n => n.dataset.incident));
    await chip.press("2"); // Immediate water response reduces pressure and changes ranking.
    assert.equal(await node.evaluate(element => element === document.activeElement), true);
    const orderAfter = await page.locator("[data-incident]").evaluateAll(nodes => nodes.map(n => n.dataset.incident));
    assert.notDeepEqual(orderBefore, orderAfter);
    const saved = JSON.parse(await page.evaluate(() => localStorage.getItem("fireline-season")));
    assert.deepEqual(saved.moves, [{ type: "action", id: 2, kind: "water" }]);
    assert.equal(await page.locator("#front-number").textContent(), "1 / 12");
    const index = orderAfter.indexOf("2");
    await page.keyboard.press("Tab");
    const expected = orderAfter[index + 1];
    if (expected) assert.equal(await page.evaluate(() => document.activeElement.dataset.incident), expected);
    else assert.equal(await page.evaluate(() => document.activeElement.closest("#incident-list") === null), true);
    await page.locator('[data-fire="3"]').press("Enter");
    assert.equal(await page.locator('[data-fire="3"]').evaluate(element => element === document.activeElement), true);
    assert.equal(await page.locator('[data-incident="3"]').getAttribute("aria-pressed"), "true");
    await chip.press("Enter");
    assert.equal(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth), true);
    await page.screenshot({ path: `${out}/${width}.png`, fullPage: width < 760 });
    results.push({ width, height, enter_space_preserve_focus: true,
      water_reorders_same_node: true, tab_follows_new_order: true, map_focus_preserved: true,
      accepted_moves: saved.moves });
  }
  // Exercise removal without changing the live game state or its save.
  const savedBefore = await page.evaluate(() => localStorage.getItem("fireline-season"));
  const fixtures = await page.evaluate(async () => {
    const { IncidentList } = await import("./strategy/incident-list.js");
    const root = document.createElement("div"), fallback = document.createElement("button");
    fallback.textContent = "Fixture advance";
    document.body.append(root, fallback);
    const list = new IncidentList(root, () => {}, fallback);
    const first = { id: 101, name: "Fixture A", size: 2 }, second = { id: 102, name: "Fixture B", size: 1 };
    list.render([first, second], 101);
    list.buttons.get(101).focus();
    list.render([second], 102);
    const containedFocus = document.activeElement === list.buttons.get(102);
    list.render([], undefined);
    const allClearFocus = document.activeElement === fallback;
    root.remove(); fallback.remove();
    return { contained_focus_next_fire: containedFocus, all_clear_focus_advance: allClearFocus };
  });
  assert.deepEqual(fixtures, { contained_focus_next_fire: true, all_clear_focus_advance: true });
  assert.equal(await page.evaluate(() => localStorage.getItem("fireline-season")), savedBefore);
  assert.deepEqual(errors, []);
  const files = ["incident-list.js", "ui.js", "focus-check.mjs", "rules.js", "scenario.js", "upgrades.js", "session.js"];
  const hashes = {};
  for (const file of files) {
    const name = `web/demo/strategy/${file}`;
    hashes[name] = hash(await fs.readFile(name));
    if (["rules.js", "scenario.js", "upgrades.js", "session.js"].includes(file))
      assert.equal(hashes[name], hash(execFileSync("git", ["show", `HEAD:${name}`])));
  }
  hashes["web/demo/assets/strategy.js"] = hash(await fs.readFile("web/demo/assets/strategy.js"));
  await fs.writeFile(`${out}/receipt.json`, JSON.stringify({
    checked_utc: new Date().toISOString(), status: "passed", before,
    before_commit: beforeCommit, before_bundle_sha256: hash(originalBundle), source_sha256: hashes, results, fixtures, errors,
    game_rule_changes: false, predictor_fits: 0, quantum_states: 0, hardware_jobs: 0,
    scope: "Keyboard selection/response and tab order on three viewports; isolated containment/all-clear DOM fixtures. Not a human gameplay or balance study.",
  }, null, 2) + "\n");
  console.log("Fire controls retain focus and node identity; containment/all-clear fallback and tab order pass.");
} finally {
  await browser.close();
}

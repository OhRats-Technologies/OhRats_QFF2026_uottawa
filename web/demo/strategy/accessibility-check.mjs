// Native-key interaction and Chromium's accessibility tree; not a screen-reader trial.
import assert from "node:assert/strict";
import fs from "node:fs/promises";
import { createHash } from "node:crypto";
import { execFileSync } from "node:child_process";
import { createRequire } from "node:module";

const require = createRequire(`${process.env.RUNTIME_NODE_MODULES}/../package.json`);
const { chromium } = require("playwright");
const browser = await chromium.launch({ headless: true, channel: "chrome" });
const output = ".cache/judge-submission/accessible-context";
const baseline = "b1c203a";
const hash = bytes => createHash("sha256").update(bytes).digest("hex");
const oldFiles = Object.fromEntries(["index.html", "assets/strategy.js"].map(path =>
  [path, execFileSync("git", ["show", `${baseline}:web/demo/${path}`])],
));
const errors = [], cases = [];
await fs.mkdir(output, { recursive: true });

async function tree(page) {
  const cdp = await page.context().newCDPSession(page);
  const result = await cdp.send("Accessibility.getFullAXTree");
  await cdp.detach();
  return result.nodes.filter(node => !node.ignored);
}

const role = (nodes, value) => nodes.filter(node => node.role?.value === value);
const name = node => node.name?.value ?? "";
const saved = page => page.evaluate(() => localStorage.getItem("fireline-season"));

try {
  const old = await browser.newPage({ reducedMotion: "reduce" });
  old.on("pageerror", error => errors.push(error.message));
  await old.route("https://**/*", route => route.abort());
  await old.route("**/assets/strategy.js", route => route.fulfill({
    body: oldFiles["assets/strategy.js"], contentType: "application/javascript",
  }));
  await old.route("**/web/demo/?qa=accessible-before*", route => route.fulfill({
    body: oldFiles["index.html"], contentType: "text/html",
  }));
  await old.goto("http://127.0.0.1:8790/web/demo/?qa=accessible-before#season=2");
  await old.locator("#welcome[open]").waitFor();
  const beforeWelcome = name(role(await tree(old), "dialog")[0]);
  assert.equal(beforeWelcome, "");
  await old.locator("#start").press("Enter");
  const beforeChip = await old.locator('[data-incident="2"]').getAttribute("aria-label");
  assert.equal(beforeChip, null);
  await old.locator("#guide-open").press("Enter");
  const beforeGuide = name(role(await tree(old), "dialog")[0]);
  assert.equal(beforeGuide, "");
  await old.close();

  for (const [width, height] of [[1280, 720], [844, 390], [390, 844]]) {
    const page = await browser.newPage({ viewport: { width, height }, reducedMotion: "reduce" });
    page.on("pageerror", error => errors.push(error.message));
    await page.route("https://**/*", route => route.abort());
    await page.goto(`http://127.0.0.1:8790/web/demo/?qa=accessible-${width}#season=2`);
    await page.locator("#welcome[open]").waitFor();
    const welcome = name(role(await tree(page), "dialog")[0]);
    assert.match(welcome, /Hold the\s*season\./);
    await page.locator("#start").press("Enter");
    // The qa query deliberately bypasses saves; resume through the normal URL.
    await page.evaluate(() => history.replaceState(null, "", location.pathname));
    assert.equal(await page.locator("#game-title").evaluate(node => node === document.activeElement), true);
    const chip = page.locator('[data-incident="2"]');
    await chip.press("Enter");
    const beforeMoves = JSON.parse(await saved(page)).moves;
    assert.deepEqual(beforeMoves, []);
    const firstName = await chip.getAttribute("aria-label");
    assert.match(firstName, /burning, pressure \d+\.\d/);
    assert.ok(role(await tree(page), "button").some(node => name(node) === firstName));
    await chip.press("1");
    assert.equal(await chip.evaluate(node => node === document.activeElement), true);
    const assignedName = await chip.getAttribute("aria-label");
    assert.match(assignedName, /Crew returns in 2 fronts/);
    assert.ok(role(await tree(page), "button").some(node => name(node) === assignedName));
    assert.deepEqual(JSON.parse(await saved(page)).moves, [{ type: "action", id: 2, kind: "crew" }]);
    const readout = role(await tree(page), "group").find(node => name(node) === "Pressure and reserve projection");
    assert.ok(readout);
    assert.match(readout.description?.value ?? "", /Toy fuel .*exposure .*fictional game units, not hectares/);
    assert.match(await page.locator("#announcement").textContent(), /crew/i);
    const checkpoint = await saved(page);
    await page.locator("#guide-open").press("Enter");
    const guide = name(role(await tree(page), "dialog")[0]);
    assert.equal(guide, "Decisions, not reflexes.");
    assert.equal(await saved(page), checkpoint);
    await page.keyboard.press("Escape");
    assert.equal(await page.locator("#guide-open").evaluate(node => node === document.activeElement), true);
    assert.equal(await saved(page), checkpoint);
    await page.reload();
    await page.locator("#start").press("Enter");
    assert.equal(await saved(page), checkpoint);
    assert.equal(await chip.getAttribute("aria-label"), assignedName);
    assert.equal(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth), true);
    cases.push({ width, height, welcome, guide, fire_button: assignedName,
      readout_description: readout.description.value, keyboard_focus_and_crew_response: true,
      escape_returns_to_opener: true, exact_save_preserved_through_guide_and_reload: true });
    await page.close();
  }
  assert.deepEqual(errors, []);
  const paths = ["web/demo/index.html", "web/demo/assets/strategy.js", ...[
    "incident-list.js", "marker-description.js", "ui.js", "main.js", "keyboard.js",
    "rules.js", "scenario.js", "upgrades.js", "session.js", "accessibility-check.mjs",
  ].map(path => `web/demo/strategy/${path}`)];
  const pins = Object.fromEntries(await Promise.all(paths.map(async path => [path, hash(await fs.readFile(path))])));
  for (const path of paths.filter(path => /\/(rules|scenario|upgrades|session)\.js$/.test(path)))
    assert.equal(pins[path], hash(execFileSync("git", ["show", `${baseline}:${path}`])));
  const receipt = { checked_utc: new Date().toISOString(), status: "passed", baseline,
    baseline_hashes: Object.fromEntries(Object.entries(oldFiles).map(([path, bytes]) => [path, hash(bytes)])),
    before: { welcome_name: beforeWelcome, guide_name: beforeGuide, fire_chip_label: beforeChip },
    source_sha256: pins, cases, errors, game_rule_changes: false,
    new_predictor_fits: 0, new_quantum_states: 0, hardware_jobs: 0,
    scope: "Chromium accessibility-tree exposure and native keys in isolated pages at three sizes. No physical screen reader, speech output, assistive device or human enjoyment certification." };
  await fs.writeFile(`${output}/receipt.json`, JSON.stringify(receipt, null, 2) + "\n");
  console.log("Accessible dialog names, fire status/context, native focus and exact-save continuation pass at three sizes.");
} finally {
  await browser.close();
}

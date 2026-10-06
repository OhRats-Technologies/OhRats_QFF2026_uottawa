// Exercise real keys from different controls, plus explicit composition fixtures.
import assert from "node:assert/strict";
import fs from "node:fs/promises";
import { execFileSync } from "node:child_process";
import { createHash } from "node:crypto";
import { createRequire } from "node:module";
import { replay } from "./session.js";

const hash = bytes => createHash("sha256").update(bytes).digest("hex");
const baselineCommit = "baa0d9c";
const baselineBundle = execFileSync("git", ["show", `${baselineCommit}:web/demo/assets/strategy.js`]);
const source = JSON.parse(await fs.readFile("web/demo/assets/context/scenario.json", "utf8"));
const pinned = {};
for (const file of ["rules.js", "scenario.js", "upgrades.js", "session.js"]) {
  const path = `web/demo/strategy/${file}`, bytes = await fs.readFile(path);
  assert.equal(hash(bytes), hash(execFileSync("git", ["show", `HEAD:${path}`])));
  pinned[path] = hash(bytes);
}
const require = createRequire(`${process.env.RUNTIME_NODE_MODULES}/../package.json`);
const { chromium } = require("playwright");
const browser = await chromium.launch({ headless: true, channel: "chrome", args: ["--mute-audio"] });
const out = ".cache/judge-submission/keyboard";
await fs.mkdir(out, { recursive: true });
const results = [], errors = [];
try {
  const page = await browser.newPage({ reducedMotion: "reduce" });
  page.on("pageerror", e => errors.push(e.message));
  await page.route("https://**/*", route => route.abort());
  const saved = async () => JSON.parse(await page.evaluate(() => localStorage.getItem("fireline-season")));
  const state = async () => replay(await saved(), source.pool).state;
  const moves = async () => JSON.stringify((await saved()).moves);
  await page.route("**/assets/strategy.js", route => route.fulfill({ contentType: "text/javascript",
    body: baselineBundle }));
  await page.goto("http://127.0.0.1:8790/web/demo/?qa=keyboard-before#season=2");
  await page.locator("#start").click();
  await page.locator('[data-fire="1"]').press("Enter");
  await page.locator('[data-fire="1"]').press("n");
  assert.equal((await state()).turn, 0);
  await page.unroute("**/assets/strategy.js");
  for (const [width, height] of [[1280, 720], [1024, 768], [390, 844]]) {
    await page.setViewportSize({ width, height });
    await page.goto(`http://127.0.0.1:8790/web/demo/?qa=keyboard-${width}#season=2`);
    await page.locator("#start").press("n");
    assert.equal((await state()).turn, 0);
    await page.locator("#start").click();
    const marker = page.locator('[data-fire="1"]');
    await marker.press("Space");
    assert.equal((await state()).turn, 0); // Native marker selection, not advancement.
    await marker.press("n");
    assert.equal((await state()).turn, 1);
    assert.equal(await marker.evaluate(n => n === document.activeElement), true);
    await page.locator('[data-action="crew"]').press("n");
    assert.equal((await state()).turn, 2);
    await marker.press("1");
    await marker.press("2");
    assert.deepEqual((await saved()).moves.slice(-2).map(m => [m.type, m.kind]),
      [["action", "crew"], ["action", "water"]]);
    const beforeGuards = await moves();
    await page.locator("#lens-toggle").click();
    for (const selector of ['#damping', '#dephasing', '#coherent-noise', '#layer']) {
      await page.locator(selector).press("n");
      assert.equal(await moves(), beforeGuards, selector);
    }
    await page.locator("#damping").press("ArrowRight");
    assert.equal(await page.locator("#damping").getAttribute("aria-valuenow"), "0.01");
    await marker.press("Alt+n");
    assert.equal(await moves(), beforeGuards);
    await marker.evaluate(node => {
      for (const flags of [{ isComposing: true }, { metaKey: true }, { ctrlKey: true }])
        node.dispatchEvent(new KeyboardEvent("keydown", { key: "n", bubbles: true, ...flags }));
    });
    assert.equal(await moves(), beforeGuards);
    await page.locator("#guide-open").click();
    await page.locator("#guide-close").press("n");
    assert.equal(await moves(), beforeGuards);
    await page.locator("#guide-close").click();
    await page.evaluate(() => {
      const edit = document.createElement("textarea");
      edit.id = "keyboard-edit-fixture";
      document.body.append(edit);
    });
    await page.locator("#keyboard-edit-fixture").press("n");
    assert.equal(await moves(), beforeGuards);
    await page.locator("#keyboard-edit-fixture").evaluate(node => node.remove());
    await marker.press("Enter");
    await page.keyboard.down("n");
    assert.equal((await state()).turn, 3);
    await page.keyboard.down("n"); // Browser marks the second keydown as a repeat.
    assert.equal((await state()).turn, 3);
    await page.keyboard.up("n");
    await page.locator("#advance").press("Space");
    assert.equal((await state()).turn, 4);
    const atUpgrade = await moves();
    await page.locator("#upgrade-options button").first().press("n");
    assert.equal(await moves(), atUpgrade);
    await page.locator("#upgrade-options button").first().click();
    assert.equal(await page.locator("#advance").getAttribute("aria-keyshortcuts"), "N");
    assert.equal(await page.locator("#advance small").textContent(), "N");
    assert.equal(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth), true);
    await page.locator("#lens-toggle").click();
    await page.screenshot({ path: `${out}/${width}.png`, fullPage: width < 760 });
    while ((await state()).status === "playing") {
      if (await page.locator("#upgrade").evaluate(n => n.open))
        await page.locator("#upgrade-options button").first().click();
      else await page.locator("#advance").press("n");
    }
    const ending = await state(), terminalMoves = await moves();
    await page.locator("#debrief").press("Escape");
    await page.locator("#advance").press("n");
    assert.equal(await page.locator("#debrief").evaluate(n => n.open), true);
    assert.equal(await moves(), terminalMoves);
    results.push({ width, height, terminalStatus: ending.status, terminalFront: ending.turn,
      mapAndResponseAdvance: true, nativeSpaceRetained: true, heldKeyOneFrontOnly: true,
      crewAndWaterShortcuts: true, editableAndModalGuards: true, compositionAndCommandModifierFixtures: true,
      terminalReportReopensWithoutMove: true });
  }
  assert.deepEqual(errors, []);
  for (const path of ["web/demo/strategy/main.js", "web/demo/strategy/keyboard.js",
    "web/demo/strategy/keyboard-check.mjs", "web/demo/strategy/ui.js", "web/demo/index.html", "web/demo/assets/strategy.js"])
    pinned[path] = hash(await fs.readFile(path));
  await fs.writeFile(`${out}/receipt.json`, JSON.stringify({ checked_utc: new Date().toISOString(),
    status: "passed", source_sha256: pinned, baselineCommit,
    baselineBundleSHA256: hash(baselineBundle), baselineNDoesNotAdvance: true, results, errors,
    predictor_fits: 0, qiskit_circuit_executions: 0, hardware_jobs: 0,
    scope: "Actual browser key input and saved-rule replay; composition/command modifier flags and a temporary textarea are explicitly authoring fixtures. Three sizes, unchanged rules/scenario/upgrades/save version. No physical keyboard, touch or assistive-device certification.",
  }, null, 2) + "\n");
  console.log("N advances consistently; native Space, held-key, editable/modal guards and terminal report pass in three views.");
} finally { await browser.close(); }

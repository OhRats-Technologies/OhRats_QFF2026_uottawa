import assert from "node:assert/strict";
import fs from "node:fs/promises";
import { execFileSync } from "node:child_process";
import { createHash } from "node:crypto";
import { createRequire } from "node:module";
import { createRun, action, advance, active, available, forecast } from "./rules.js";
import { upgradeChoices, applyUpgrade } from "./upgrades.js";
const require = createRequire(`${process.env.RUNTIME_NODE_MODULES}/../package.json`);
const { chromium } = require("playwright");
const browser = await chromium.launch({ channel: "chrome", headless: true });
const source = JSON.parse(await fs.readFile("web/demo/assets/context/scenario.json", "utf8"));
const out = ".cache/judge-submission/upgrade-choice";
await fs.mkdir(out, { recursive: true });
const hash = bytes => createHash("sha256").update(bytes).digest("hex");
const save = page => page.evaluate(() => JSON.parse(localStorage.getItem("fireline-season")));
const errors = [], results = [];

async function geometry(page) {
  return page.locator("#upgrade").evaluate(dialog => {
    const box = dialog.getBoundingClientRect();
    const choices = [...dialog.querySelectorAll("button")].map(button => {
      const rect = button.getBoundingClientRect(), x = rect.x + rect.width / 2, y = rect.y + rect.height / 2;
      return { id: button.dataset.upgrade, description: button.querySelector("small").textContent,
        rect: rect.toJSON(), native_center_hit: document.elementFromPoint(x, y) === button ||
          document.elementFromPoint(x, y)?.closest("button") === button };
    });
    return { nativeTapHighlight: getComputedStyle(document.querySelector("#advance")).webkitTapHighlightColor,
      rect: box.toJSON(), scrollTop: dialog.scrollTop, scrollHeight: dialog.scrollHeight,
      clientHeight: dialog.clientHeight, label: dialog.getAttribute("aria-labelledby"), choices };
  });
}
async function chooseNative(page, choice, touch) {
  const box = await page.locator(`[data-upgrade="${choice}"]`).boundingBox();
  const x = box.x + box.width / 2, y = box.y + box.height / 2;
  if (touch) await page.touchscreen.tap(x, y);
  else await page.mouse.click(x, y);
}

try {
  const baselineCommit = "a32315b", baseline = await browser.newPage({ viewport: { width: 844, height: 390 } });
  await baseline.route("https://**/*", route => route.abort());
  const files = ["web/demo/index.html", "web/demo/strategy/styles/dialogs.css"];
  const bytes = Object.fromEntries(files.map(path => [path, execFileSync("git", ["show", `${baselineCommit}:${path}`])]));
  await baseline.route("**/web/demo/**", route => {
    const path = new URL(route.request().url()).pathname.slice(1);
    const key = path === "web/demo/" ? "web/demo/index.html" : path;
    return bytes[key] ? route.fulfill({ body: bytes[key], contentType: key.endsWith(".html") ? "text/html" : "text/css" })
      : route.continue();
  });
  await baseline.goto("http://127.0.0.1:8790/web/demo/?qa=upgrade-before#season=7");
  await baseline.locator("#start").click();
  for (let i = 0; i < 4; i++) await baseline.locator("#advance").click();
  const before = await geometry(baseline);
  assert.ok(before.scrollHeight > before.clientHeight);
  assert.ok(before.choices[2].rect.bottom > before.rect.bottom);
  await baseline.screenshot({ path: `${out}/before-landscape.png` });
  await baseline.close();
  for (const [width, height, touch] of [[844, 390, true], [320, 568, true], [1280, 720, false]]) {
    const page = await browser.newPage({ viewport: { width, height }, hasTouch: touch,
      isMobile: touch, reducedMotion: "reduce" });
    page.setDefaultTimeout(10000);
    page.on("pageerror", error => errors.push(error.message));
    await page.route("https://**/*", route => route.abort());
    await page.goto(`http://127.0.0.1:8790/web/demo/?qa=upgrade-${width}#season=7`);
    if (touch) await page.locator("#start").tap(); else await page.locator("#start").click();
    const state = createRun(7, source.pool), moves = [], milestones = [];
    async function click(selector) {
      if (touch) await page.locator(selector).tap(); else await page.locator(selector).click();
    }
    while (state.turn < 8 || state.upgradePending) {
      if (state.upgradePending) {
        const offered = upgradeChoices(state), layout = await geometry(page);
        assert.equal(layout.label, "upgrade-title");
        assert.equal(layout.nativeTapHighlight, "rgba(0, 0, 0, 0)");
        assert.equal(layout.scrollTop, 0);
        assert.ok(layout.scrollHeight <= layout.clientHeight);
        assert.deepEqual(layout.choices.map(item => [item.id, item.description]), offered.map(item => [item.id, item.description]));
        for (const choice of layout.choices) {
          assert.equal(choice.native_center_hit, true);
          assert.ok(choice.rect.top >= layout.rect.top && choice.rect.bottom <= layout.rect.bottom);
          assert.ok(choice.rect.left >= 0 && choice.rect.right <= width);
        }
        const beforeChoice = await save(page);
        assert.deepEqual(beforeChoice.moves, moves);
        await page.screenshot({ path: `${out}/${width}-front-${state.turn}.png` });
        const choice = offered.find(item => item.id === "network") ?? offered[0];
        await chooseNative(page, choice.id, touch);
        assert.equal(applyUpgrade(state, choice.id), true);
        moves.push({ type: "upgrade", id: choice.id });
        assert.deepEqual((await save(page)).moves, moves);
        assert.equal(await page.locator("#upgrade").evaluate(d => d.open), false);
        milestones.push({ front: state.turn, selected: choice.id, layout, native_selection: true });
        continue;
      }
      assert.equal(state.status, "playing");
      const fires = active(state).sort((a, b) => b.size - a.size);
      for (const kind of ["crew", "water"]) for (const fire of fires) {
        const use = kind === "crew" ? !fire.crew && available(state) && state.supplies >= 2
          : forecast(state, fire) > 1.1 && state.supplies >= 4;
        if (!use) continue;
        await click(`[data-incident="${fire.id}"]`);
        await click(`[data-action="${kind}"]`);
        assert.equal(action(state, fire.id, kind), true);
        moves.push({ type: "action", id: fire.id, kind });
      }
      await click("#advance");
      assert.equal(advance(state), true);
      moves.push({ type: "advance" });
    }
    assert.deepEqual(milestones.map(item => item.front), [4, 8]);
    assert.deepEqual((await save(page)).moves, moves);
    results.push({ width, height, input: touch ? "touch" : "mouse", accepted_moves: moves.length,
      move_replay_exact: true, milestones, gameplay_locators_auto_scroll: true,
      upgrade_selection_auto_scroll: false });
    await page.close();
  }
  assert.deepEqual(errors, []);
  const hashes = {};
  for (const path of ["web/demo/index.html", "web/demo/strategy/styles/dialogs.css", "web/demo/strategy/styles/base.css",
    "web/demo/strategy/upgrade-choice-check.mjs", "web/demo/assets/strategy.js", "web/demo/assets/context/scenario.json"])
    hashes[path] = hash(await fs.readFile(path));
  for (const name of ["rules.js", "scenario.js", "upgrades.js", "session.js"]) {
    const path = `web/demo/strategy/${name}`, bytes = await fs.readFile(path);
    hashes[path] = hash(bytes);
    assert.equal(hash(bytes), hash(execFileSync("git", ["show", `HEAD:${path}`])));
  }
  await fs.writeFile(`${out}/receipt.json`, JSON.stringify({ checked_utc: new Date().toISOString(), status: "passed",
    baseline: { commit: baselineCommit, layout: before,
      source_sha256: Object.fromEntries(files.map(path => [path, hash(bytes[path])])) },
    source_sha256: hashes, results, errors, predictor_fits: 0, quantum_circuit_executions: 0, hardware_jobs: 0,
    scope: "Chromium, blocked remote fonts, one replayed season per size. Both milestone comparisons fit without dialog scrolling; native selection coordinates do not auto-scroll. Preparatory gameplay locators do. Not physical-device, human choice or enjoyment certification." }, null, 2) + "\n");
  console.log("All three tradeoffs fit together at both milestones, with native selections and exact move replay.");
} finally { await browser.close(); }

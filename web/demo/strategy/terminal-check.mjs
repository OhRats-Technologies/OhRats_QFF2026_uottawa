// Verify terminal map inspection, keyboard report access and restart/resume.
import assert from "node:assert/strict";
import fs from "node:fs/promises";
import { createHash } from "node:crypto";
import { execFileSync } from "node:child_process";
import { createRequire } from "node:module";
import { createRun, action, advance, active, available, forecast } from "./rules.js";
import { applyUpgrade, upgradeChoices } from "./upgrades.js";
import { seasonBreakdown } from "./debrief.js";

const hash = bytes => createHash("sha256").update(bytes).digest("hex");
const source = JSON.parse(await fs.readFile("web/demo/assets/context/scenario.json", "utf8"));
function fixture(seed, triage) {
  const state = createRun(seed, source.pool), moves = [];
  while (state.status === "playing") {
    if (state.upgradePending) {
      const order = ["training", "logistics", "network", "precision"];
      const choice = upgradeChoices(state).sort((a, b) => order.indexOf(a.id) - order.indexOf(b.id))[0];
      assert.equal(applyUpgrade(state, choice.id), true);
      moves.push({ type: "upgrade", id: choice.id });
    }
    if (triage) {
      const fires = active(state).sort((a, b) => b.size - a.size);
      const respond = (fire, kind) => {
        if (action(state, fire.id, kind)) moves.push({ type: "action", id: fire.id, kind });
      };
      for (const fire of fires) {
        if (!fire.crew && available(state) > 0) respond(fire, "crew");
      }
      for (const fire of fires) {
        if (forecast(state, fire) > 1.1 && state.supplies >= 4) respond(fire, "water");
      }
    }
    assert.equal(advance(state), true);
    moves.push({ type: "advance" });
  }
  assert.equal(state.status, triage ? "won" : "lost");
  return { seed, state, moves };
}
const fixtures = [fixture(2, true), fixture(7, false)];
const require = createRequire(`${process.env.RUNTIME_NODE_MODULES}/../package.json`);
const { chromium } = require("playwright");
const browser = await chromium.launch({ headless: true, channel: "chrome" });
const out = ".cache/judge-submission/end-menu";
await fs.mkdir(out, { recursive: true });
const results = [], errors = [];
try {
  const page = await browser.newPage({ reducedMotion: "reduce" });
  page.on("pageerror", error => errors.push(error.message));
  await page.route("https://**/*", route => route.abort());
  for (const [width, height] of [[1280, 720], [1024, 768], [390, 844]]) {
    await page.setViewportSize({ width, height });
    for (const { seed, state, moves } of fixtures) {
      await page.goto(`http://127.0.0.1:8790/web/demo/?qa=terminal-${width}-${seed}#season=${seed}`);
      await page.locator("#start").click();
      for (const move of moves) {
        if (move.type === "upgrade") await page.locator(`[data-upgrade="${move.id}"]`).click();
        else if (move.type === "action") {
          await page.locator(`[data-incident="${move.id}"]`).click();
          await page.locator(`[data-action="${move.kind}"]`).click();
        } else await page.locator("#advance").click();
      }
      assert.equal(await page.locator("#debrief").evaluate(dialog => dialog.open), true);
      const description = seasonBreakdown(state);
      const directImpact = state.history.reduce((sum, row) => sum + row.damage, 0);
      assert.ok(Math.abs(description.total - directImpact) < 1e-10);
      assert.ok(Math.abs(description.total - state.damage) < 1e-10);
      assert.match(await page.locator("#debrief-peak").textContent(), new RegExp(`front ${description.peak.front}`));
      assert.equal(await page.locator("[data-impact-fire]").count(), description.top.length);
      for (const fire of description.top) {
        const row = page.locator(`[data-impact-fire="${fire.id}"]`);
        assert.match(await row.textContent(), new RegExp(fire.name));
        assert.ok((await row.textContent()).includes(`${fire.impact.toFixed(1)} · ${(fire.share * 100).toFixed(0)}%`));
      }
      assert.match(await page.locator("#debrief-impact").getAttribute("aria-label"), /not effects prevented/);
      const frame = await page.locator("#debrief").boundingBox();
      assert.ok(frame.x >= 0 && frame.x + frame.width <= width && frame.y >= 0 && frame.y + frame.height <= height);
      const opening = await page.locator("#debrief").evaluate(dialog => ({
        scrollTop: dialog.scrollTop, scrollHeight: dialog.scrollHeight,
        clientHeight: dialog.clientHeight, titleFocused: document.activeElement.id === "debrief-title",
      }));
      assert.equal(opening.scrollTop, 0);
      assert.equal(opening.titleFocused, true);
      assert.ok(opening.scrollHeight <= opening.clientHeight + 1, `${width} ${state.status}: ${JSON.stringify(opening)}`);
      await page.screenshot({ path: `${out}/${width}-${state.status}-report.png` });
      const snapshot = JSON.parse(await page.evaluate(() => localStorage.getItem("fireline-season")));
      assert.deepEqual(snapshot.moves, moves);
      await page.keyboard.press("Escape");
      assert.equal(await page.locator("#debrief").evaluate(dialog => dialog.open), false);
      assert.equal(await page.locator("#advance").isEnabled(), true);
      assert.match(await page.locator("#advance").innerText(), /Season report/);
      assert.equal(await page.locator("#front-number").textContent(), `${state.turn} / 12`);
      assert.equal(await page.locator("#front-name").textContent(), state.weather[state.turn - 1].name);
      assert.match(await page.locator("#incident-readout").textContent(), /—season ended/);
      assert.deepEqual(await page.locator("[data-action] small").allTextContents(), ["", ""]);
      await page.locator("[data-incident]").first().click();
      assert.equal(await page.locator("#debrief").evaluate(dialog => dialog.open), false);
      const inspected = await page.evaluate(() => localStorage.getItem("fireline-season"));
      assert.deepEqual(JSON.parse(inspected).moves, moves);
      await page.locator("#advance").press("Enter");
      assert.equal(await page.locator("#debrief").evaluate(dialog => dialog.open), true);
      assert.equal(await page.evaluate(() => localStorage.getItem("fireline-season")), inspected);
      await page.keyboard.press("Escape");
      // The QA query intentionally ignores saves; use the normal viewer for resume.
      await page.goto(`http://127.0.0.1:8790/web/demo/#season=${seed}`);
      await page.locator("#debrief[open]").waitFor();
      await page.reload();
      await page.locator("#debrief[open]").waitFor();
      assert.equal(await page.locator("#debrief").evaluate(dialog => dialog.open), true);
      assert.equal(await page.locator("#welcome").evaluate(dialog => dialog.open), false);
      assert.deepEqual(JSON.parse(await page.evaluate(() => localStorage.getItem("fireline-season"))).moves, moves);
      await page.keyboard.press("Escape");
      await page.locator("#advance").press("Space");
      assert.equal(await page.locator("#debrief").evaluate(dialog => dialog.open), true);
      assert.equal(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth), true);
      await page.keyboard.press("Escape");
      await page.screenshot({ path: `${out}/${width}-${state.status}.png`, fullPage: width < 760 });
      await page.locator("#advance").click();
      await page.locator(seed === 7 ? "#retry" : "#new-season").click();
      assert.equal(await page.locator("#debrief").evaluate(dialog => dialog.open), false);
      assert.equal(await page.locator("#supplies").textContent(), "18");
      assert.equal(await page.locator("#front-number").textContent(), "1 / 12");
      assert.deepEqual(await page.locator("[data-action] small").allTextContents(),
        ["Suppression over 2 fronts", "Reduce pressure immediately"]);
      const fresh = JSON.parse(await page.evaluate(() => localStorage.getItem("fireline-season")));
      assert.equal(fresh.seed, seed === 7 ? seed : 3024231355); // Replay 7; new season from 2.
      assert.deepEqual(fresh.moves, []);
      results.push({ width, height, seed, status: state.status, completed_fronts: state.turn,
        inspected_without_reopening: true, keyboard_report: true, resume_report: true,
        report_preserves_moves: true, restart: seed === 7 ? "same_seed" : "new_seed" });
      results.at(-1).recorded_impact = description.total;
      results.at(-1).top_fire_ids = description.top.map(fire => fire.id);
      results.at(-1).peak_front = description.peak.front;
      results.at(-1).report_frame = frame;
      results.at(-1).opening = opening;
    }
  }
  assert.deepEqual(errors, []);
  const hashes = {};
  for (const file of ["rules.js", "scenario.js", "upgrades.js", "session.js", "ui.js", "main.js", "debrief.js", "terminal-check.mjs"]) {
    const name = `web/demo/strategy/${file}`;
    const bytes = await fs.readFile(name);
    hashes[name] = hash(bytes);
    if (["rules.js", "scenario.js", "upgrades.js", "session.js"].includes(file)) {
      assert.equal(hashes[name], hash(execFileSync("git", ["show", `HEAD:${name}`])));
    }
  }
  hashes["web/demo/assets/strategy.js"] = hash(await fs.readFile("web/demo/assets/strategy.js"));
  for (const name of ["web/demo/index.html", "web/demo/strategy/styles/dialogs.css"])
    hashes[name] = hash(await fs.readFile(name));
  await fs.writeFile(`${out}/after.json`, JSON.stringify({
    checked_utc: new Date().toISOString(), status: "passed", source_sha256: hashes, results, errors,
    game_rule_changes: false, predictor_fits: 0, qiskit_statevector_executions: 0, hardware_jobs: 0,
    scope: "Actual control-driven winning/losing endings at three viewports. Per-fire sums agree with stored front damage, peak front/ranked contributions are displayed, reports preserve moves across close/reopen/reload/retry. Reduced motion and external-font failure covered; no new balance estimate, human enjoyment trial, causal response effect or real fire validation.",
  }, null, 2) + "\n");
  console.log("Escape, map inspection, keyboard report, terminal resume and restart pass for both endings.");
} finally {
  await browser.close();
}

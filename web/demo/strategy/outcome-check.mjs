// Accepted visible controls must report the same front as move replay.
import assert from "node:assert/strict";
import fs from "node:fs/promises";
import { createHash } from "node:crypto";
import { execFileSync } from "node:child_process";
import { createRequire } from "node:module";
import { createRun, action, advance, active, available, forecast } from "./rules.js";
import { applyUpgrade, upgradeChoices } from "./upgrades.js";
import { replay } from "./session.js";
import { frontOutcome } from "./outcome.js";

const hash = bytes => createHash("sha256").update(bytes).digest("hex");
const source = JSON.parse(await fs.readFile("web/demo/assets/context/scenario.json", "utf8"));
const pinned = {};
for (const file of ["rules.js", "scenario.js", "upgrades.js", "session.js"]) {
  const name = `web/demo/strategy/${file}`;
  const bytes = await fs.readFile(name);
  assert.equal(hash(bytes), hash(execFileSync("git", ["show", `HEAD:${name}`])));
  pinned[name] = hash(bytes);
}
assert.equal(frontOutcome(createRun(2, source.pool)), null);
const extreme = createRun(2, source.pool);
advance(extreme);
const reserveBefore = extreme.integrity;
for (const fire of active(extreme)) {
  fire.size = 9;
  fire.exposure = 100; // Disposable stress fixture, outside the game distribution.
}
advance(extreme);
assert.equal(extreme.integrity, 0);
assert.equal(frontOutcome(extreme).reserveLost, reserveBefore);
assert.ok(extreme.history.at(-1).damage > reserveBefore);
const require = createRequire(`${process.env.RUNTIME_NODE_MODULES}/../package.json`);
const { chromium } = require("playwright");
const browser = await chromium.launch({ headless: true, channel: "chrome" });
const out = ".cache/judge-submission/front-outcomes";
await fs.mkdir(out, { recursive: true });
const results = [], errors = [];
const base = "http://127.0.0.1:8790";
try {
  const page = await browser.newPage({ reducedMotion: "reduce" });
  page.on("pageerror", error => errors.push(error.message));
  await page.route("**/*", route => new URL(route.request().url()).origin === base
    ? route.continue() : route.abort());
  const cases = [[1280, 720, 2, "triage"], [1024, 768, 2, "triage"],
    [390, 844, 2, "triage"], [1280, 720, 7, "idle"]];
  for (const [width, height, seed, policy] of cases) {
    await page.setViewportSize({ width, height });
    await page.goto(`${base}/web/demo/?qa=outcome-${width}-${policy}#season=${seed}`);
    await page.locator("#start").click();
    const state = createRun(seed, source.pool);
    const fronts = [];
    while (state.status === "playing") {
      if (state.upgradePending) {
        const order = ["training", "logistics", "network", "precision"];
        const choice = upgradeChoices(state).sort((a, b) => order.indexOf(a.id) - order.indexOf(b.id))[0];
        await page.locator(`[data-upgrade="${choice.id}"]`).click();
        assert.equal(applyUpgrade(state, choice.id), true);
      }
      const before = {
        reserve: state.integrity, contained: state.contained,
        ids: active(state).map(fire => fire.id),
      };
      if (policy === "triage") {
        const fires = active(state).sort((a, b) => b.size - a.size);
        async function respond(fire, kind) {
          await page.locator(`[data-incident="${fire.id}"]`).click();
          await page.locator(`[data-action="${kind}"]`).click();
          assert.equal(action(state, fire.id, kind), true);
        }
        for (const fire of fires) {
          if (!fire.crew && available(state) > 0 && state.supplies >= 2) await respond(fire, "crew");
        }
        for (const fire of fires) {
          if (forecast(state, fire) > 1.1 && state.supplies >= 4) await respond(fire, "water");
        }
      }
      const afterActionsSupplies = state.supplies;
      await page.locator("#advance").click();
      assert.equal(advance(state), true);
      const frozenState = JSON.stringify(state);
      const outcome = frontOutcome(state);
      assert.equal(JSON.stringify(state), frozenState, "Outcome must not change state");
      assert.ok(Math.abs(outcome.reserveLost - (before.reserve - state.integrity)) < 1e-10);
      assert.equal(outcome.contained, state.contained - before.contained);
      assert.equal(outcome.ignitions, active(state).filter(fire => !before.ids.includes(fire.id)).length);
      assert.equal(outcome.resupplied, state.supplies - afterActionsSupplies);
      assert.equal(outcome.ready, state.crewTotal - active(state).filter(fire => fire.crew > 0).length);
      assert.equal(await page.locator("#action-feedback").textContent(), outcome.feedback);
      assert.equal(await page.locator("#announcement").textContent(), outcome.announcement);
      assert.equal(await page.locator("#action-feedback").getAttribute("role"), "status");
      assert.equal(await page.locator("#announcement").getAttribute("aria-live"), "polite");
      const saved = JSON.parse(await page.evaluate(() => localStorage.getItem("fireline-season")));
      const replayed = replay(saved, source.pool).state;
      assert.deepEqual(frontOutcome(replayed), outcome);
      const layout = await page.evaluate(() => {
        const feedback = document.querySelector("#action-feedback");
        const operations = document.querySelector(".operations");
        return {
          horizontalOverflow: document.documentElement.scrollWidth > innerWidth + 1,
          feedbackOverflow: feedback.scrollWidth > feedback.clientWidth + 1,
          operationsScroll: operations.scrollHeight - operations.clientHeight,
        };
      });
      assert.equal(layout.horizontalOverflow, false);
      assert.equal(layout.feedbackOverflow, false);
      if (width > 760) assert.ok(layout.operationsScroll <= 1);
      fronts.push({ ...outcome, ...layout, status: state.status, upgradePending: state.upgradePending });
      if (state.turn === 3) {
        await page.screenshot({ path: `${out}/${width}-${policy}.png`, fullPage: width < 760 });
      }
    }
    assert.equal(state.status, policy === "triage" ? "won" : "lost");
    if (policy === "triage") {
      assert.equal(fronts.length, 12);
      assert.equal(state.upgrades.length, 2);
      assert.equal(fronts.at(-1).resupplied, 0);
    }
    results.push({ width, height, seed, policy, fronts, status: state.status });
  }
  assert.deepEqual(errors, []);
  const sourceHashes = { ...pinned };
  for (const file of ["outcome.js", "main.js", "outcome-check.mjs"]) {
    const name = `web/demo/strategy/${file}`;
    sourceHashes[name] = hash(await fs.readFile(name));
  }
  sourceHashes["web/demo/assets/strategy.js"] = hash(await fs.readFile("web/demo/assets/strategy.js"));
  await fs.writeFile(`${out}/receipt.json`, JSON.stringify({
    checked_utc: new Date().toISOString(), status: "passed", source_sha256: sourceHashes,
    completed_fronts: results.reduce((sum, result) => sum + result.fronts.length, 0),
    outcome_immutable: true, accepted_move_replay_matches: true,
    clipped_reserve_stress_fixture: true,
    external_fonts_blocked: true, results, errors,
    game_rule_changes: false, predictor_fits: 0, qiskit_statevector_executions: 0, hardware_jobs: 0,
    scope: "Actual accepted controls and saved move replay; source arithmetic and laptop/mobile layout with reduced motion and blocked external fonts. Not human enjoyment or real fire-response validation.",
  }, null, 2) + "\n");
  console.log(`Front outcomes agree across ${results.length} complete control-driven seasons.`);
} finally {
  await browser.close();
}

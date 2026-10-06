// Compare the displayed per-fire risk with actual rule-driven front damage.
import assert from "node:assert/strict";
import fs from "node:fs/promises";
import { createHash } from "node:crypto";
import { execFileSync } from "node:child_process";
import { createRequire } from "node:module";
import { createRun, action, advance, active } from "./rules.js";
import { incidentProjection } from "./readout.js";

const hash = bytes => createHash("sha256").update(bytes).digest("hex");
const source = JSON.parse(await fs.readFile("web/demo/assets/context/scenario.json", "utf8"));
const require = createRequire(`${process.env.RUNTIME_NODE_MODULES}/../package.json`);
const { chromium } = require("playwright");
const browser = await chromium.launch({ headless: true, channel: "chrome" });
const out = ".cache/judge-submission/fire-risk";
await fs.mkdir(out, { recursive: true });
const results = [], terminalViews = [], errors = [];
try {
  const page = await browser.newPage({ reducedMotion: "reduce" });
  page.on("pageerror", error => errors.push(error.message));
  await page.route("https://**/*", route => route.abort());
  for (const [width, height] of [[1280, 720], [1024, 768], [390, 844]]) {
    const state = createRun(2, source.pool), moves = [];
    await page.setViewportSize({ width, height });
    await page.goto(`http://127.0.0.1:8790/web/demo/?qa=risk-${width}#season=2`);
    await page.locator("#start").click();
    for (let front = 0; front < 3; front++) {
      const responses = front === 0 ? [[3, "crew"], [1, "water"]]
        : front === 1 ? [[1, "water"], [2, "crew"]] : [[2, "water"], [5, "crew"]];
      for (const [id, kind] of responses) {
        if (!action(state, id, kind)) continue;
        state.selected = id;
        await page.locator(`[data-fire="${id}"]`).click();
        await page.locator(`[data-action="${kind}"]`).click();
        moves.push({ type: "action", id, kind });
        const fire = state.incidents.find(item => item.id === id);
        if (fire.status === "contained") {
          assert.equal(await page.locator("#incident-risk").textContent(), "0.0");
          assert.match(await page.locator("#incident-readout").textContent(), /—after front/);
        }
      }
      const after = structuredClone(state);
      assert.equal(advance(after), true);
      let total = 0;
      for (const fire of active(state)) {
        state.selected = fire.id;
        const projection = incidentProjection(state, fire);
        const resolved = after.incidents.find(item => item.id === fire.id).history.at(-1);
        assert.ok(Math.abs(projection.loss - resolved.damage) < 1e-12);
        assert.equal(projection.pressure, resolved.size);
        total += projection.loss;
        await page.locator(`[data-incident="${fire.id}"]`).click();
        assert.equal(await page.locator("#incident-risk").textContent(), resolved.damage.toFixed(1));
        assert.match(await page.locator("#incident-readout").getAttribute("title"), /Toy fuel .*exposure/);
      }
      assert.ok(Math.abs(total - after.history.at(-1).damage) < 1e-12);
      await page.locator("#advance").click();
      assert.equal(advance(state), true);
      moves.push({ type: "advance" });
      const saved = JSON.parse(await page.evaluate(() => localStorage.getItem("fireline-season")));
      assert.deepEqual(saved.moves, moves);
      results.push({ width, height, completed_front: state.turn,
        projected_total: total, actual_damage: state.history.at(-1).damage,
        displayed_incident_values_match: true });
    }
    assert.equal(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth), true);
    await page.screenshot({ path: `${out}/${width}.png`, fullPage: width < 760 });
    await page.goto(`http://127.0.0.1:8790/web/demo/?qa=risk-ending-${width}#season=7`);
    await page.locator("#start").click();
    let ended = false;
    for (let front = 0; front < 12; front++) {
      if (await page.locator("#upgrade").evaluate(dialog => dialog.open))
        await page.locator("[data-upgrade]").first().click();
      await page.locator("#advance").click();
      if (await page.locator("#debrief").evaluate(dialog => dialog.open)) {
        ended = true;
        break;
      }
    }
    assert.equal(ended, true);
    await page.keyboard.press("Escape");
    assert.equal(await page.locator("#incident-risk").textContent(), "—");
    assert.match(await page.locator("#incident-readout").textContent(), /—season ended/);
    terminalViews.push({ width, height, risk_unavailable: true });
  }
  const terminal = createRun(7, source.pool);
  terminal.status = "lost";
  const original = JSON.stringify(terminal);
  assert.deepEqual(incidentProjection(terminal, terminal.incidents[0]), { pressure: null, loss: null });
  assert.equal(JSON.stringify(terminal), original);
  const contained = createRun(2, source.pool);
  contained.incidents[0].status = "contained";
  assert.deepEqual(incidentProjection(contained, contained.incidents[0]), { pressure: null, loss: 0 });
  assert.deepEqual(errors, []);
  const hashes = {};
  for (const file of ["readout.js", "ui.js", "risk-check.mjs", "rules.js", "scenario.js", "upgrades.js", "session.js"]) {
    const name = `web/demo/strategy/${file}`;
    hashes[name] = hash(await fs.readFile(name));
    if (["rules.js", "scenario.js", "upgrades.js", "session.js"].includes(file))
      assert.equal(hashes[name], hash(execFileSync("git", ["show", `HEAD:${name}`])));
  }
  for (const name of ["web/demo/index.html", "web/demo/assets/strategy.js"])
    hashes[name] = hash(await fs.readFile(name));
  await fs.writeFile(`${out}/receipt.json`, JSON.stringify({
    checked_utc: new Date().toISOString(), status: "passed", source_sha256: hashes,
    results, terminal_views: terminalViews, contained_zero: true, terminal_unavailable: true, errors,
    game_rule_changes: false, predictor_fits: 0, quantum_states: 0, hardware_jobs: 0,
    scope: "Three accepted response/advance fronts at three viewport sizes; selected-fire contributions agree with actual history before combined reserve clamping. Containment and three control-driven terminal views checked. Not measured wildfire risk or a policy-quality study.",
  }, null, 2) + "\n");
  console.log("Per-fire displayed reserve risk matches resolved front history after crew/water responses.");
} finally {
  await browser.close();
}

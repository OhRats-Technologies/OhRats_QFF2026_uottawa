// Actual milestone choices and a read-only ledger, checked against move replay.
import assert from "node:assert/strict";
import fs from "node:fs/promises";
import { createHash } from "node:crypto";
import { execFileSync } from "node:child_process";
import { createRequire } from "node:module";
import { createRun, action, advance, active, available, forecast } from "./rules.js";
import { upgrades, applyUpgrade, upgradeChoices } from "./upgrades.js";
import { replay } from "./session.js";

const hash = bytes => createHash("sha256").update(bytes).digest("hex");
const source = JSON.parse(await fs.readFile("web/demo/assets/context/scenario.json", "utf8"));
const pinned = {};
for (const file of ["rules.js", "scenario.js", "upgrades.js", "session.js"]) {
  const name = `web/demo/strategy/${file}`, bytes = await fs.readFile(name);
  assert.equal(hash(bytes), hash(execFileSync("git", ["show", `HEAD:${name}`])));
  pinned[name] = hash(bytes);
}
const require = createRequire(`${process.env.RUNTIME_NODE_MODULES}/../package.json`);
const { chromium } = require("playwright");
const browser = await chromium.launch({ headless: true, channel: "chrome", args: ["--mute-audio"] });
const out = process.argv[2] ?? ".cache/judge-submission/upgrade-ledger";
await fs.mkdir(out, { recursive: true });
const results = [], errors = [], chosen = new Set();
try {
  const page = await browser.newPage({ reducedMotion: "reduce" });
  page.on("pageerror", error => errors.push(error.message));
  await page.route("https://**/*", route => route.abort());
  for (const [width, height] of [[1280, 720], [1024, 768], [390, 844]]) {
    await page.setViewportSize({ width, height });
    for (const preferred of ["network", "training", "logistics", "precision"]) {
      await page.goto(`http://127.0.0.1:8790/web/demo/?qa=build-${width}-${preferred}#season=2`);
      await page.locator("#start").click();
      let state = createRun(2, source.pool);
      const views = [];
      async function inspect() {
        const saveBefore = await page.evaluate(() => localStorage.getItem("fireline-season"));
        if (width < 760) {
          await page.locator("#guide-open").click();
          await page.locator("#guide-progress").press("Enter");
          assert.equal(await page.locator("#guide").evaluate(dialog => dialog.open), false);
        } else await page.locator('[data-milestone="4"]').press("Enter");
        await page.locator("#progression[open]").waitFor();
        const expected = { crews: String(state.crewTotal), power: state.crewPower.toFixed(2),
          supplies: String(state.resupply), water: `${Math.round((1 - state.dropFactor) * 100)}%` };
        for (const [id, value] of Object.entries(expected))
          assert.equal(await page.locator(`[data-build-effect="${id}"]`).textContent(), value);
        assert.equal(await page.locator(".progression-step.earned").count(), state.upgrades.length);
        for (const item of upgrades) {
          const node = page.locator(`[data-build-upgrade="${item.id}"]`);
          assert.equal(await node.locator("small").textContent(), item.description);
          assert.equal(await node.locator("em").textContent(), state.upgrades.includes(item.id) ? "Equipped" : "Not chosen");
        }
        for (const [index, front] of [4, 8].entries()) {
          const milestone = page.locator(".progression-step").nth(index);
          const selected = upgrades.find(item => item.id === state.upgrades[index]);
          const status = selected ? selected.name : state.status !== "playing" ? "Not earned"
            : state.turn >= front ? "Choice ready" : `In ${front - state.turn} fronts`;
          assert.equal(await milestone.locator("b").textContent(), status);
        }
        assert.equal(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth), true);
        assert.equal(await page.locator("#progression").evaluate(dialog => dialog.scrollWidth <= dialog.clientWidth), true);
        await page.screenshot({ path: `${out}/${width}-${preferred}-${state.turn}.png`, fullPage: false });
        await page.keyboard.press("Escape");
        assert.equal(await page.locator("#progression").evaluate(dialog => dialog.open), false);
        const focus = width < 760 ? "#guide-open" : '[data-milestone="4"]';
        assert.equal(await page.locator(focus).evaluate(element => element === document.activeElement), true);
        assert.equal(await page.evaluate(() => localStorage.getItem("fireline-season")), saveBefore);
        const saved = JSON.parse(saveBefore), replayed = replay(saved, source.pool).state;
        for (const name of ["upgrades", "crewTotal", "crewPower", "resupply", "dropFactor", "integrity", "turn"])
          assert.deepEqual(replayed[name], state[name]);
        const description = await page.locator("#front-detail").textContent();
        assert.doesNotMatch(description, /\bturns?\b/);
        if (state.upgrades.length && [4, 8].includes(state.turn))
          assert.doesNotMatch(description, /choose.*upgrade/i);
        views.push({ front: state.turn, upgrades: [...state.upgrades], effects: expected,
          weather_description: description, save_unchanged: true });
      }
      await inspect();
      while (state.status === "playing") {
        if (state.upgradePending) {
          assert.match(await page.locator("#front-detail").textContent(), /choose.*upgrade/i);
          const choices = upgradeChoices(state);
          const choice = choices.find(item => item.id === preferred) ?? choices[0];
          await page.locator(`[data-upgrade="${choice.id}"]`).click();
          assert.equal(applyUpgrade(state, choice.id), true);
          chosen.add(choice.id);
          await inspect();
        }
        async function respond(fire, kind) {
          await page.locator(`[data-incident="${fire.id}"]`).click();
          await page.locator(`[data-action="${kind}"]`).click();
          assert.equal(action(state, fire.id, kind), true);
        }
        const fires = active(state).sort((a, b) => b.size - a.size);
        for (const fire of fires)
          if (!fire.crew && available(state) > 0 && state.supplies >= 2) await respond(fire, "crew");
        for (const fire of fires)
          if (forecast(state, fire) > 1.1 && state.supplies >= 4) await respond(fire, "water");
        await page.locator("#advance").click();
        assert.equal(advance(state), true);
      }
      await page.keyboard.press("Escape");
      await inspect();
      // Reload the saved season through normal continuation, not fixture injection.
      await page.goto("http://127.0.0.1:8790/web/demo/");
      await page.locator("#debrief[open]").waitFor();
      await page.keyboard.press("Escape");
      await inspect();
      results.push({ width, height, preferred, status: state.status, views });
    }
  }
  assert.deepEqual([...chosen].sort(), upgrades.map(item => item.id).sort());
  assert.deepEqual(errors, []);
  const hashes = { ...pinned };
  for (const name of ["web/demo/strategy/progression.js", "web/demo/strategy/front-detail.js", "web/demo/strategy/ui.js",
    "web/demo/strategy/progression-check.mjs", "web/demo/strategy/styles/progression.css",
    "web/demo/strategy.css", "web/demo/index.html", "web/demo/assets/strategy.js"])
    hashes[name] = hash(await fs.readFile(name));
  await fs.writeFile(`${out}/receipt.json`, JSON.stringify({ checked_utc: new Date().toISOString(),
    status: "passed", source_sha256: hashes, results, chosen_upgrades: [...chosen].sort(), errors,
    predictor_fits: 0, quantum_circuit_executions: 0, hardware_jobs: 0,
    scope: "Read-only upgrade ledger, milestone prompt before/after choices, front-unit descriptions, all four existing effects and saved continuation across three sizes. Game rules/sampling/effects remain unchanged; not a new balance or human-enjoyment study.",
  }, null, 2) + "\n");
  console.log("12 control-driven seasons verify four upgrade effects, milestones, mobile/keyboard ledger and saved continuation.");
} finally {
  await browser.close();
}

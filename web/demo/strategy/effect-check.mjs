// Saved Qiskit vectors verify the added fidelity display; no circuit execution.
import assert from "node:assert/strict";
import fs from "node:fs/promises";
import { createHash } from "node:crypto";
import { execFileSync } from "node:child_process";
import { createRequire } from "node:module";
import { compareChannel } from "./channel-comparison.js";
import { createRun } from "./rules.js";

const hash = bytes => createHash("sha256").update(bytes).digest("hex");
const cache = ".cache/quantum-instrument-v1";
const intent = JSON.parse(await fs.readFile(`${cache}/intent.json`, "utf8"));
const recordsBytes = await fs.readFile(`${cache}/records.json`);
const records = JSON.parse(recordsBytes);
for (const [name, digest] of Object.entries(intent.source_hashes))
  assert.equal(hash(await fs.readFile(name)), digest, name);
assert.equal(records.length, 256);
const key = row => [row.theta, row.phi, row.options.damping, row.options.dephasing].join("/");
const raw = new Map(records.filter(row => row.control === "raw").map(row => [key(row), row]));
assert.equal(raw.size, 64);
assert.equal(new Set(records.map(row => `${key(row)}/${row.control}`)).size, 256);
let fidelityError = 0, vectorError = 0;
for (const row of records) {
  const { theta, phi } = row;
  const input = [Math.sin(theta) * Math.cos(phi), Math.sin(theta) * Math.sin(phi), Math.cos(theta)];
  const result = compareChannel(input, row.options);
  const targets = [[result.before, raw.get(key(row)).qiskit, result.beforeFidelity],
    [result.after, row.qiskit, result.afterFidelity]];
  for (const [actual, expected, fidelity] of targets) {
    vectorError = Math.max(vectorError, ...actual.map((value, index) => Math.abs(value - expected[index])));
    // Computational-basis <psi|rho|psi> from the saved Qiskit output vector.
    const [x, y, z] = expected, c = Math.cos(theta / 2), s = Math.sin(theta / 2);
    const overlap = c * c * (1 + z) / 2 + s * s * (1 - z) / 2
      + c * s * (x * Math.cos(phi) + y * Math.sin(phi));
    fidelityError = Math.max(fidelityError, Math.abs(fidelity - overlap));
    assert.ok(fidelity >= -1e-12 && fidelity <= 1 + 1e-12);
  }
}
assert.ok(vectorError < 1e-12 && fidelityError < 1e-12);
const source = JSON.parse(await fs.readFile("web/demo/assets/context/scenario.json", "utf8"));
const state = createRun(2, source.pool), fire = state.incidents[0];
const theta = Math.PI * (0.15 + 0.7 * Math.tanh(fire.size / 2)), phi = fire.x * Math.PI * 2;
const input = [Math.sin(theta) * Math.cos(phi), Math.sin(theta) * Math.sin(phi), Math.cos(theta)];
const require = createRequire(`${process.env.RUNTIME_NODE_MODULES}/../package.json`);
const { chromium } = require("playwright");
const browser = await chromium.launch({ headless: true, channel: "chrome", args: ["--mute-audio"] });
const out = ".cache/judge-submission/instrument-effects";
await fs.mkdir(out, { recursive: true });
const results = [], errors = [];
try {
  const page = await browser.newPage({ reducedMotion: "reduce" });
  page.on("pageerror", error => errors.push(error.message));
  await page.route("https://**/*", route => route.abort());
  for (const [width, height] of [[1280, 720], [1024, 768], [390, 844]]) {
    await page.setViewportSize({ width, height });
    for (const technique of ["dd", "twirl", "postselect", "readout", "psd", "lowrank"]) {
      await page.goto(`http://127.0.0.1:8790/web/demo/?qa=effect-${width}-${technique}#season=2`);
      await page.locator("#start").click();
      await page.locator("#lab-open").click();
      await page.locator("#instrument-dialog[open]").waitFor();
      const baseline = compareChannel(input, { idle: 0.7, gate: 0.3, damping: 0, dephasing: 0 });
      assert.equal(await page.locator('[data-fidelity="before"]').textContent(), baseline.beforeFidelity.toFixed(3));
      assert.equal(await page.locator('[data-fidelity="after"]').textContent(), baseline.afterFidelity.toFixed(3));
      await page.locator(`[data-technique="${technique}"]`).press("Enter");
      const expected = compareChannel(input, { idle: 0.7, gate: 0.3, damping: 0, dephasing: 0,
        dd: technique === "dd", twirl: technique === "twirl" });
      assert.equal(await page.locator('[data-fidelity="before"]').textContent(), expected.beforeFidelity.toFixed(3));
      assert.equal(await page.locator('[data-fidelity="after"]').textContent(), expected.afterFidelity.toFixed(3));
      const description = await page.locator("#lab-channel svg").getAttribute("aria-label");
      assert.match(description, /Equatorial x\/y projection/);
      assert.match(description, /Fidelity includes the omitted z component/);
      const feedback = await page.locator("#instrument-feedback").textContent();
      assert.match(feedback, /equipped.*Fire response unchanged/);
      assert.match(feedback, technique === "dd" || technique === "twirl" ? /Channel fidelity/
        : technique === "postselect" ? /Samples kept 17\/32; 0 wrong-cardinality/ : /Kernel error/);
      assert.equal(await page.locator("#instrument-close").evaluate(element => element === document.activeElement), true);
      assert.equal(await page.locator(`[data-technique="${technique}"]`).isDisabled(), true);
      const save = JSON.parse(await page.evaluate(() => localStorage.getItem("fireline-season")));
      assert.deepEqual(save.moves, []);
      assert.deepEqual(save.techniques, [technique]);
      assert.equal(await page.locator("#supplies").textContent(), "18");
      assert.equal(await page.locator("#integrity").textContent(), "100");
      assert.equal(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth), true);
      assert.equal(await page.locator("#instrument-dialog").evaluate(dialog => dialog.scrollWidth <= dialog.clientWidth), true);
      await page.screenshot({ path: `${out}/${width}-${technique}.png`, fullPage: width < 760 });
      await page.keyboard.press("Escape");
      assert.equal(await page.locator("#instrument-dialog").evaluate(dialog => dialog.open), false);
      results.push({ width, height, technique,
        initial_equip_pointer_opens: true,
        before_fidelity: expected.beforeFidelity, loadout_fidelity: expected.afterFidelity,
        effect_feedback: feedback, keyboard_focus_and_close: true, game_moves_unchanged: true });
    }
  }
  // Opening the bench refreshes a changed damping control instead of showing stale values.
  await page.goto("http://127.0.0.1:8790/web/demo/?qa=effect-damping#season=2");
  await page.locator("#start").click();
  await page.locator("#lens-toggle").click();
  await page.getByRole("slider", { name: "Amplitude damping", exact: true }).press("Home");
  await page.getByRole("slider", { name: "Amplitude damping", exact: true }).press("PageUp");
  await page.locator("#lab-open").click();
  const noisy = compareChannel(input, { idle: 0.7, gate: 0.3, damping: 0.1, dephasing: 0 });
  assert.equal(await page.locator('[data-fidelity="before"]').textContent(), noisy.beforeFidelity.toFixed(3));
  assert.deepEqual(errors, []);
  const hashes = {};
  for (const name of ["web/demo/strategy/channel-comparison.js", "web/demo/strategy/instruments.js",
    "web/demo/strategy/effect-check.mjs", "web/demo/strategy/styles/research.css",
    "web/demo/strategy/styles/compact.css", "web/demo/assets/strategy.js",
    ...["quantum.js", "diagnostic.js", "rules.js", "scenario.js", "upgrades.js", "session.js"].map(name => `web/demo/strategy/${name}`)]) {
    hashes[name] = hash(await fs.readFile(name));
    if (!name.includes("comparison") && !name.includes("instruments") && !name.includes("effect-check")
      && !name.includes("styles/") && !name.includes("assets/"))
      assert.equal(hashes[name], hash(execFileSync("git", ["show", `HEAD:${name}`])));
  }
  assert.equal(hash(await fs.readFile(`${cache}/records.json`)), hash(recordsBytes));
  await fs.writeFile(`${out}/receipt.json`, JSON.stringify({
    checked_utc: new Date().toISOString(), status: "passed", source_sha256: hashes,
    parent_records_sha256: hash(recordsBytes), saved_qiskit_paths: records.length,
    maximum_vector_error: vectorError, maximum_fidelity_error: fidelityError,
    results, damping_refresh: true, errors, predictor_fits: 0,
    pointer_repair: "Preserve feedback line height when focused Advance blurs; Equip no longer shifts between pointerdown and pointerup.",
    new_quantum_circuit_executions: 0, hardware_jobs: 0,
    scope: "Pure-input fidelity derived from saved Qiskit Bloch vectors; equatorial projection/UI controls and equipment at three sizes. Not a new physics run, device comparison, predictive or universal technique ranking.",
  }, null, 2) + "\n");
  console.log("256 saved Qiskit paths, 18 equipment views, focus/feedback and damping refresh pass.");
} finally {
  await browser.close();
}

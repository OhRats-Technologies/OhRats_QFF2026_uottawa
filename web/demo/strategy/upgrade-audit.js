// Matched offered choices in the fictional game; no policy or rule optimization.
import assert from "node:assert/strict";
import { createHash } from "node:crypto";
import { execFileSync } from "node:child_process";
import { mkdir } from "node:fs/promises";
import { resolve, relative, dirname } from "node:path";
import { createRun, action, advance, active, available, forecast } from "./rules.js";
import { upgradeChoices, applyUpgrade } from "./upgrades.js";

const planPath = "experiments/game_upgrade_tradeoffs.json";
const bytes = await Bun.file(planPath).text();
const plan = JSON.parse(bytes);
const sha = value => createHash("sha256").update(value).digest("hex");
assert.equal(bytes, execFileSync("git", ["show", `HEAD:${planPath}`], { encoding: "utf8" }));
for (const [path, expected] of Object.entries(plan.parent_hashes))
  assert.equal(sha(await Bun.file(path).bytes()), expected, path);
const source = await Bun.file("web/demo/assets/context/scenario.json").json();
const output = resolve(Bun.argv[2] ?? plan.output);
assert.ok(relative(resolve(".cache"), output) && !relative(resolve(".cache"), output).startsWith(".."));
await mkdir(dirname(output), { recursive: true });
await mkdir(output); // Exclusive output: choose a new directory for another collection.
const began = performance.now();

function defaultUpgrade(state) {
  const choices = upgradeChoices(state);
  const selected = plan.upgrade_preference.find(id => choices.some(choice => choice.id === id));
  assert.equal(applyUpgrade(state, selected), true);
}

function respond(state, policy) {
  const crew = () => {
    for (const fire of active(state).sort((a, b) => b.size - a.size))
      if (!fire.crew && available(state) > 0) action(state, fire.id, "crew");
  };
  const water = () => {
    for (const fire of active(state).sort((a, b) => b.size - a.size))
      if (forecast(state, fire) > plan.water_threshold && state.supplies >= 4)
        action(state, fire.id, "water");
  };
  if (policy === "crew_first") { crew(); water(); }
  else { water(); crew(); }
}

function proceed(state, policy, front) {
  while (state.status === "playing" && state.turn < front) {
    if (state.upgradePending) defaultUpgrade(state);
    respond(state, policy);
    assert.equal(advance(state), true);
  }
}

const contexts = [], skipped = [];
function branch(checkpoint, policy, milestone) {
  if (checkpoint.status !== "playing" || !checkpoint.upgradePending) {
    skipped.push({ seed: checkpoint.seed, policy, milestone, status: checkpoint.status, turn: checkpoint.turn });
    return;
  }
  assert.equal(checkpoint.turn, milestone);
  const offers = upgradeChoices(checkpoint).map(choice => choice.id).sort();
  assert.equal(offers.length, 3);
  const weather = sha(JSON.stringify(checkpoint.weather));
  const results = offers.map(id => {
    const state = structuredClone(checkpoint);
    assert.equal(applyUpgrade(state, id), true);
    proceed(state, policy, 12);
    assert.equal(sha(JSON.stringify(state.weather)), weather);
    assert.ok(state.upgrades.includes(id) && ["won", "lost"].includes(state.status));
    return { id, status: state.status, reserve: state.integrity, score: state.score,
      fronts: state.turn, contained: state.contained, spent: state.spent,
      supplies: state.supplies, upgrades: state.upgrades };
  });
  contexts.push({ seed: checkpoint.seed, policy, milestone, weather_sha256: weather,
    checkpoint: { reserve: checkpoint.integrity, supplies: checkpoint.supplies,
      burning: active(checkpoint).length, available_crews: available(checkpoint), upgrades: checkpoint.upgrades },
    offers, results });
}

for (const policy of plan.policies) {
  for (let seed = plan.seed_start; seed < plan.seed_start + plan.seed_count; seed++) {
    const state = createRun(seed, source.pool);
    proceed(state, policy, 4);
    branch(state, policy, 4);
    proceed(state, policy, 8);
    branch(state, policy, 8);
  }
}

const groups = new Map();
for (const context of contexts) {
  for (let i = 0; i < context.results.length; i++) {
    for (let j = i + 1; j < context.results.length; j++) {
      const left = context.results[i], right = context.results[j];
      const key = [context.policy, context.milestone, left.id, right.id].join("/");
      if (!groups.has(key)) groups.set(key, []);
      groups.get(key).push({ reserve: left.reserve - right.reserve,
        won: Number(left.status === "won") - Number(right.status === "won") });
    }
  }
}
const paired = [...groups].map(([key, rows]) => {
  const [policy, milestone, left, right] = key.split("/");
  return { policy, milestone: Number(milestone), left, right, matched_contexts: rows.length,
    mean_reserve_left_minus_right: rows.reduce((sum, row) => sum + row.reserve, 0) / rows.length,
    mean_survival_left_minus_right: rows.reduce((sum, row) => sum + row.won, 0) / rows.length,
    left_higher_reserve: rows.filter(row => row.reserve > 1e-9).length,
    right_higher_reserve: rows.filter(row => row.reserve < -1e-9).length,
    ties: rows.filter(row => Math.abs(row.reserve) <= 1e-9).length };
});
const result = { checked_utc: new Date().toISOString(), plan_sha256: sha(bytes),
  source_hashes: plan.parent_hashes, contexts, skipped,
  game_branches: contexts.length * 3, elapsed_seconds: (performance.now() - began) / 1000,
  new_predictor_fits: 0, quantum_states: 0, hardware_jobs: 0,
  scope: plan.limits };
await Bun.write(`${output}/branches.json`, JSON.stringify(result, null, 2) + "\n");
const summary = { checked_utc: result.checked_utc, status: "passed", plan_sha256: sha(bytes),
  branch_records_sha256: sha(await Bun.file(`${output}/branches.json`).bytes()),
  source_hashes: plan.parent_hashes, seed_start: plan.seed_start, seed_count: plan.seed_count,
  policies: plan.policies, contexts: contexts.length, game_branches: result.game_branches,
  skipped, paired, elapsed_seconds: result.elapsed_seconds,
  offer_checks: "Three actual available choices per reached milestone; exact common weather hash preserved",
  new_predictor_fits: 0, quantum_states: 0, hardware_jobs: 0, scope: plan.limits };
await Bun.write(`${output}/summary.json`, JSON.stringify(summary, null, 2) + "\n");
console.log(JSON.stringify({ contexts: summary.contexts, game_branches: summary.game_branches,
  skipped: skipped.length, elapsed_seconds: summary.elapsed_seconds, output }));

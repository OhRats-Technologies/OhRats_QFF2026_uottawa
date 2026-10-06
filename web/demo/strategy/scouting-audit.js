// Fixed matched game-policy comparison; no predictors, quantum execution or network.
import { createHash } from "node:crypto";
import { mkdir } from "node:fs/promises";
import { resolve, relative } from "node:path";
import {
  createRun,
  action,
  advance,
  active,
  available,
  forecast,
} from "./rules.js";
import { upgradeChoices, applyUpgrade } from "./upgrades.js";

const root = resolve(import.meta.dir, "../../..");
const planPath = resolve(root, "experiments/game_scouting.json");
const plan = await Bun.file(planPath).json();
const sourcePath = resolve(root, "web/demo/assets/context/scenario.json");
const source = await Bun.file(sourcePath).json();
const output = resolve(root, process.argv[2] || plan.output);
if (!output.startsWith(resolve(root, ".cache") + "/"))
  throw new Error("Use an ignored cache output");

const digest = async (path) =>
  createHash("sha256")
    .update(new Uint8Array(await Bun.file(path).arrayBuffer()))
    .digest("hex");
const codePaths = [
  "rules.js",
  "upgrades.js",
  "scenario.js",
  "random.js",
  "scouting-audit.js",
];
const hashes = {
  [relative(root, planPath)]: await digest(planPath),
  [relative(root, sourcePath)]: await digest(sourcePath),
};
for (const name of codePaths) {
  const path = resolve(import.meta.dir, name);
  hashes[relative(root, path)] = await digest(path);
}
const publishedPath = resolve(root, "docs/data/game_scouting.json");
if (await Bun.file(publishedPath).exists()) {
  const previous = await Bun.file(publishedPath).json();
  for (const [path, hash] of Object.entries(previous.hashes)) {
    if (path.endsWith("scouting-audit.js")) continue;
    if (hashes[path] !== hash)
      throw new Error(
        "Historical scouting audit requires pre-pruning rules at ae4cae4",
      );
  }
}
await mkdir(output); // Exclusive evidence namespace; never rewrite an earlier run.
await Bun.write(
  resolve(output, "intent.json"),
  JSON.stringify({ plan, hashes }, null, 2),
);

function chooseUpgrade(state) {
  const choice = upgradeChoices(state).sort(
    (a, b) =>
      plan.upgrade_preference.indexOf(a.id) -
      plan.upgrade_preference.indexOf(b.id),
  )[0];
  applyUpgrade(state, choice.id);
}

function decide(state, policy) {
  const fires = active(state).sort((a, b) => b.size - a.size);
  if (policy === "free_perfect_fuel") {
    for (const fire of fires) fire.scanned = true;
  }
  for (const fire of fires) {
    if (!fire.crew && available(state) > 0) action(state, fire.id, "crew");
  }
  for (const fire of fires) {
    const [low, high] = forecast(state, fire);
    const crossesDecision =
      low <= plan.water_threshold && high > plan.water_threshold;
    const wantsScan =
      policy === "legacy_triage"
        ? fire.size > 0.95
        : policy === "decision_scouting" && crossesDecision;
    if (wantsScan && !fire.scanned && state.supplies >= 5)
      action(state, fire.id, "recon");
    if (
      forecast(state, fire)[1] > plan.water_threshold &&
      state.supplies >= 4
    ) {
      action(state, fire.id, "water");
    }
  }
}

const rows = [];
for (
  let seed = plan.seed_start;
  seed < plan.seed_start + plan.seed_count;
  seed++
) {
  for (const policy of plan.policies) {
    const state = createRun(seed, source.pool);
    while (state.status === "playing") {
      if (state.upgradePending) chooseUpgrade(state);
      decide(state, policy);
      advance(state);
    }
    rows.push({
      seed,
      policy,
      won: state.status === "won",
      reserve: state.integrity,
      spent: state.spent,
      scouting: state.reconCount,
      water: state.drops,
      contained: state.contained,
      turns: state.turn,
    });
  }
}
const mean = (values) =>
  values.reduce((sum, value) => sum + Number(value), 0) / values.length;
const baseline = new Map(
  rows
    .filter((row) => row.policy === "no_scouting")
    .map((row) => [row.seed, row]),
);
const summary = plan.policies.map((policy) => {
  const group = rows.filter((row) => row.policy === policy);
  const differences = group.map(
    (row) => row.reserve - baseline.get(row.seed).reserve,
  );
  return {
    policy,
    win_fraction: mean(group.map((row) => row.won)),
    mean_reserve: mean(group.map((row) => row.reserve)),
    mean_spent: mean(group.map((row) => row.spent)),
    mean_scouting: mean(group.map((row) => row.scouting)),
    mean_water: mean(group.map((row) => row.water)),
    mean_contained: mean(group.map((row) => row.contained)),
    paired_reserve_vs_no_scouting: {
      mean: mean(differences),
      better: differences.filter((value) => value > 1e-9).length,
      worse: differences.filter((value) => value < -1e-9).length,
      same: differences.filter((value) => Math.abs(value) <= 1e-9).length,
    },
  };
});
const result = {
  plan,
  hashes,
  simulated_seasons: rows.length,
  position_pool: source.count,
  policies: summary,
  predictor_fits: 0,
  quantum_states: 0,
  hardware_jobs: 0,
};
await Bun.write(resolve(output, "rows.json"), JSON.stringify(rows));
await Bun.write(
  resolve(output, "summary.json"),
  JSON.stringify(result, null, 2) + "\n",
);
console.log(JSON.stringify(result, null, 2));

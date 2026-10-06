// Compare gameplay strategies under identical exogenous scenarios, not wildfire models.
import {
  createRun,
  action,
  advance,
  active,
  available,
  forecast,
} from "./rules.js";
import { upgradeChoices, applyUpgrade } from "./upgrades.js";
import { random } from "./random.js";
const source = await Bun.file(
  new URL("../assets/context/scenario.json", import.meta.url),
).json();
const pool = source.pool;
const policies = ["idle", "water_only", "crew_only", "random", "triage"];
function chooseUpgrade(state) {
  const preferred = ["training", "logistics", "network", "precision"];
  const choices = upgradeChoices(state);
  applyUpgrade(
    state,
    choices.sort((a, b) => preferred.indexOf(a.id) - preferred.indexOf(b.id))[0]
      .id,
  );
}
function decide(state, policy, rng) {
  const fires = active(state).sort((a, b) => b.size - a.size);
  if (policy === "idle") return;
  if (policy === "water_only") {
    for (const f of fires) if (f.size > 0.8) action(state, f.id, "water");
    return;
  }
  if (policy === "random") {
    for (const f of fires)
      action(
        state,
        f.id,
        ["crew", "water", "hold"][Math.floor(random(rng) * 3)],
      );
    return;
  }
  for (const f of fires) {
    if (!f.crew && available(state) > 0) action(state, f.id, "crew");
  }
  if (policy === "triage") {
    for (const f of fires) {
      if (forecast(state, f) > 1.1 && state.supplies >= 4)
        action(state, f.id, "water");
    }
  }
}
const output = {
  purpose:
    "Game balancing only; actual position pool, pressure-only priority and visible toy fuel and next-front pressure. Fictional dynamics, no trained predictor or quantum simulation.",
  position_pool: source.count,
  seeds: 500,
  policies: [],
};
for (const policy of policies) {
  const results = [];
  for (let seed = 1; seed <= output.seeds; seed++) {
    const state = createRun(seed, pool),
      rng = { rng: seed * 173 + 3 };
    while (state.status === "playing") {
      if (state.upgradePending) chooseUpgrade(state);
      decide(state, policy, rng);
      advance(state);
    }
    results.push({
      won: state.status === "won",
      integrity: state.integrity,
      score: state.score,
      turns: state.turn,
      contained: state.contained,
      spent: state.spent,
    });
  }
  const average = (key) =>
    results.reduce((sum, r) => sum + Number(r[key]), 0) / results.length;
  output.policies.push({
    id: policy,
    win_rate: average("won"),
    mean_integrity: average("integrity"),
    mean_turns: average("turns"),
    mean_contained: average("contained"),
    mean_spent: average("spent"),
    mean_score: average("score"),
  });
}
console.log(JSON.stringify(output, null, 2));

import { clamp } from "./random.js";
import { createScenario } from "./scenario.js";

export const active = (s) => s.incidents.filter((f) => f.status === "burning");
export const busy = (s) => active(s).filter((f) => f.crew > 0).length;
export const available = (s) => s.crewTotal - busy(s);
export const growth = (fuel, weather) =>
  0.12 +
  0.22 * weather.dry +
  0.15 * weather.wind +
  0.18 * fuel -
  0.28 * weather.rain;
export const impact = (size, exposure) => 0.68 * Math.pow(size, 1.2) * exposure;
export const canPlay = (s) => s.status === "playing" && !s.upgradePending;

export function createRun(seed, pool) {
  const scenario = createScenario(seed, pool);
  const state = {
    seed,
    turn: 0,
    status: "playing",
    integrity: 100,
    supplies: 18,
    crewTotal: 2,
    crewPower: 0.9,
    resupply: 2,
    dropFactor: 0.42,
    upgrades: [],
    upgradePending: false,
    selected: 1,
    contained: 0,
    spent: 0,
    drops: 0,
    deployments: 0,
    damage: 0,
    log: [],
    history: [],
    ...scenario,
  };
  spawn(state);
  return state;
}
export function spawn(state) {
  state.incidents
    .filter((f) => f.spawn === state.turn)
    .forEach((f) => {
      f.status = "burning";
      state.log.push({ turn: state.turn, type: "ignition", text: f.name });
    });
}
export function forecast(state, fire) {
  const weather = state.weather[state.turn];
  const pressure = clamp(
    fire.size * (1 + growth(fire.fuel, weather)) -
      (fire.crew ? state.crewPower : 0),
    0,
    9,
  );
  return pressure <= 0.16 ? 0 : pressure;
}
export function action(state, id, kind) {
  if (!canPlay(state)) return false;
  const fire = state.incidents.find((f) => f.id === id);
  if (!fire || fire.status !== "burning") return false;
  const costs = { crew: 2, water: 4 };
  const cost = costs[kind];
  if (cost === undefined || state.supplies < cost) return false;
  if (kind === "crew" && (fire.crew || available(state) <= 0)) return false;
  if (kind === "water" && fire.dropTurn === state.turn) return false;
  state.supplies -= cost;
  state.spent += cost;
  if (kind === "crew") {
    fire.crew = state.turn === 5 ? 3 : 2;
    state.deployments++;
  } else if (kind === "water") {
    fire.size *= state.dropFactor;
    fire.dropTurn = state.turn;
    state.drops++;
    contain(state, fire);
  }
  state.log.push({ turn: state.turn, type: kind, fire: id, text: fire.name });
  return true;
}
function contain(state, fire) {
  if (fire.size <= 0.16 && fire.status === "burning") {
    fire.size = 0;
    fire.status = "contained";
    fire.crew = 0;
    state.contained++;
    state.log.push({
      turn: state.turn,
      type: "contained",
      fire: fire.id,
      text: fire.name,
    });
  }
}
export function advance(state) {
  if (!canPlay(state)) return false;
  const weather = state.weather[state.turn];
  let damage = 0;
  for (const fire of active(state)) {
    fire.size = clamp(
      fire.size * (1 + growth(fire.fuel, weather)) -
        (fire.crew ? state.crewPower : 0),
      0,
      9,
    );
    contain(state, fire);
    const loss = impact(fire.size, fire.exposure);
    damage += loss;
    fire.history.push({ turn: state.turn, size: fire.size, damage: loss });
    if (fire.crew > 0) fire.crew--;
  }
  state.damage += damage;
  state.integrity = clamp(100 - state.damage, 0, 100);
  state.history.push({
    turn: state.turn,
    integrity: state.integrity,
    damage,
    supplies: state.supplies,
    burning: active(state).length,
  });
  state.turn++;
  if (state.integrity <= 40) state.status = "lost";
  else if (state.turn >= 12) state.status = "won";
  if (state.status === "playing") {
    state.supplies = Math.min(26, state.supplies + state.resupply);
    spawn(state);
    state.upgradePending = [4, 8].includes(state.turn);
    if (!active(state).some((f) => f.id === state.selected))
      state.selected = active(state)[0]?.id;
  } else {
    state.score = Math.round(
      state.integrity * 10 + state.contained * 18 + state.supplies * 2,
    );
    state.log.push({
      turn: state.turn,
      type: state.status,
      text: state.status === "won" ? "Season held" : "Season overwhelmed",
    });
  }
  return true;
}

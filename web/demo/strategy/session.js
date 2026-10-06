import { createRun, action, advance } from "./rules.js";
import { applyUpgrade } from "./upgrades.js";

// Bump when season rules or the source position pool change.
const VERSION = "fireline-season-20261006-v2";
const KEY = "fireline-season";

export function replay(snapshot, pool) {
  if (
    snapshot.version !== VERSION ||
    !Number.isInteger(snapshot.seed) ||
    snapshot.seed < 1
  )
    throw new Error("Unsupported season");
  if (!Array.isArray(snapshot.moves) || snapshot.moves.length > 512)
    throw new Error("Invalid move history");
  const state = createRun(snapshot.seed, pool);
  for (const move of snapshot.moves) {
    const accepted =
      move.type === "advance"
        ? advance(state)
        : move.type === "action"
          ? action(state, move.id, move.kind)
          : move.type === "upgrade"
            ? applyUpgrade(state, move.id)
            : false;
    if (!accepted) throw new Error("Move history cannot be replayed");
  }
  const techniques = snapshot.techniques ?? [];
  const credits = 1 + Number(state.turn >= 4) + Number(state.turn >= 8);
  const allowed = ["dd", "twirl", "postselect", "readout", "psd", "lowrank"];
  if (
    !Array.isArray(techniques) ||
    new Set(techniques).size !== techniques.length ||
    techniques.length > credits ||
    techniques.some((id) => !allowed.includes(id))
  )
    throw new Error("Invalid instrument loadout");
  if (state.incidents.some((fire) => fire.id === snapshot.selected))
    state.selected = snapshot.selected;
  return { state, moves: snapshot.moves, techniques };
}

export function loadSession(pool, storage) {
  try {
    const body = (storage ?? globalThis.localStorage).getItem(KEY);
    return body ? replay(JSON.parse(body), pool) : null;
  } catch {
    return null; // Storage may be unavailable; the game remains playable.
  }
}

export function saveSession(state, moves, techniques, storage) {
  const snapshot = {
    version: VERSION,
    seed: state.seed,
    selected: state.selected,
    moves,
    techniques,
  };
  try {
    (storage ?? globalThis.localStorage).setItem(KEY, JSON.stringify(snapshot));
    return true;
  } catch {
    return false;
  }
}

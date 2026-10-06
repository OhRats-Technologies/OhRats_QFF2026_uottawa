import { describe, test, expect } from "bun:test";
import { createRun, action, advance } from "./rules.js";
import { upgradeChoices, applyUpgrade } from "./upgrades.js";
import { loadSession, saveSession } from "./session.js";

const pool = Array.from({ length: 40 }, (_, id) => ({
  x: 0.15 + id / 100,
  y: 0.25,
  cover: 210,
}));
function storage() {
  const values = new Map();
  return {
    getItem: (key) => values.get(key),
    setItem: (key, value) => values.set(key, value),
  };
}

describe("local season replay", () => {
  test("rebuilds resources, delayed crews, selection and instrument credits from accepted moves", () => {
    const state = createRun(2, pool),
      moves = [],
      cache = storage();
    action(state, 3, "crew");
    moves.push({ type: "action", id: 3, kind: "crew" });
    action(state, 3, "water");
    moves.push({ type: "action", id: 3, kind: "water" });
    for (let i = 0; i < 4; i++) {
      advance(state);
      moves.push({ type: "advance" });
    }
    saveSession(state, moves, [], cache);
    expect(loadSession(pool, cache).state.upgradePending).toBe(
      state.upgradePending,
    );
    if (state.upgradePending) {
      const id = upgradeChoices(state)[0].id;
      applyUpgrade(state, id);
      moves.push({ type: "upgrade", id });
    }
    state.selected = 2;
    expect(saveSession(state, moves, ["dd"], cache)).toBe(true);
    const restored = loadSession(pool, cache);
    expect(restored.state).toEqual(state);
    expect(restored.techniques).toEqual(["dd"]);
  });
  test("rejects corrupt, incompatible and impossible histories rather than accepting saved raw state", () => {
    const cache = storage();
    cache.setItem("fireline-season", "broken json");
    expect(loadSession(pool, cache)).toBeNull();
    saveSession(
      createRun(2, pool),
      [{ type: "action", id: 100, kind: "crew" }],
      [],
      cache,
    );
    expect(loadSession(pool, cache)).toBeNull();
    saveSession(createRun(2, pool), [], ["dd", "twirl"], cache);
    expect(loadSession(pool, cache)).toBeNull();
    cache.setItem(
      "fireline-season",
      JSON.stringify({ version: "old", seed: 2, moves: [] }),
    );
    expect(loadSession(pool, cache)).toBeNull();
    cache.setItem(
      "fireline-season",
      JSON.stringify({
        version: "fireline-season-20261006-v1",
        seed: 2,
        moves: [],
      }),
    );
    expect(loadSession(pool, cache)).toBeNull();
  });
  test("storage failure leaves normal gameplay usable", () => {
    const blocked = {
      getItem() {
        throw new Error("disabled");
      },
      setItem() {
        throw new Error("disabled");
      },
    };
    const state = createRun(2, pool);
    expect(loadSession(pool, blocked)).toBeNull();
    expect(saveSession(state, [], [], blocked)).toBe(false);
    expect(action(state, 1, "crew")).toBe(true);
  });
});

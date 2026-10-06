import { describe, test, expect } from "bun:test";
import {
  createRun,
  action,
  advance,
  active,
  available,
  forecast,
} from "./rules.js";
import { applyUpgrade, upgradeChoices } from "./upgrades.js";
const pool = Array.from({ length: 20 }, (_, i) => ({
  x: 0.2 + i * 0.02,
  y: 0.3 + i * 0.018,
  cover: 210,
}));
const run = () => createRun(2026, pool);
function tick(s) {
  if (s.upgradePending) applyUpgrade(s, upgradeChoices(s)[0].id);
  return advance(s);
}

describe("season rules", () => {
  test("identical seed and actions produce identical state", () => {
    const a = run(),
      b = run();
    for (let i = 0; i < 12 && a.status === "playing"; i++) {
      const id = active(a)[0]?.id;
      action(a, id, "crew");
      action(b, id, "crew");
      tick(a);
      tick(b);
    }
    expect(a).toEqual(b);
  });
  test("unaffordable and repeated actions preserve budget", () => {
    const s = run();
    action(s, 1, "water");
    const budget = s.supplies;
    expect(action(s, 1, "water")).toBe(false);
    expect(s.supplies).toBe(budget);
    s.supplies = 0;
    expect(action(s, 2, "crew")).toBe(false);
    expect(s.spent).toBe(4);
  });
  test("crews are constrained, suppress and return", () => {
    const s = run();
    for (const f of active(s)) action(s, f.id, "crew");
    expect(available(s)).toBe(0);
    const sizes = active(s).map((f) => f.size);
    tick(s);
    expect(active(s).every((f) => f.crew <= 1)).toBe(true);
    expect(s.incidents.slice(0, 3).some((f, i) => f.size < sizes[i])).toBe(
      true,
    );
    tick(s);
    expect(available(s)).toBe(2);
  });
  test("visible next-front pressure matches deterministic growth and containment", () => {
    const s = run(),
      fires = active(s);
    action(s, fires[0].id, "crew");
    const predictions = fires.map((f) => forecast(s, f));
    advance(s);
    for (let i = 0; i < fires.length; i++)
      expect(fires[i].size).toBeCloseTo(predictions[i]);
    const before = structuredClone(s);
    expect(action(s, fires[0].id, "recon")).toBe(false);
    expect(s).toEqual(before);
  });
  test("upgrades block advancing, cannot be duplicated, and alter mechanics", () => {
    const s = run();
    s.turn = 4;
    s.upgradePending = true;
    expect(advance(s)).toBe(false);
    const id = upgradeChoices(s)[0].id;
    expect(applyUpgrade(s, id)).toBe(true);
    expect(applyUpgrade(s, id)).toBe(false);
    s.turn = 8;
    s.upgradePending = true;
    expect(upgradeChoices(s).some((u) => u.id === id)).toBe(false);
  });
  test("inaction loses and terminal state cannot consume resources", () => {
    const s = run();
    while (s.status === "playing") tick(s);
    expect(s.status).toBe("lost");
    const end = structuredClone(s);
    expect(action(s, active(s)[0]?.id, "crew")).toBe(false);
    expect(advance(s)).toBe(false);
    expect(s).toEqual(end);
  });
  test("supplies conserve initial, resupply and spending before cap", () => {
    const s = run();
    action(s, 1, "crew");
    advance(s);
    expect(s.supplies).toBe(18 - 2 + 2);
    expect(s.damage).toBeCloseTo(100 - s.integrity);
    expect(s.integrity).toBeLessThanOrEqual(100);
  });
});

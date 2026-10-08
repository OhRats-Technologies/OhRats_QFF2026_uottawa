import { test, expect } from "bun:test";
import data from "./data.json";
import { run } from "./engine.js";
import { fresh, build, record } from "./session.js";
import { candidateSets, scorer, planHints, meetsContract } from "./coach-plan.js";
import { coachPages, FULL_HELP_DEPTH } from "./coach-copy.js";
import { BettyCoach } from "./coach.js";

test("advisor scores agree with the game, preserving its contract and legal inputs", () => {
  for (let round = 0; round < 4; round++) {
    const s = fresh(); s.round = round;
    record(s, run(data, build(s), round));
    const before = JSON.stringify(s), plan = planHints(data, s);
    expect(plan.winner).toBe(true);
    expect(JSON.stringify(s)).toBe(before);
    expect(plan.checked).toBeLessThanOrEqual(240);
    const actual = run(data, plan.recommendation.build, round);
    expect(actual.mae).toBeCloseTo(plan.recommendation.mae, 10);
    expect(meetsContract(actual, s.starts[round])).toBe(true);
    for (const words of coachPages(data, plan).map((text) => text.split(/\s+/).length)) {
      expect(words).toBeGreaterThanOrEqual(10); expect(words).toBeLessThanOrEqual(25);
    }
    const allowed = data.rounds[round].available || data.features.map((_, i) => i);
    expect(candidateSets(data, s).every((f) => f.every((j) => allowed.includes(j)))).toBe(true);
  }
});
test("incomplete, wider and changed settings produce concrete plans in every season", () => {
  for (let round = 0; round < 4; round++) {
    const s = fresh(); s.round = round; record(s, run(data, build(s), round));
    const allowed = data.rounds[round].available || data.features.map((_, i) => i);
    for (const features of [[], [allowed[0]], allowed.slice(0, 6), allowed.slice(0, 10)]) {
      Object.assign(s, { features, width: features.length < 2 ? 4 : features.length,
        angle: Math.PI / 2, C: 10, epsilon: 0.5 });
      const plan = planHints(data, s);
      expect(plan.recommendation.build.features.length).toBeGreaterThanOrEqual(2);
      expect(Number.isFinite(plan.recommendation.mae)).toBe(true);
      const actual = run(data, plan.recommendation.build, round);
      expect(plan.winner).toBe(meetsContract(actual, s.starts[round]));
      for (const text of coachPages(data, plan)) {
        expect(text.split(/\s+/).length).toBeGreaterThanOrEqual(10);
        expect(text.split(/\s+/).length).toBeLessThanOrEqual(25);
      }
    }
  }
});
test("an unset baseline is measured before assistance can claim a win", () => {
  const s = fresh(); s.features = [];
  const p = planHints(data, s);
  expect(p.baseline).toBe(true); expect(p.winner).toBeUndefined();
  expect(p.recommendation.build.features).toEqual([0, 1, 2, 3]);
  expect(coachPages(data, p).length).toBeGreaterThan(FULL_HELP_DEPTH);
});
test("full assistance cannot bypass gradual hints and requesting more hints preserves the build", () => {
  const s = fresh(); s.hintDepths = {};
  let solved = 0, saved = 0;
  const coach = new BettyCoach({ state: () => s, persist: () => saved++, status: () => {} });
  coach.plan = { recommendation: { build: build(s) } };
  coach.pages = Array.from({ length: 7 }, () => "A hint");
  coach.depth = coach.page = 0; coach.solve = () => solved++;
  const before = build(s);
  for (let i = 0; i < FULL_HELP_DEPTH; i++) {
    coach.handle("coach-solve"); expect(solved).toBe(0);
    coach.handle("coach-next");
    expect(build(s)).toEqual(before);
  }
  coach.handle("coach-solve"); expect(solved).toBe(1);
  expect(saved).toBe(FULL_HELP_DEPTH);
  expect(s.hintDepths[s.round]).toBe(FULL_HELP_DEPTH);
});
test("contract boundaries match error and effort routes, and do not manufacture success", () => {
  const first = { mae: 100, effort: 100 };
  expect(meetsContract({ mae: 95, effort: 100 }, first)).toBe(true);
  expect(meetsContract({ mae: 105, effort: 75 }, first)).toBe(true);
  expect(meetsContract({ mae: 105.1, effort: 75 }, first)).toBe(false);
  expect(meetsContract({ mae: 96, effort: 76 }, first)).toBe(false);
  expect(scorer(data, 0)(build(fresh())).mae).toBeCloseTo(run(data, build(fresh()), 0).mae, 10);
});

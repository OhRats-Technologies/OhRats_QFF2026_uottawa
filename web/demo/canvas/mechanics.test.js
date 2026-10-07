import { test, expect } from "bun:test";
import data from "./data.json";
import { sampleCandidates } from "./foundry.js";
import { fresh, record, assessment, setWidth, toggle } from "./session.js";
import { run } from "./engine.js";
test("sampled SQD never invents an unsampled subset; more samples retain the prefix", () => {
  for (const method of ["uniform", "qaoa"]) {
    const a = sampleCandidates(data.rounds[0].objective, 64, 17, method),
      b = sampleCandidates(data.rounds[0].objective, 256, 17, method);
    expect(a.normalization).toBeCloseTo(1, 10);
    expect(a.candidates.reduce((s, r) => s + r.count, 0)).toBe(64);
    expect(b.best.energy).toBeLessThanOrEqual(a.best.energy);
    expect(a.candidates.every((r) => r.features.length === 4)).toBe(true);
    expect(
      a.candidates.every((r) =>
        b.candidates.some((v) => v.mask === r.mask && v.count >= r.count),
      ),
    ).toBe(true);
  }
});
test("both error and resource contracts are attainable and stable beyond log pruning", () => {
  const s = fresh();
  record(s, { mae: 100, effort: 1000, build: { features: [0, 1, 2, 3] } });
  record(s, { mae: 94, effort: 1000, build: { features: [0, 1, 2, 3] } });
  expect(assessment(s).won).toBe(true);
  record(s, { mae: 104, effort: 700, build: { features: [0, 1] } });
  expect(assessment(s).won).toBe(true);
  for (let i = 0; i < 24; i++)
    record(s, { mae: 103, effort: 700, build: { features: [0, 1] } });
  expect(s.history.length).toBe(18);
  expect(assessment(s).cost).toBe(0.3);
});
test("actual repairs produce different outcomes; at least two improvements exist per season", () => {
  for (let round = 0; round < 3; round++) {
    const first = run(
      data,
      { features: [0, 1, 2, 3], angle: Math.PI / 16, C: 1, epsilon: 0.2 },
      round,
    );
    const proposals = [];
    for (const features of [
      [0, 1],
      [2, 3],
      [5, 11],
      [0, 1, 2, 3],
    ])
      for (const angle of [Math.PI / 32, Math.PI / 8, Math.PI / 4])
        for (const C of [0.3, 1, 3, 10]) {
          const r = run(data, { features, angle, C, epsilon: 0.2 }, round);
          if (
            r.mae <= first.mae * 0.95 ||
            (r.effort <= first.effort * 0.75 && r.mae <= first.mae * 1.05)
          )
            proposals.push(r);
        }
    expect(proposals.length).toBeGreaterThanOrEqual(2);
  }
});

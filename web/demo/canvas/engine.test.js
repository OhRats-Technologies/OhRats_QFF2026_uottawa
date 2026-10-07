import { test, expect } from "bun:test";
import data from "./data.json";
import golden from "./golden.json";
import { featureState, fidelity } from "./kernel.js";
import { run } from "./engine.js";
test("ZZ states match independently computed Qiskit amplitudes", () => {
  golden.samples.forEach((x, j) => {
    const s = featureState(x);
    golden.states[j].forEach(([re, im], i) => {
      expect(s.re[i]).toBeCloseTo(re, 10);
      expect(s.im[i]).toBeCloseTo(im, 10);
    });
    expect(fidelity(s, s)).toBeCloseTo(1, 10);
  });
});
test("freeform browser epsilon-SVR matches sklearn on real development rows", () => {
  const r = run(data, golden.build, 2);
  r.gram.forEach((row, i) =>
    row.forEach((v, j) => expect(v).toBeCloseTo(golden.gram[i][j], 10)),
  );
  r.predicted.forEach((v, i) =>
    expect(Math.abs(v - golden.predicted[i])).toBeLessThan(0.08),
  );
  expect(Math.abs(r.quantum.beta.reduce((a, b) => a + b, 0))).toBeLessThan(
    1e-9,
  );
});
test("non-preset and ten-input builds both execute", () => {
  for (const features of [
    [2, 5, 11, 19],
    [0, 1, 2, 3, 10, 11, 12, 13, 14, 15],
  ]) {
    const r = run(data, { ...golden.build, features }, 0);
    expect(r.predicted.length).toBe(4);
    expect(r.predicted.every(Number.isFinite)).toBe(true);
  }
});
import { sectorState } from "./foundry.js";
test("QAOA feasible-sector amplitudes match independent Qiskit RXX/RYY gates", () => {
  const r = sectorState(golden.sector.objective, 4);
  r.masks.forEach((m, i) => {
    expect(r.re[i]).toBeCloseTo(golden.sector.states[m][0], 10);
    expect(r.im[i]).toBeCloseTo(golden.sector.states[m][1], 10);
  });
});
test("2/4/6/10-input SVR controls match sklearn across distinct settings", () => {
  for (const fixture of golden.svr_checks) {
    const r = run(data, fixture.build, fixture.round);
    r.predicted.forEach((v, i) =>
      expect(Math.abs(v - fixture.predicted[i])).toBeLessThan(0.1),
    );
  }
});

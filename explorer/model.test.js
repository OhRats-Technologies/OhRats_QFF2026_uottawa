import { test, expect } from "bun:test";
import { readFileSync } from "node:fs";
import { gunzipSync } from "node:zlib";
import { evolve } from "./model.js";
const html = readFileSync(new URL("index.html", import.meta.url), "utf8");
const packed = html.match(/<script id="payload"[^>]*>([^<]+)<\/script>/)[1];
const data = JSON.parse(gunzipSync(Buffer.from(packed.trim(), "base64")));
test("continuous evolution agrees with every saved time/source/disconnection", () => {
  for (const model of Object.values(data.models))
    for (let source = 0; source < 8; source++)
      for (let k = 0; k < 81; k++) {
        const result = evolve(model.spectral, source, k / 10);
        for (let i = 0; i < 8; i++) {
          expect(
            Math.abs(result.quantum[i] - model.quantum[k][i][source]),
          ).toBeLessThan(5.1e-9);
          expect(
            Math.abs(result.classical[i] - model.classical[k][i][source]),
          ).toBeLessThan(5.1e-9);
        }
      }
});
test("arbitrary between-sample times preserve probability and frozen scale", () => {
  for (const model of Object.values(data.models))
    for (let source = 0; source < 8; source++)
      for (const t of [0.037, 0.219, 1.414, 3.14159, 5.503, 7.999]) {
        const r = evolve(model.spectral, source, t);
        for (const key of ["quantum", "classical"]) {
          expect(Math.abs(r[key].reduce((a, b) => a + b, 0) - 1)).toBeLessThan(
            1e-10,
          );
          expect(Math.min(...r[key])).toBeGreaterThanOrEqual(0);
        }
      }
  const isolated = evolve(data.models["1"].spectral, 1, 3.14159);
  expect(isolated.quantum[1]).toBeCloseTo(1, 12);
  expect(isolated.classical[1]).toBeCloseTo(1, 12);
});
test("analytic two-node interference differs from monotone diffusion", () => {
  const a = Math.SQRT1_2,
    v = Array.from({ length: 8 }, (_, i) =>
      Array.from({ length: 8 }, (_, j) => (i === j ? 1 : 0)),
    );
  v[0][0] = a;
  v[0][1] = a;
  v[1][0] = a;
  v[1][1] = -a;
  const r = evolve(
    { values: [0, 2, 0, 0, 0, 0, 0, 0], vectors: v },
    0,
    Math.PI / 2,
  );
  expect(r.quantum[1]).toBeCloseTo(1, 12);
  expect(r.classical[1]).toBeCloseTo((1 - Math.exp(-Math.PI)) / 2, 12);
});

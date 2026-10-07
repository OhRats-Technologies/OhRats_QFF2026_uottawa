import { prepare } from "./engine.js";
import { featureState, quantumMatrix } from "./kernel.js";
export function preview(data, build, round) {
  if (!build.features.length) return null;
  const p = prepare(data, build, data.rounds[round]);
  const angles = p.x.map((row) =>
    row.map((z) => build.angle * Math.tanh(z / 2)),
  );
  const states = angles.map(featureState),
    gram = quantumMatrix(states),
    off = gram.flatMap((row, i) => row.filter((v, j) => i !== j));
  const state = states.at(-1);
  let x = 0,
    y = 0,
    z = 0;
  for (let j = 0; j < state.re.length; j++) {
    const prob = state.re[j] ** 2 + state.im[j] ** 2;
    z += j & 1 ? -prob : prob;
    if (!(j & 1)) {
      x += 2 * (state.re[j] * state.re[j + 1] + state.im[j] * state.im[j + 1]);
      y += 2 * (state.re[j] * state.im[j + 1] - state.im[j] * state.re[j + 1]);
    }
  }
  return {
    gram,
    angles,
    trainYears: p.train.map((r) => r.year),
    support: [],
    similarity: off.reduce((s, v) => s + v, 0) / off.length,
    bloch: { x, y, z },
  };
}

import { prepare } from "./engine.js";
import { featureState, quantumMatrix } from "./kernel.js";
import { fitSVR, predictSVR } from "./svr.js";
import { angles, build } from "./session.js";

export const meetsContract = (r, first) => r.mae <= first.mae * 0.95 ||
  (r.effort <= first.effort * 0.75 && r.mae <= first.mae * 1.05);
export function scorer(data, round) {
  const cache = new Map();
  return (b) => {
    const key = JSON.stringify([b.features, b.angle]);
    if (!cache.has(key)) {
      const p = prepare(data, b, data.rounds[round]),
        encode = (rows) => rows.map((x) => featureState(x.map((z) => b.angle * Math.tanh(z / 2)))),
        states = encode(p.x);
      cache.set(key, { p, gram: quantumMatrix(states), cross: quantumMatrix(encode(p.cross), states) });
    }
    const { p, gram, cross } = cache.get(key),
      model = fitSVR(gram, p.y, b.C, b.epsilon),
      predictions = predictSVR(model, cross).map((v) => Math.max(0, Math.expm1(v * p.yScale + p.yMean))),
      mae = predictions.reduce((sum, v, i) => sum + Math.abs(v - p.test[i].y), 0) / p.test.length;
    return { build: b, mae, effort: b.features.length *
      (p.train.length * (p.train.length - 1) / 2 + p.test.length * p.train.length) };
  };
}
export function candidateSets(data, s) {
  const round = data.rounds[s.round], allowed = round.available || data.features.map((_, i) => i),
    groups = [], seen = new Set();
  const add = (features) => {
    const f = [...new Set(features)].filter((j) => allowed.includes(j));
    if (![2, 4].includes(f.length)) return;
    const key = f.join(",");
    if (!seen.has(key)) { seen.add(key); groups.push(f); }
  };
  add(s.features);
  Object.values(round.selectors).forEach(add);
  const top = Object.entries(round.objective).sort((a, b) => a[1] - b[1]).slice(0, 6)
    .map(([mask]) => allowed.filter((j) => Number(mask) & (1 << j)));
  top.forEach(add);
  const pool = [...new Set([...s.features, ...top.flat(), ...Object.values(round.selectors).flat()])]
    .filter((j) => allowed.includes(j)).slice(0, 12);
  for (let i = 0; i < pool.length; i++)
    for (let j = i + 1; j < pool.length; j++) add([pool[i], pool[j]]);
  return groups;
}
export function planHints(data, s, progress = () => {}) {
  const score = scorer(data, s.round), first = s.starts?.[s.round] || s.history.find((r) => r.round === s.round);
  if (!first) {
    const b = { features: [0, 1, 2, 3], angle: Math.PI / 16, C: 1, epsilon: 0.2 };
    return { baseline: true, recommendation: score(b), checked: 1 };
  }
  const groups = candidateSets(data, s), seen = new Set(), ranked = [];
  let checked = 0, best;
  const evaluate = (b) => {
    const key = JSON.stringify(b);
    if (seen.has(key) || checked >= 240) return null;
    seen.add(key);
    const r = score(b);
    checked++;
    ranked.push(r);
    if (!best || r.mae < best.mae) best = r;
    if (checked % 8 === 0) progress(checked);
    return meetsContract(r, first) ? r : null;
  };
  let winner;
  for (const f of groups) {
    winner = evaluate({ ...build(s), features: f });
    if (winner) break;
  }
  if (!winner) {
    const promising = [...ranked].sort((a, b) => a.mae - b.mae).slice(0, 8);
    for (const r of promising) {
      for (const angle of angles) {
        winner = evaluate({ ...r.build, angle });
        if (winner) break;
      }
      if (winner) break;
    }
  }
  if (!winner) {
    const promising = [...ranked].sort((a, b) => a.mae - b.mae).slice(0, 5);
    for (const r of promising) {
      for (const C of [0.3, 1, 3, 10]) {
        for (const epsilon of [0.05, 0.2, 0.5]) {
          winner = evaluate({ ...r.build, C, epsilon });
          if (winner) break;
        }
        if (winner) break;
      }
      if (winner) break;
    }
  }
  return { recommendation: winner || best, winner: !!winner, first, checked,
    current: build(s), currentWidth: s.width, round: s.round };
}

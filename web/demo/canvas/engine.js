import { featureState, quantumMatrix, rbfMatrix } from "./kernel.js";
import { fitSVR, predictSVR } from "./svr.js";
const mean = (a) => a.reduce((s, v) => s + v, 0) / a.length;
const sd = (a) => Math.sqrt(mean(a.map((v) => (v - mean(a)) ** 2))) || 1;
const median = (a) => {
  const b = [...a].sort((x, y) => x - y);
  return b.length ? (b[(b.length - 1) >> 1] + b[b.length >> 1]) / 2 : 0;
};
export function prepare(data, build, round) {
  const train = data.rows.filter((r) => r.year <= round.trainEnd);
  const test = data.rows.filter((r) => round.years.includes(r.year));
  const stats = build.features.map((j) => {
    const values = train.map((r) => r.x[j]).filter((v) => v !== null);
    const m = median(values),
      filled = train.map((r) => r.x[j] ?? m);
    return { median: m, mean: mean(filled), sd: sd(filled) };
  });
  const scale = (row) =>
    build.features.map(
      (j, i) => ((row.x[j] ?? stats[i].median) - stats[i].mean) / stats[i].sd,
    );
  const log = train.map((r) => Math.log1p(r.y)),
    yMean = mean(log),
    yScale = sd(log);
  return {
    train,
    test,
    x: train.map(scale),
    cross: test.map(scale),
    y: log.map((v) => (v - yMean) / yScale),
    yMean,
    yScale,
  };
}
export function run(data, build, roundIndex) {
  const round = data.rounds[roundIndex],
    p = prepare(data, build, round);
  const angles = (rows) =>
    rows.map((row) => row.map((z) => build.angle * Math.tanh(z / 2)));
  const trainAngles = angles(p.x),
    states = trainAngles.map(featureState);
  const gram = quantumMatrix(states),
    cross = quantumMatrix(angles(p.cross).map(featureState), states);
  const quantum = fitSVR(gram, p.y, build.C, build.epsilon);
  const distances = p.x
    .flatMap((x, i) =>
      p.x
        .slice(i + 1)
        .map((y) => x.reduce((s, v, j) => s + (v - y[j]) ** 2, 0)),
    )
    .filter((v) => v > 0);
  const gamma = 1 / median(distances),
    rbf = fitSVR(rbfMatrix(p.x, p.x, gamma), p.y, build.C, build.epsilon);
  const inverse = (values) =>
    values.map((v) => Math.max(0, Math.expm1(v * p.yScale + p.yMean)));
  const predicted = inverse(predictSVR(quantum, cross));
  const rival = inverse(predictSVR(rbf, rbfMatrix(p.cross, p.x, gamma)));
  const actual = p.test.map((r) => r.y),
    baseline = mean(p.train.map((r) => r.y));
  const error = (values) => mean(values.map((v, i) => Math.abs(v - actual[i])));
  const off = gram.flatMap((row, i) => row.filter((v, j) => i !== j));
  return {
    build: structuredClone(build),
    round: roundIndex,
    years: round.years,
    actual,
    predicted,
    rival,
    baseline,
    mae: error(predicted),
    rbfMAE: error(rival),
    meanMAE: error(actual.map(() => baseline)),
    gram,
    cross,
    angles: trainAngles,
    trainYears: p.train.map((r) => r.year),
    quantum,
    support: quantum.beta.flatMap((b, i) => (Math.abs(b) > 1e-5 ? [i] : [])),
    similarity: mean(off),
    pairs:
      (p.train.length * (p.train.length - 1)) / 2 +
      p.test.length * p.train.length,
    effort:
      build.features.length *
      ((p.train.length * (p.train.length - 1)) / 2 +
        p.test.length * p.train.length),
  };
}

// Pair-coordinate descent on the convex epsilon-SVR dual, with sum(beta)=0.
export function fitSVR(K, y, C = 1, epsilon = 0.2, tolerance = 1e-8) {
  const n = y.length,
    beta = Array(n).fill(0),
    prediction = Array(n).fill(0);
  let sweeps = 0,
    improvement = Infinity;
  for (; sweeps < 1600 && improvement > tolerance; sweeps++) {
    improvement = 0;
    for (let i = 0; i < n; i++)
      for (let j = i + 1; j < n; j++) {
        const lo = Math.max(-C - beta[i], beta[j] - C);
        const hi = Math.min(C - beta[i], beta[j] + C);
        const h = Math.max(0, K[i][i] + K[j][j] - 2 * K[i][j]);
        const g = prediction[i] - prediction[j] - y[i] + y[j];
        const cuts = [lo, hi, -beta[i], beta[j]]
          .filter((d) => d >= lo && d <= hi)
          .sort((a, b) => a - b);
        const candidates = [...cuts, 0];
        for (let k = 0; k < cuts.length - 1; k++) {
          const mid = (cuts[k] + cuts[k + 1]) / 2;
          const slope =
            g + epsilon * (Math.sign(beta[i] + mid) - Math.sign(beta[j] - mid));
          if (h > 1e-12)
            candidates.push(
              Math.max(cuts[k], Math.min(cuts[k + 1], -slope / h)),
            );
        }
        const delta = (d) =>
          0.5 * h * d * d +
          g * d +
          epsilon *
            (Math.abs(beta[i] + d) +
              Math.abs(beta[j] - d) -
              Math.abs(beta[i]) -
              Math.abs(beta[j]));
        let d = 0,
          best = 0;
        for (const v of candidates)
          if (delta(v) < best) {
            best = delta(v);
            d = v;
          }
        if (best < -1e-14) {
          beta[i] += d;
          beta[j] -= d;
          improvement -= best;
          for (let k = 0; k < n; k++) prediction[k] += d * (K[k][i] - K[k][j]);
        }
      }
  }
  let lower = -Infinity,
    upper = Infinity;
  const free = [];
  for (let i = 0; i < n; i++) {
    const b = y[i] - prediction[i],
      v = beta[i];
    if (v > 1e-6 && v < C - 1e-6) free.push(b - epsilon);
    else if (v < -1e-6 && v > -C + 1e-6) free.push(b + epsilon);
    if (v < C - 1e-6)
      lower = Math.max(lower, b + (v < -1e-6 ? epsilon : -epsilon));
    if (v > -C + 1e-6)
      upper = Math.min(upper, b + (v > 1e-6 ? -epsilon : epsilon));
  }
  const intercept = free.length
    ? free.reduce((s, v) => s + v, 0) / free.length
    : (lower + upper) / 2;
  return { beta, intercept, sweeps, improvement };
}
export const predictSVR = (model, cross) =>
  cross.map(
    (row) =>
      model.intercept +
      row.reduce((sum, value, i) => sum + value * model.beta[i], 0),
  );

// Exact ZZ feature states. Gates follow Qiskit's one-layer, linear ZZFeatureMap.
export function featureState(angles) {
  const n = angles.length,
    size = 1 << n;
  const re = new Float64Array(size).fill(1 / Math.sqrt(size));
  const im = new Float64Array(size);
  const phase = (mask, theta) => {
    const c = Math.cos(theta),
      s = Math.sin(theta);
    for (let b = 0; b < size; b++)
      if (mask(b)) {
        const a = re[b],
          d = im[b];
        re[b] = a * c - d * s;
        im[b] = a * s + d * c;
      }
  };
  angles.forEach((theta, j) => phase((b) => (b >> j) & 1, 2 * theta));
  for (let j = 0; j < n - 1; j++)
    phase(
      (b) => ((b >> j) ^ (b >> (j + 1))) & 1,
      2 * (Math.PI - angles[j]) * (Math.PI - angles[j + 1]),
    );
  return { re, im };
}
export function fidelity(a, b) {
  let re = 0,
    im = 0;
  for (let i = 0; i < a.re.length; i++) {
    re += a.re[i] * b.re[i] + a.im[i] * b.im[i];
    im += a.re[i] * b.im[i] - a.im[i] * b.re[i];
  }
  return Math.min(1, Math.max(0, re * re + im * im));
}
export const quantumMatrix = (a, b = a) =>
  a.map((x) => b.map((y) => fidelity(x, y)));
export function rbfMatrix(a, b = a, gamma = 1) {
  return a.map((x) =>
    b.map((y) =>
      Math.exp(-gamma * x.reduce((s, v, i) => s + (v - y[i]) ** 2, 0)),
    ),
  );
}

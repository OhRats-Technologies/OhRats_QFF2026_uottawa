// One fixed QAOA layer: uniform four-excitation state, diagonal phase, XY ring mixer.
export function sectorState(objective, qubits = 20, method = "qaoa") {
  const masks = Object.keys(objective).map(Number),
    index = new Map(masks.map((m, i) => [m, i]));
  const n = masks.length,
    re = new Float64Array(n).fill(1 / Math.sqrt(n)),
    im = new Float64Array(n);
  const energies = masks.map((m) => objective[m]),
    spread = Math.max(...energies) - Math.min(...energies) || 1;
  if (method === "qaoa") {
    for (let i = 0; i < n; i++) {
      const phase = (-2.5 * energies[i]) / spread;
      re[i] = Math.cos(phase) / Math.sqrt(n);
      im[i] = Math.sin(phase) / Math.sqrt(n);
    }
    for (let bit = 0; bit < qubits; bit++) {
      const next = (bit + 1) % qubits,
        c = Math.cos(0.35),
        s = Math.sin(0.35);
      for (let i = 0; i < n; i++)
        if ((masks[i] >> bit) & 1 && !((masks[i] >> next) & 1)) {
          const j = index.get(masks[i] ^ (1 << bit) ^ (1 << next));
          // Seasons with unavailable signals keep the mixer on available subsets.
          if (j === undefined) continue;
          const a = re[i],
            b = im[i],
            d = re[j],
            e = im[j];
          re[i] = c * a + s * e;
          im[i] = c * b - s * d;
          re[j] = c * d + s * b;
          im[j] = c * e - s * a;
        }
    }
  }
  return { masks, re, im };
}
export function sampleCandidates(objective, shots, seed = 17, method = "qaoa") {
  const { masks, re, im } = sectorState(objective, 20, method),
    n = masks.length;
  const cdf = [];
  let total = 0;
  for (let i = 0; i < n; i++) {
    total += re[i] ** 2 + im[i] ** 2;
    cdf.push(total);
  }
  let state = seed >>> 0;
  const random = () => {
    state = (Math.imul(1664525, state) + 1013904223) >>> 0;
    return state / 2 ** 32;
  };
  const counts = new Map();
  for (let k = 0; k < shots; k++) {
    const r = random() * total;
    let lo = 0,
      hi = n - 1;
    while (lo < hi) {
      const mid = (lo + hi) >> 1;
      if (cdf[mid] < r) lo = mid + 1;
      else hi = mid;
    }
    counts.set(masks[lo], (counts.get(masks[lo]) || 0) + 1);
  }
  const candidates = [...counts]
    .map(([mask, count]) => ({
      mask,
      count,
      energy: objective[mask],
      features: Array.from({ length: 20 }, (_, j) => j).filter(
        (j) => (mask >> j) & 1,
      ),
    }))
    .sort((a, b) => a.energy - b.energy);
  return {
    candidates,
    best: candidates[0],
    shots,
    method,
    normalization: total,
  };
}

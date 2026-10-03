// Exact continuous-time evolution of the eight-dimensional frozen model.
// Classical diffusion and quantum amplitudes share the intact Laplacian scale.
export function evolve(spectral, source, time) {
  const { values, vectors } = spectral;
  const real = Array(8).fill(0),
    imag = Array(8).fill(0),
    classical = Array(8).fill(0);
  for (let k = 0; k < 8; k++) {
    const c = Math.cos(values[k] * time),
      s = -Math.sin(values[k] * time),
      decay = Math.exp(-values[k] * time);
    for (let i = 0; i < 8; i++) {
      const v = vectors[i][k] * vectors[source][k];
      real[i] += v * c;
      imag[i] += v * s;
      classical[i] += v * decay;
    }
  }
  const quantum = real.map((r, i) => r * r + imag[i] * imag[i]);
  const reference = Math.atan2(imag[source], real[source]);
  const phase = real.map((r, i) => Math.atan2(imag[i], r) - reference);
  return { quantum, classical: classical.map((p) => Math.max(0, p)), phase };
}

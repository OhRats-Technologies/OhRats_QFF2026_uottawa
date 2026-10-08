// Sample the live scene above the shoreline into a rippled, palette-limited lake.
const palette = [
  [12, 26, 25], [19, 36, 32], [26, 45, 39], [33, 54, 48],
  [39, 62, 56], [46, 70, 64], [56, 79, 70], [67, 90, 80],
  [81, 102, 91], [91, 113, 99], [56, 57, 50], [72, 67, 56],
  [86, 77, 62], [104, 88, 69], [110, 66, 38], [144, 79, 38],
  [178, 95, 41], [203, 115, 49], [226, 141, 62], [244, 178, 87],
];
const lookup = new Uint8Array(32768);
for (let key = 0; key < lookup.length; key++) {
  const rgb = [(key >> 10) * 8 + 4, ((key >> 5) & 31) * 8 + 4, (key & 31) * 8 + 4];
  let best = Infinity;
  palette.forEach((tone, i) => {
    const distance = rgb.reduce((sum, v, j) => sum + (v - tone[j]) ** 2, 0);
    if (distance < best) { best = distance; lookup[key] = i; }
  });
}
let surface;
export function reflectLake(c, time, shoreline = 95) {
  const w = c.canvas.width, h = c.canvas.height - shoreline,
    scene = c.getImageData(0, 0, w, shoreline).data;
  if (!surface || surface.width !== w || surface.height !== h)
    surface = c.createImageData(w, h);
  const pixels = surface.data;
  for (let y = 0; y < h; y++) {
    const depth = y / h,
      wave = Math.sin(y * 0.49 - time * 1.4) + Math.sin(y * 0.19 + time * 0.8),
      shift = Math.round(wave * (0.5 + depth * 2.5)),
      sy = Math.max(0, Math.min(shoreline - 1,
        Math.round(shoreline - 1 - y * 1.13 + wave * depth * 0.7))),
      reflectivity = 0.77 - depth * 0.15;
    for (let x = 0; x < w; x++) {
      const sx = Math.max(0, Math.min(w - 1, x + shift)),
        source = (sy * w + sx) * 4,
        glint = (x + Math.floor(time * 3) + y * 11) % 29 < 5 && y % 3 === 0 ? 6 : 0,
        r = Math.round(scene[source] * reflectivity + 25 * (1 - reflectivity)),
        g = Math.round(scene[source + 1] * reflectivity + 49 * (1 - reflectivity) + glint),
        b = Math.round(scene[source + 2] * reflectivity + 52 * (1 - reflectivity) + glint),
        tone = palette[lookup[((r >> 3) << 10) | ((g >> 3) << 5) | (b >> 3)]],
        target = (y * w + x) * 4;
      pixels[target] = tone[0]; pixels[target + 1] = tone[1];
      pixels[target + 2] = tone[2]; pixels[target + 3] = 255;
    }
  }
  c.putImageData(surface, 0, shoreline);
}

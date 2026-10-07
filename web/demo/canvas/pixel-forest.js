// Original code-drawn pixel forest for the finish scene: a 320x180 low-res
// canvas with a limited palette, scaled up with crisp square pixels.
export const RES = { w: 320, h: 180, ground: 150 };
let cached = null;
function seeded(seed) {
  return () => {
    seed = (seed * 16807) % 2147483647;
    return seed / 2147483647;
  };
}
function paint() {
  const cv = document.createElement("canvas");
  cv.width = RES.w;
  cv.height = RES.h;
  const c = cv.getContext("2d"),
    px = (x, y, w, h, tone) => {
      c.fillStyle = tone;
      c.fillRect(Math.round(x), Math.round(y), w, h);
    },
    disc = (cx, cy, r, tone) => {
      for (let y = -r; y <= r; y++) {
        const half = Math.floor(Math.sqrt(r * r - y * y));
        px(cx - half, cy + y, half * 2 + 1, 1, tone);
      }
    };
  // Dusk sky: teal to amber bands, two-row checker dither at each seam.
  const sky = ["#11253a", "#173247", "#214456", "#35585f", "#7d5f50", "#b96f3e", "#e58f3f", "#f7b65c"],
    band = 12,
    horizon = 104;
  sky.forEach((tone, i) => px(0, i * band, RES.w, i === sky.length - 1 ? horizon - i * band : band, tone));
  sky.forEach((tone, i) => {
    if (!i) return;
    for (let x = 0; x < RES.w; x++) {
      if ((x + i) % 2 === 0) px(x, i * band - 1, 1, 1, tone);
      if (x % 4 === i % 4) px(x, i * band - 2, 1, 1, tone);
    }
  });
  const rnd = seeded(5);
  for (let i = 0; i < 28; i++) px(rnd() * RES.w, rnd() * 30, 1, 1, rnd() > 0.7 ? "#fff3cf" : "#9fb8c0");
  // Striped retro sun sitting on the far ridge.
  for (let y = -12; y <= 12; y++) {
    if (y > 2 && y % 3 === 0) continue;
    const half = Math.floor(Math.sqrt(144 - y * y));
    px(236 - half, 92 + y, half * 2 + 1, 1, y < -4 ? "#fff1b8" : "#ffd27a");
  }
  // Ridges: lit far mountains, then a darker forested hill.
  const ridge = (base, amp, freq, phase, tone, light, texture) => {
    for (let x = 0; x < RES.w; x++) {
      const y = Math.round(base - amp * (Math.sin(x * freq + phase) * 0.65 + Math.sin(x * freq * 2.3 + phase * 2) * 0.35));
      px(x, y, 1, horizon + 20 - y, tone);
      px(x, y, 1, 1, light);
      if (texture && x % 3 === 0) px(x, y + 2 + (x % 5), 1, 2, texture);
    }
  };
  ridge(90, 18, 0.022, 0.6, "#3a4d63", "#c8743e");
  ridge(100, 9, 0.05, 2.1, "#22403f", "#3f6b55", "#1a3232");
  // Tiered pine: three skirts, outlined, lit on the sun side.
  const pine = (x, base, h, tones) => {
    const [outline, dark, mid, lit] = tones,
      tiers = h > 24 ? 4 : 3,
      tierH = Math.ceil(h / tiers);
    px(x - 1, base - 2, 3, 4, "#3a2a20");
    for (let t = tiers - 1; t >= 0; t--) {
      const top = base - h + t * tierH * 0.8,
        width = Math.round(h * (0.18 + t * 0.12));
      for (let y = 0; y < tierH + 2; y++) {
        const half = Math.round((width * (y + 1)) / (tierH + 2));
        px(x - half - 1, top + y, half * 2 + 3, 1, outline);
        px(x - half, top + y, half * 2 + 1, 1, dark);
        px(x, top + y, half + 1, 1, mid);
        px(x + half - 1, top + y, 1, 1, lit);
        if (y === tierH + 1) px(x - half, top + y, half * 2 + 1, 1, outline);
        else if ((y + t + x) % 4 === 0 && half > 2) px(x + 1, top + y, 1, 1, lit);
      }
    }
  };
  const far = seeded(91);
  for (let x = -3; x < RES.w + 4; x += 5 + Math.floor(far() * 3))
    pine(x, 112, 9 + Math.floor(far() * 7), ["#0f2a28", "#1c4440", "#245650", "#3b7a62"]);
  // Drifting mist over the far treeline, dithered like the painted fog.
  for (let y = 104; y < 113; y++)
    for (let x = (y % 2); x < RES.w; x += y > 107 ? 2 : 4) px(x, y, 1, 1, y > 109 ? "#8fa69f" : "#6f8a86");
  // Lake: banded water, sun column and dark tree reflections near the shore.
  for (let y = 112; y < RES.ground; y++) {
    px(0, y, RES.w, 1, y < 116 ? "#16332f" : y % 3 === 0 ? "#355e6a" : "#28495a");
    if (y > 116 && y % 5 === 0) for (let x = (y * 13) % 23; x < RES.w; x += 23) px(x, y, 4, 1, "#4f7f8a");
    if (y > 116 && y % 2 === 0) {
      const spread = 6 + (y - 116) * 0.6;
      px(236 - spread / 2 + ((y * 5) % 7), y, spread * (0.4 + (y % 3) * 0.2), 1, y % 4 ? "#f2a447" : "#ffd27a");
    }
  }
  // Mirrored far-tree reflections, broken by ripples.
  const mirror = seeded(91);
  for (let x = -3; x < RES.w + 4; x += 5 + Math.floor(mirror() * 3)) {
    const h = 9 + Math.floor(mirror() * 7);
    for (let y = 0; y < h * 0.6; y += 2) px(x - Math.max(0, 2 - y / 3), 113 + y, Math.max(1, 5 - y / 2), 1, "#173a3a");
  }
  // Near pines framing both edges.
  const near = ["#040c09", "#0b2219", "#123424", "#2a6040"];
  for (const [x, h] of [[10, 78], [30, 58], [50, 42], [64, 28], [306, 74], [286, 56], [268, 40], [254, 26]])
    pine(x, RES.ground + 1, h, near);
  // Rounded shoreline rocks with a lit top edge.
  // Flat boulders: wider than tall, dark rim, lit top-right edge.
  const rock = (x, y, r) => {
    const rows = Math.max(2, Math.round(r * 0.75));
    for (let j = -rows; j <= 0; j++) {
      const half = Math.round(r * 1.4 * Math.sqrt(1 - (j / (rows + 1)) ** 2));
      px(x - half - 1, y + j, half * 2 + 3, 1, "#1d2a2a");
      px(x - half, y + j, half * 2 + 1, 1, j < -rows / 2 ? "#6b7a76" : "#4a5755");
      if (j < -rows / 2) px(x + 1, y + j, half - 1, 1, "#8c9a92");
    }
  };
  for (const [x, y, r] of [[24, 149, 5], [42, 146, 8], [60, 149, 5], [78, 150, 3], [206, 150, 4], [222, 148, 6], [262, 147, 8], [282, 149, 5], [300, 146, 7]]) rock(x, y, r);
  // Grass with tufts over stone-studded soil.
  px(0, RES.ground, RES.w, RES.h - RES.ground, "#5a3a26");
  for (let x = 0; x < RES.w; x++) {
    px(x, RES.ground, 1, 3, x % 2 ? "#3a7a38" : "#4a9044");
    px(x, RES.ground + 3, 1, 1, x % 3 ? "#2c6a2e" : "#5a3a26");
    if (x % 6 === 0) px(x, RES.ground - 2, 1, 2, "#4a9044");
    if (x % 6 === 1) px(x, RES.ground - 1, 1, 1, "#62ad54");
    if (x % 23 === 5) px(x, RES.ground - 3, 1, 1, x % 2 ? "#ffe08a" : "#f4ead8");
  }
  for (let y = RES.ground + 14; y < RES.h; y++)
    for (let x = y % 2; x < RES.w; x += y > RES.ground + 22 ? 1 : 2) px(x, y, 1, 1, "#47301f");
  const soil = seeded(7);
  for (let i = 0; i < 46; i++) {
    const x = Math.floor(soil() * RES.w), y = RES.ground + 7 + Math.floor(soil() * (RES.h - RES.ground - 9));
    px(x, y, 3, 2, "#7a5236");
    px(x, y + 2, 3, 1, "#3e2718");
  }
  return cv;
}
// Drifting clouds and a flapping flock live outside the cached scene.
const CLOUDS = [
  {
    x: 46,
    y: 28,
    speed: 1.6,
    parts: [[0, 0, 8], [12, -5, 11], [26, 0, 8], [-10, 3, 5], [36, 3, 5]],
  },
  { x: 158, y: 16, speed: 2.6, parts: [[0, 0, 6], [10, -3, 9], [22, 1, 6]] },
  { x: 276, y: 46, speed: 1.1, parts: [[0, 0, 6], [11, -4, 9], [23, 0, 7]] },
];
const BIRDS = [[188, 52], [198, 47], [206, 55]];
let clouds = null;
// Outlined cloud catching the sunset on its underside, on its own canvas.
function cloudSprite({ x, y, speed, parts }) {
  const edge = (pick, sign) => Math.max(...parts.map((q) => sign * q[pick] + q[2] + 1)),
    left = edge(0, -1),
    top = edge(1, -1),
    cv = document.createElement("canvas");
  cv.width = left + edge(0, 1) + 1;
  cv.height = top + edge(1, 1) + 1;
  const c = cv.getContext("2d"),
    disc = (cx, cy, r, tone) => {
      c.fillStyle = tone;
      for (let j = -r; j <= r; j++) {
        const half = Math.floor(Math.sqrt(r * r - j * j));
        c.fillRect(left + cx - half, top + cy + j, half * 2 + 1, 1);
      }
    };
  for (const [dx, dy, r] of parts) disc(dx, dy, r + 1, "#5a4a5c");
  for (const [dx, dy, r] of parts) disc(dx, dy, r, "#e8a07a");
  for (const [dx, dy, r] of parts) disc(dx, dy - 1, r - 1, "#f2b98e");
  for (const [dx, dy, r] of parts) disc(dx - 1, dy - 3, r - 3, "#fbe0bd");
  return { canvas: cv, left: x - left, top: y - top, speed };
}
// Draws the scene covering W x H, bottom-anchored; returns the ground line y.
export function pixelForest(p, W, H, time = 0) {
  cached ||= paint();
  const k = Math.max(W / RES.w, H / RES.h),
    iw = RES.w * k,
    ih = RES.h * k,
    x = (W - iw) / 2,
    y = H - ih;
  p.c.imageSmoothingEnabled = false;
  p.c.drawImage(cached, x, y, iw, ih);
  // Moving layers step in whole low-res pixels so they stay crisp.
  const low = (lx, ly, lw, lh) =>
    p.rect(x + lx * k, y + ly * k, lw * k, lh * k, "#2a2430");
  clouds ||= CLOUDS.map(cloudSprite);
  for (const cl of clouds) {
    const w = cl.canvas.width,
      span = RES.w + w,
      lx =
        Math.round((((cl.left + w + time * cl.speed) % span) + span) % span) - w;
    p.c.drawImage(
      cl.canvas,
      x + lx * k,
      y + cl.top * k,
      w * k,
      cl.canvas.height * k,
    );
  }
  BIRDS.forEach(([bx0, by0], i) => {
    const span = RES.w + 16,
      bx = Math.round((bx0 + time * 7) % span) - 8,
      by = Math.round(by0 + Math.sin(time * 1.6 + i * 1.3) * 2);
    if (time && Math.floor(time * 5 + i * 0.7) % 2) {
      // Wings up: a small V.
      for (const d of [-2, -1, 1, 2]) low(bx + d, by - Math.abs(d), 1, 1);
      low(bx, by, 1, 1);
    } else {
      // Wings down: a flat glide.
      low(bx - 2, by - 1, 2, 1);
      low(bx, by, 1, 1);
      low(bx + 1, by - 1, 2, 1);
    }
  });
  return y + RES.ground * k;
}

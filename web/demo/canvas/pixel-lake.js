// Original code-drawn pixel version of the Fireline title painting: towering
// spruce and mossy granite on the left, misty forested hills and a calm lake,
// and a burning ridge with a smoke plume on the right. 320x180, crisp pixels.
import { reflectLake } from "./pixel-reflection.js";
const R = { w: 320, h: 180 };
let cached = null;
const seeded = (seed) => () => {
  seed = (seed * 16807) % 2147483647;
  return seed / 2147483647;
};
// Ridge heights shared by the static scene and the animated burn.
const bigHill = (x) =>
  Math.round(80 - 38 * Math.exp(-(((x - 232) / 78) ** 2)) - 3 * Math.sin(x * 0.09));
const farHill = (x) =>
  Math.round(76 - 20 * Math.exp(-(((x - 150) / 70) ** 2)) - 2 * Math.sin(x * 0.2));
function tools(c, rnd) {
  const px = (x, y, w, h, tone) => {
    c.fillStyle = tone;
    c.fillRect(Math.round(x), Math.round(y), Math.max(1, Math.round(w)), Math.max(1, Math.round(h)));
  };
  // Bushy spruce: sawtooth tiers widening downward, jagged tips, rim light.
  const spruce = (x, base, h, [dark, mid, rim]) => {
    const w = Math.max(3, h * 0.34),
      tier = Math.max(3, Math.round(h / 7));
    px(x, base - Math.min(6, h * 0.12), 1, Math.min(6, h * 0.12), "#2a1d14");
    for (let y = 0; y < h * 0.94; y++) {
      const t = y / h,
        inTier = (y % tier) / tier,
        half = Math.max(0, Math.round((w / 2) * (0.08 + 0.92 * t) * (0.35 + 0.65 * inTier) + (rnd() - 0.4) * 3));
      const row = base - h + y;
      const lean = rnd() > 0.85 ? Math.round((rnd() - 0.5) * 4) : 0;
      px(x - half + lean, row, half * 2 + 1, 1, dark);
      if (half > 2) px(x + 1, row, Math.max(1, half - 2), 1, mid);
      if (inTier > 0.8 && half > 1) px(x - half, row, 1, 1, rim);
    }
  };
  // Granite boulder: flat-topped superellipse, cracks, moss and a lit top.
  const boulder = (cx, cy, rx, ry) => {
    for (let j = -ry; j <= ry; j++) {
      const v = Math.abs(j / ry),
        half = Math.round(rx * Math.pow(Math.max(0, 1 - v ** 2.2), 1 / 2.2) - (j < 0 ? ((cx * 3 + j * 5) % 4) : 0));
      const tone = j < -ry + 2 ? "#66705f" : j < -ry * 0.3 ? "#414a43" : "#2d3430";
      px(cx - half - 1, cy + j, half * 2 + 3, 1, "#161c19");
      px(cx - half, cy + j, half * 2 + 1, 1, tone);
    }
    px(cx - rx * 0.2, cy - ry * 0.4, 1, ry * 1.1, "#2a312d");
    px(cx + rx * 0.35, cy - ry * 0.1, 1, ry * 0.9, "#2a312d");
    for (let i = 0; i < rx; i += 2)
      if (rnd() > 0.4) px(cx - rx * 0.7 + i, cy - ry * 0.6 + rnd() * 2, 2, 1, "#56723e");
  };
  return { px, spruce, boulder };
}
function paint() {
  const cv = document.createElement("canvas");
  cv.width = R.w;
  cv.height = R.h;
  const rnd = seeded(29);
  let { px, spruce, boulder } = tools(cv.getContext("2d"), rnd);
  // Dark teal dusk sky with streaky stratus, warmer near the horizon.
  ["#223330", "#2a3b36", "#32443c", "#3a4b41", "#435244"].forEach((tone, i) => px(0, i * 12, R.w, 12, tone));
  for (let i = 0; i < 90; i++) {
    const y = 2 + rnd() * 56,
      x = rnd() * R.w - 20,
      len = 10 + rnd() * 46,
      warm = y > 30 && x < 260 && rnd() > 0.3;
    px(x, y, len, 1, warm ? (y > 44 ? "#d0844e" : "#9a6a4c") : rnd() > 0.5 ? "#6f8274" : "#55685d");
    if (rnd() > 0.4) px(x + 3, y + 1, len * 0.7, 1, warm ? "#7a5440" : "#3e5048");
  }
  // Low sun with a dithered horizon glow.
  for (let y = 36; y < 66; y++)
    for (let x = 0; x < 230; x++) {
      const g = 1 - Math.hypot((x - 104) / 105, (y - 57) / 13);
      if (g > 0.6 || (g > 0.25 && (x + y) % 2 === 0) || (g > 0.05 && (x + y) % 4 === 0))
        px(x, y, 1, 1, g > 0.7 ? "#e28a4a" : g > 0.4 ? "#c06a3c" : "#8a5038");
    }
  for (let j = -4; j <= 4; j++) {
    const half = Math.round(Math.sqrt(16 - j * j) * 1.2);
    px(104 - half, 56 + j, half * 2 + 1, 1, j < 0 ? "#f6b066" : "#e8894a");
  }
  // Far blue mountains, then the misty central forested hill.
  for (let x = 0; x < R.w; x++) {
    const y = Math.round(60 - 4 * Math.sin(x * 0.035 + 1) - 2 * Math.sin(x * 0.09));
    px(x, y, 1, 30, "#3a4b4a");
    px(x, y, 1, 1, "#566868");
  }
  for (let x = 30; x < 270; x++) px(x, farHill(x), 1, 40, "#1e2e2a");
  for (let x = 32; x < 268; x += 2) spruce(x + rnd() * 2, farHill(x) + 3, 5 + rnd() * 6, ["#172723", "#1e302b", "#3a4a3c"]);
  // Big right hill with a forested crown, and the rocky headland beyond.
  for (let x = 286; x < R.w; x++) {
    const y = Math.round(44 - (x - 286) * 0.35);
    px(x, y, 1, 60, "#2a383a");
    if (x % 3 === 0) px(x, y + 4 + (x % 7), 1, 8, "#36464a");
  }
  for (let x = 120; x < 310; x++) px(x, bigHill(x), 1, 60, "#18271f");
  for (let x = 122; x < 306; x += 3) spruce(x + rnd() * 2, bigHill(x) + 3, 5 + rnd() * 5, ["#132119", "#1a2c23", "#2a3a2c"]);
  // Fog banks drifting between the hills.
  const fog = (y0, y1, x0, x1, tone, dense) => {
    for (let y = y0; y < y1; y++)
      for (let x = x0; x < x1; x++) {
        const f = Math.sin(x * 0.045 + y * 0.4) * 0.35 + 0.65 - Math.abs(y - (y0 + y1) / 2) / ((y1 - y0) / 2);
        if (f > 0.25 && (x * 3 + y * 5) % (f > dense ? 2 : 4) === 0) px(x, y, 1, 1, tone);
      }
  };
  fog(66, 82, 30, 300, "#6c7f78", 0.55);
  fog(80, 92, 60, 280, "#86978f", 0.6);
  // Far shore treeline and the small forested island left of centre.
  for (let x = 90; x < 290; x += 3) spruce(x + rnd() * 2, 94, 6 + rnd() * 12, ["#13221f", "#1a2c28", "#24362f"]);
  for (const [x, y, rx, ry] of [[104, 94, 7, 2], [126, 95, 9, 2], [150, 94, 6, 2]]) boulder(x, y, rx, ry);
  // Foreground stays separate: it masks the live reflection, never enters it.
  const foreground = document.createElement("canvas");
  foreground.width = R.w; foreground.height = R.h;
  ({ px, spruce, boulder } = tools(foreground.getContext("2d"), rnd));
  // Right shore: granite under a stand of rim-lit spruce.
  for (const [x, h] of [[244, 24], [254, 34], [264, 22], [276, 40], [288, 30], [300, 44], [314, 34]])
    spruce(x, 99, h, ["#0e1a17", "#16271f", "#b8743e"]);
  for (const [x, y, rx, ry] of [[240, 100, 8, 3], [258, 101, 11, 4], [282, 100, 13, 4], [306, 101, 12, 4]]) boulder(x, y, rx, ry);
  // Left: a dark mossy bank, towering spruce frame and granite boulders.
  for (let x = 0; x < 210; x++) {
    const top = Math.round(136 + ((x / 210) ** 2) * 36);
    px(x, top, 1, R.h - top, x % 3 ? "#1a241e" : "#202c24");
    if (x % 2 === 0) px(x, top - 1 - (x % 3), 1, 2 + (x % 3), (x * 7) % 5 ? "#2f4428" : "#6a5a32");
  }
  // A dense stand along the left shore, rooted on the bank and shrinking eastward.
  const bank = (x) => Math.round(136 + ((x / 210) ** 2) * 36);
  for (let x = 98; x < 196; x += 5) spruce(x + rnd() * 3, bank(x) + 2, 52 - (x - 98) * 0.38 + rnd() * 8, ["#0e1a16", "#152620", "#a9703c"]);
  for (const [x, h] of [[96, 74], [78, 104], [58, 132], [34, 168], [12, 180]])
    spruce(x, 150, h, ["#0b1613", "#12221d", "#b07640"]);
  for (const [x, y, rx, ry] of [[22, 152, 22, 10], [64, 148, 18, 8], [102, 157, 20, 9], [142, 165, 16, 7], [30, 170, 26, 10], [88, 174, 24, 9], [150, 178, 16, 7]])
    boulder(x, y, rx, ry);
  for (let x = 0; x < 190; x += 2) if ((x * 13) % 7 < 3) px(x, 170 + (x % 7), 1, 5, (x % 4 ? "#3a5530" : "#6a5a32"));
  // Small spruce on the near shore, bottom centre.
  for (const [x, h] of [[198, 26], [210, 18], [234, 34], [246, 22]]) spruce(x, 182, h, ["#0e1a17", "#16271f", "#a9703c"]);
  const frame = document.createElement("canvas");
  frame.width = R.w; frame.height = R.h;
  return { scene: cv, foreground, frame, tick: -1 };
}
// Animated burn along the big hill's crown and a billowing plume.
function burn(low, time) {
  const frame = Math.floor(time * 8),
    puff = (cx, cy, r, tone) => {
      for (let j = -r; j <= r; j++) {
        const half = Math.floor(Math.sqrt(r * r - j * j));
        low(cx - half, cy + j, half * 2 + 1, 1, tone);
      }
    };
  for (let i = 0; i < 22; i++) {
    const age = (time * 5 + i * 2.9) % 64,
      r = 2 + Math.floor(age / 5) + (i % 3),
      x = Math.round(222 + (i % 3) * 7 + age * 1.15 + Math.sin(time * 0.6 + i * 1.7) * 4),
      y = Math.round(bigHill(226) - 2 - age * 0.95);
    puff(x, y, r, age < 8 ? "#8a4e30" : age < 22 ? "#6e5546" : age < 42 ? "#5c4c46" : "#4c4446");
    if (age < 30) puff(x - 1, y + r - 2, Math.max(1, r - 3), age < 12 ? "#c06a36" : "#8a5a40");
    if (age > 10) puff(x + 2, y - r + 2, Math.max(1, r - 4), "#7a6a62");
  }
  for (let x = 200; x <= 270; x++) {
    const base = bigHill(x) + 3,
      shape = 1 - Math.abs(x - 236) / 38,
      h = Math.max(1, Math.round((3 + ((x * 5 + frame * 3 + (x % 4) * frame) % 8)) * shape));
    low(x, base - h, 1, h, "#a8432a");
    if (h > 2) low(x, base - h + 1, 1, h - 2, "#e0702c");
    if (h > 4) low(x, base - h + 2, 1, h - 4, "#f6a84a");
    if (h > 6 && (x + frame) % 3 === 0) low(x, base - h + 2, 1, 1, "#ffe08a");
  }
  for (let i = 0; i < 14; i++) {
    const age = (time * 9 + i * 7) % 50;
    low(214 + ((i * 13) % 44) + age * 0.6, bigHill(236) - age * 0.9, 1, 1, i % 2 ? "#ffb653" : "#f6d27a");
  }
}
// Draws the scene covering W x H, centred.
export function pixelLake(p, W, H, time = 0) {
  cached ||= paint();
  const tick = Math.floor(time * 24);
  if (cached.tick !== tick) {
    const c = cached.frame.getContext("2d", { willReadFrequently: true });
    c.clearRect(0, 0, R.w, R.h);
    c.drawImage(cached.scene, 0, 0);
    burn((lx, ly, lw, lh, tone) => {
      c.fillStyle = tone;
      c.fillRect(Math.round(lx), Math.round(ly), Math.max(1, Math.round(lw)), Math.max(1, Math.round(lh)));
    }, tick / 24);
    reflectLake(c, tick / 24);
    c.drawImage(cached.foreground, 0, 0);
    cached.tick = tick;
  }
  const k = Math.max(W / R.w, H / R.h),
    x = (W - R.w * k) / 2,
    y = (H - R.h * k) / 2;
  p.c.save();
  p.c.imageSmoothingEnabled = false;
  p.c.drawImage(cached.frame, x, y, R.w * k, R.h * k);
  p.c.restore();
}

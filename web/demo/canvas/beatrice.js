// Original code-drawn pixel portrait; Beatrice is a fictional Fireline guide.
// Idle motion is driven by time (seconds); time 0 (reduced motion) is static.
const within = (t, period, start, length) =>
  t > 0 && (t % period) - start >= 0 && (t % period) - start < length;

// Per-view step memory: a forward step starts a hop, and fire-related
// lesson text has Betty light her drip torch.
const seen = new Map();
const fiery = /\bfires?\b|wildfire|burn|flame|blaze/i;
export function bettyCue(view, step, time, text) {
  const last = seen.get(view) ?? { step, jumpAt: -1, fireAt: time };
  if (step !== last.step) {
    if (step > last.step) last.jumpAt = time;
    last.fireAt = time;
    last.step = step;
  }
  seen.set(view, last);
  // The opening step greets: a wave first, then the torch.
  return {
    jumpAt: last.jumpAt,
    fire: fiery.test(text),
    fireAt: last.fireAt,
    greet: step === 0,
  };
}

export function beatrice(p, x, y, size, time = 0, cue = {}) {
  const c = p.c,
    t = time,
    hop = t && cue.jumpAt >= 0 ? (t - cue.jumpAt) / 0.5 : 1,
    lift = hop >= 0 && hop < 1 ? Math.round(Math.sin(Math.PI * hop) * 12) : 0;
  c.save();
  c.translate(x, y);
  c.scale(size / 52, size / 52);
  c.translate(0, -lift);
  const ink = "#112429",
    fur = "#8f563c",
    light = "#bf8150",
    gold = "#ffb653";
  const block = (x, y, w, h, color) => p.rect(x, y, w, h, color);
  // Whole-pixel offsets keep every motion on the portrait's grid.
  const breath = t && Math.sin(t * 2.4) > 0.35 ? 1 : 0,
    sway = t ? Math.round(Math.sin(t * 3.1) * 1.4) : 0,
    thump = within(t, 9, 4, 0.5) ? (Math.floor(t * 8) % 2 ? -2 : 0) : 0,
    blink = within(t, 4.3, 0, 0.14) || within(t, 12.9, 8.88, 0.12),
    twitch = within(t, 5.7, 2.1, 0.22) ? -1 : 0,
    lead = cue.greet ? 1.6 : 0,
    greeting = !!(cue.greet && t && t - cue.fireAt < lead),
    torch = !!cue.fire && !greeting,
    waving = greeting || torch || within(t, 7.5, 1, 1.5),
    wave = !torch && waving && Math.floor(t * 6) % 2 ? 1 : 0,
    glint = within(t, 6.2, 3, 0.7) ? ((t % 6.2) - 3) / 0.7 : -1,
    tap = within(t, 3.4, 1.8, 0.6) && Math.floor(t * 10) % 2 ? 1 : 0;
  // Broad, crosshatched tail behind the jacket; it sways and thumps.
  block(34 + sway, 31 + thump, 14, 18, ink);
  block(37 + sway, 33 + thump, 9, 15, "#633e32");
  for (let j = 0; j < 4; j++) {
    block(37 + sway, 35 + thump + j * 3, 9, 1, "#9b6644");
    block(38 + sway + j * 2, 33 + thump, 1, 15, "#3b302c");
  }
  block(12, 44, 10, 7, ink);
  block(27, 44, 10, 7, ink);
  block(10, 49, 13, 3, "#385353");
  block(27, 49, 13, 3, "#385353");
  block(10, 29, 29, 18, ink);
  block(13, 29, 23, 16, "#d37c31");
  block(12, 34, 25, 3, gold);
  block(15, 39, 19, 3, "#e3d7a1");
  block(23, 31, 2, 14, "#75492e");
  if (waving) {
    // Raised sleeve and paw beside the helmet, rocking side to side.
    block(4, 22, 9, 12, ink);
    block(5, 23, 7, 10, "#d37c31");
    block(5, 27, 7, 2, gold);
  } else {
    block(7, 29, 7, 11, "#d37c31");
    block(6, 38, 8, 5, fur);
  }
  block(34, 29, 7, 9, "#d37c31");
  block(35, 35, 7, 5, light);
  // Rounded cheeks, ears and muzzle, all on the same pixel grid.
  c.translate(0, breath);
  block(11, 10, 28, 21, ink);
  block(8, 12 + twitch, 7, 8, fur);
  block(35, 12, 7, 8, fur);
  block(14, 12, 22, 15, fur);
  block(11, 20, 28, 8, fur);
  block(14, 26, 22, 5, light);
  block(16, 20, 18, 8, light);
  block(22, 20, 7, 4, ink);
  block(16, 16, 4, blink ? 1 : 4, ink);
  block(31, 16, 4, blink ? 1 : 4, ink);
  if (!blink) {
    block(17, 16, 1, 1, "#f6e9c7");
    block(32, 16, 1, 1, "#f6e9c7");
  }
  block(22, 26, 4, 5, "#f9e7b3");
  block(27, 26, 4, 5, "#f9e7b3");
  // Copper firefighter helmet, with a simple fictional chevron crest.
  block(12, 4, 26, 10, ink);
  block(15, 3, 20, 10, gold);
  block(18, 1, 14, 3, "#f3c46a");
  block(25, 3, 3, 10, "#d18035");
  block(8, 12, 34, 3, ink);
  block(10, 11, 30, 3, gold);
  block(20, 5, 10, 8, "#214345");
  block(23, 6, 4, 2, "#f4d385");
  block(24, 8, 2, 3, "#f4d385");
  // A brief highlight sweeps across the helmet.
  if (glint >= 0) {
    const gx = 10 + Math.floor(glint * 28);
    block(gx, 11, 2, 1, "#fff3cf");
    if (gx > 15 && gx < 33 && (gx < 20 || gx > 29))
      block(gx, 4, 1, 2, "#fff3cf");
  }
  c.translate(0, -breath);
  if (torch) {
    // Drip-torch wand held up; the flame grows in, then flickers.
    const grow = t
        ? Math.min(1, Math.max(0, (t - cue.fireAt - lead) / 0.4))
        : 1,
      f = t ? Math.floor(t * 9) % 3 : 0,
      fh = Math.round(11 * grow),
      top = 6 - fh;
    block(3, 5, 4, 9, ink);
    block(4, 6, 2, 8, "#7a8a86");
    if (fh > 0) {
      c.fillStyle = "#ff8a3c26";
      c.beginPath();
      c.arc(5, top + fh / 2, 4 + fh * 0.6, 0, Math.PI * 2);
      c.fill();
      block(1 + (f === 1 ? 1 : 0), top + 3, 8, fh - 3, "#ec6f56");
      block(2 + (f === 2 ? 1 : 0), top + 1, 6, fh - 3, "#ff9b3d");
      block(3 + (f === 0 ? 1 : 0) - (f === 1 ? 1 : 0), top, 3, fh - 4, gold);
      if (fh > 6) block(4, top + fh - 5, 2, 3, "#fff3cf");
      if (f === 2) block(7, top - 2, 1, 1, "#ff9b3d");
      if (f === 0) block(2, top - 1, 1, 1, "#ec6f56");
    }
  }
  if (waving) {
    // The raised paw sits in front of the ear so the wave reads clearly.
    block(wave, 13, 10, 10, ink);
    block(1 + wave, 14, 8, 8, fur);
    block(2 + wave, 15, 1, 3, light);
    block(4 + wave, 14, 1, 3, light);
    block(6 + wave, 14, 1, 3, light);
    block(3 + wave, 19, 4, 2, light);
  }
  // Clipboard: the engineering side of a forest-fire workshop.
  block(35, 35, 12, 15, ink);
  block(37, 37, 8, 11, "#afc2a1");
  block(39, 35, 4, 3, "#67847a");
  for (let j = 0; j < 3; j++) block(38, 40 + j * 2, 6, 1, "#56776c");
  // Pencil tapping the clipboard.
  block(43 + tap, 39 - tap, 2, 7, ink);
  block(44 + tap, 40 - tap, 1, 4, gold);
  block(44 + tap, 44 - tap, 1, 1, "#ec6f56");
  c.restore();
}

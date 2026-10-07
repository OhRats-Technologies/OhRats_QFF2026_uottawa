import { color } from "./paint.js";
import { sphere } from "./instruments.js";
import { foundryNote } from "./foundry-help.js";
export function menu(p, s, assets, on, W, H, time) {
  p.rect(0, 0, W, H, p.c.createPattern(assets.metal, "repeat"));
  p.frame(6, 6, W - 12, H - 12);
  const mobile = W < 700,
    xx = mobile ? 20 : W * 0.06,
    yy = mobile ? H * 0.05 : H * 0.12,
    fw = mobile ? W - 40 : W * 0.6,
    fh = mobile ? Math.min(H * 0.37, Math.max(120, H - 410)) : H * 0.71;
  p.frame(xx, yy, fw, fh);
  p.screen(xx + 12, yy + 12, fw - 24, fh - 24);
  const c = p.c;
  c.save();
  c.beginPath();
  c.rect(xx + 15, yy + 15, fw - 30, fh - 30);
  c.clip();
  c.drawImage(assets.forest, xx + 15, yy + 15, fw - 30, fh - 30);
  // Original transparent PNG is retained. Its outer padding is excluded from
  // the canvas source rectangle, leaving the plaque's bevel and shadow intact.
  const logoW = Math.min(fw * 0.5, (fh - 48) * 2078 / 510),
    logoH = logoW * 510 / 2078,
    logoX = xx + (fw - logoW) / 2,
    logoY = yy + 22;
  c.imageSmoothingEnabled = false;
  c.drawImage(assets.logo, 46, 102, 2078, 510,
    Math.round(logoX), Math.round(logoY), Math.round(logoW), Math.round(logoH));
  c.imageSmoothingEnabled = true;
  p.scan(xx + 15, yy + 15, fw - 30, fh - 30);
  if (time)
    for (let j = 0; j < 30; j++) {
      const ex = xx + 30 + ((j * 53) % Math.max(1, fw - 60)),
        ey = yy + fh - 30 - ((time * 15 + j * 31) % (fh * 0.65));
      p.rect(ex, ey, 2, 3, j % 3 ? "#f8b45a44" : "#ffc574aa");
    }
  c.restore();
  const bx = mobile ? 24 : W * 0.71,
    by = mobile ? yy + fh + 22 : H * (H < 500 ? 0.12 : 0.24),
    bw = mobile ? W - 48 : W * 0.23;
  const heading = s.finished ? "WORKSHOP COMPLETE" : "BUILD. TEST. REPAIR.";
  p.text(
    heading,
    bx,
    by,
    Math.min(19, bw / (heading.length * 0.62)),
    color.amber,
  );
  p.text(
    s.finished ? "Three seasons. Better engines." : "Beat your first engine.",
    bx,
    by + 33,
    13,
    color.mint,
  );
  p.button(
    "continue",
    s.attempts ? "CONTINUE ▶" : "START ENGINE ▶",
    bx,
    by + 74,
    bw,
    54,
    () => on("start"),
    { tone: "hot" },
  );
  p.button("new", "NEW RUN", bx, by + 142, bw, 45, () => on("new"));
  p.button(
    "menu-sound",
    on.audio.enabled ? "MUSIC ON ♫" : "MUSIC OFF ♪",
    bx,
    by + 201,
    bw,
    45,
    () => on("sound"),
    { active: on.audio.enabled },
  );
  p.button("menu-help", "BETTY’S GUIDE", bx, by + 260, bw, 40, () =>
    on("help"),
  );
  if (!mobile) {
    const top = by + 320,
      available = H - 22 - top,
      radius = Math.min(52, (available - 40) / 2, bw / 2 - 18);
    if (radius >= 24) {
      const cy = top + radius + 10;
      sphere(p, bx + bw / 2, cy, radius, 0.6, time);
      p.text("EMBER RELAY", bx + bw / 2, cy + radius + 23, 10, color.dim, "center");
    }
  }
}
export function foundry(p, s, data, on, W, H) {
  p.rect(0, 0, W, H, "#031218ec");
  const mobile = W < 920,
    w = Math.min(W - 24, 1030),
    h = Math.min(H - 24, 650),
    x = (W - w) / 2,
    y = (H - h) / 2;
  p.frame(x, y, w, h, "SUBSET FOUNDRY");
  p.button("close-foundry", "×", x + w - 59, y + 14, 34, 30, () =>
    on("foundry"),
  );
  const modes = [
    ["mi", "MI"],
    ["exact", "EXACT"],
    ["qaoa", "QAOA + SQD"],
    ["uniform", "UNIFORM"],
  ];
  modes.forEach(([id, label], i) =>
    p.button(
      `method-${id}`,
      label,
      x + 24 + (i * (w - 48)) / 4,
      y + 55,
      (w - 48) / 4 - 8,
      37,
      () => on("sample", id),
      { active: s.sample?.method === id },
    ),
  );
  const compact = h < 500,
    note = foundryNote(
      p,
      s.sample?.method,
      x + 24,
      y + 100,
      w - 48,
      compact,
      Object.keys(data.rounds[s.round].objective).length,
    );
  if (!s.sample) {
    p.text(
      "CHOOSE A CARTRIDGE",
      x + w / 2,
      y + 100 + note + (h - 100 - note) / 2,
      18,
      color.amber,
      "center",
    );
    return;
  }
  // Candidate rows fill the space between the note and the signal names.
  const top = y + 112 + note,
    first = compact ? 24 : 32,
    step = compact ? 38 : 49,
    room = y + h - (compact ? 147 : 156) - 12 - (top + first),
    fit = Math.max(1, Math.min(compact ? 2 : 4, Math.floor(room / step) + 1)),
    rows = s.sample.candidates.slice(0, fit),
    listW = mobile ? w - 48 : w * 0.44;
  p.text(
    s.sample.shots
      ? `${s.sample.shots} SHOTS · ${s.sample.candidates.length} UNIQUE`
      : "SAVED TRAINING SELECTOR",
    x + 24,
    top,
    12,
    color.dim,
  );
  rows.forEach((r, i) => {
    const py = top + first + i * step;
    p.button(
      `candidate-${i}`,
      `${i === 0 ? "★" : "○"} ${r.features.map((j) => j + 1).join(" / ")}   ${r.energy.toFixed(3)}`,
      x + 24,
      py,
      listW,
      compact ? 31 : 39,
      () => on("candidate", i),
      { active: s.candidate === i },
    );
  });
  const selected = rows[Math.min(s.candidate || 0, rows.length - 1)];
  if (!mobile) {
    const sx = x + w * 0.53,
      sy = top + 25,
      side = Math.min(w * 0.36, h * 0.43),
      u = side / 4;
    p.screen(sx - 8, sy - 8, side + 16, side + 16);
    for (let i = 0; i < 4; i++)
      for (let j = 0; j < 4; j++) {
        p.rect(
          sx + j * u,
          sy + i * u,
          u - 2,
          u - 2,
          i === j ? `hsl(26 69% ${25 + i * 7}%)` : "#0b2224",
        );
        p.text(
          i === j ? rows[i]?.energy.toFixed(3) || "—" : "0",
          sx + (j + 0.5) * u,
          sy + (i + 0.5) * u,
          13,
          i === j ? color.amber : color.dim,
          "center",
        );
      }
    p.text("SAMPLED HAMILTONIAN", sx, sy + side + 30, 11, color.dim);
  }
  const names = selected.features.map((j) => data.features[j].label);
  names.forEach((name, i) =>
    p.text(
      name,
      x + 24,
      y + h - (compact ? 147 : 156) + i * (compact ? 17 : 21),
      13,
      color.mint,
    ),
  );
  p.button(
    "apply",
    "PATCH SUBSET ▶",
    x + w - (mobile ? w - 48 : 250) - 24,
    y + h - 68,
    mobile ? w - 48 : 250,
    42,
    () => on("apply"),
    { tone: "hot" },
  );
  if (s.sample.shots && !mobile) {
    p.button("more-shots", "256 SHOTS", x + 24, y + h - 66, 150, 36, () =>
      on("more-shots"),
    );
    p.text(
      "DIAGONAL SQD · LOWEST SAMPLED ENERGY",
      x + w * 0.53,
      y + h - 130,
      10,
      color.dim,
    );
  }
}

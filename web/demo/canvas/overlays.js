import { color, pixelTitle } from "./paint.js";
import { sphere } from "./instruments.js";
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
  const scale = Math.min(mobile ? 7 : 12, (fw - 60) / 40);
  pixelTitle(p, "FIRELINE", xx + 30, yy + 40, scale);
  p.text(
    "AN ONTARIO QUANTUM WORKSHOP",
    xx + 33,
    yy + 50 + scale * 7,
    mobile ? 10 : 13,
    color.mint,
  );
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
  p.text(
    s.finished ? "WORKSHOP COMPLETE" : "BUILD. TEST. REPAIR.",
    bx,
    by,
    19,
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
    sphere(p, bx + bw / 2, H * 0.78, 52, 0.6, time);
    p.text("EMBER RELAY", bx + bw / 2, H * 0.88, 10, color.dim, "center");
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
  if (!s.sample) {
    p.text(
      "CHOOSE A CARTRIDGE",
      x + w / 2,
      y + h / 2,
      18,
      color.amber,
      "center",
    );
    return;
  }
  const compact = h < 500,
    rows = s.sample.candidates.slice(0, compact ? 2 : 4),
    listW = mobile ? w - 48 : w * 0.44,
    top = y + 112;
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
    const py = top + (compact ? 24 : 32) + i * (compact ? 38 : 49);
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
  const selected = rows[s.candidate || 0];
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

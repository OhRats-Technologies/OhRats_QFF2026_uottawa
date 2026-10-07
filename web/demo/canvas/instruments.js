import { color } from "./paint.js";
export function mapPanel(p, box, assets, time, hover) {
  const { x, y, w, h } = box;
  p.frame(x, y, w, h, "ONTARIO");
  const mx = x + 18,
    my = y + 50,
    mw = w - 36,
    mh = h - 102;
  p.screen(mx, my, mw, mh);
  const ratio = Math.min((mw - 16) / 1118, (mh - 16) / 1200),
    iw = 1118 * ratio,
    ih = 1200 * ratio,
    ix = mx + (mw - iw) / 2,
    iy = my + (mh - ih) / 2;
  if (assets.cover) p.c.drawImage(assets.cover, ix, iy, iw, ih);
  const data = assets.map;
  if (data) {
    for (const point of data.points) {
      const px = ix + point.x * ratio,
        py = iy + point.y * ratio;
      const r = point.ha >= 100 ? 2.5 : 1;
      p.circle(px, py, r, point.ha >= 100 ? "#ffbd66cc" : "#c7794466");
    }
    const focused =
      hover &&
      data.points.find(
        (pt) =>
          Math.hypot(ix + pt.x * ratio - hover.x, iy + pt.y * ratio - hover.y) <
          7,
      );
    if (focused) {
      const px = ix + focused.x * ratio,
        py = iy + focused.y * ratio;
      p.circle(px, py, 7, "#00000000", color.amber);
      p.text(
        `${focused.ha.toFixed(1)} ha`,
        mx + 10,
        my + mh - 16,
        13,
        color.amber,
      );
    }
  }
  p.scan(mx, my, mw, mh);
  p.text("COVER + FIRE RECORDS · 2021", x + 24, y + h - 31, 11, color.dim);
}
export function matrixPanel(p, box, result, time, hover) {
  const { x, y, w, h } = box;
  p.frame(x, y, w, h, "KERNEL ENGINE");
  const side = Math.min(w - 58, h - 100),
    sx = x + (w - side) / 2,
    sy = y + 55;
  p.screen(sx - 7, sy - 7, side + 14, side + 14);
  if (result) {
    const n = result.gram.length,
      u = side / n;
    result.gram.forEach((row, i) =>
      row.forEach((v, j) =>
        p.rect(
          sx + j * u,
          sy + i * u,
          u - 0.6,
          u - 0.6,
          `hsl(26 75% ${7 + v * 57}%)`,
        ),
      ),
    );
    const a = Math.floor((hover?.x - sx) / u),
      b = Math.floor((hover?.y - sy) / u);
    if (a >= 0 && a < n && b >= 0 && b < n) {
      p.line(
        [
          [sx + a * u, sy + b * u],
          [sx + (a + 1) * u, sy + b * u],
          [sx + (a + 1) * u, sy + (b + 1) * u],
          [sx + a * u, sy + (b + 1) * u],
          [sx + a * u, sy + b * u],
        ],
        color.mint,
        2,
      );
      p.text(
        `${result.trainYears[b]} × ${result.trainYears[a]}   ${result.gram[b][a].toFixed(3)}`,
        x + w / 2,
        y + h - 34,
        12,
        color.amber,
        "center",
      );
    } else
      p.text(
        `SIMILARITY  ${result.similarity.toFixed(3)}     0 ── 1`,
        x + w / 2,
        y + h - 34,
        12,
        color.dim,
        "center",
      );
    for (const i of result.support)
      p.rect(sx + i * u, sy - 12, u - 0.7, 3, color.mint);
  } else {
    for (let i = 0; i < 16; i++)
      for (let j = 0; j < 16; j++)
        p.rect(
          sx + (j * side) / 16,
          sy + (i * side) / 16,
          side / 16 - 1,
          side / 16 - 1,
          i === j ? "#2b5a52" : "#112f30",
        );
    p.text("AWAITING BUILD", x + w / 2, sy + side / 2, 17, color.dim, "center");
  }
  p.scan(sx, sy, side, side);
}
export function sphere(p, x, y, r, theta, time, bloch) {
  const c = p.c;
  p.circle(x, y, r, "#081e22", "#476d69");
  for (let i = -2; i <= 2; i++) {
    c.beginPath();
    c.ellipse(
      x,
      y,
      r,
      Math.max(3, (r * Math.sqrt(1 - (i / 3) ** 2)) / 4),
      0,
      0,
      Math.PI * 2,
    );
    c.strokeStyle = "#416b6344";
    c.stroke();
  }
  for (let a = 0; a < 3; a++) {
    c.beginPath();
    c.ellipse(x, y, r * 0.3, r, (a * Math.PI) / 3, 0, Math.PI * 2);
    c.strokeStyle = "#78a99966";
    c.stroke();
  }
  const t = theta,
    px = x + r * 0.8 * (bloch ? bloch.x : Math.sin(t)),
    py = y - r * 0.8 * (bloch ? -bloch.y * 0.55 + bloch.z * 0.65 : Math.cos(t));
  p.line(
    [
      [x - r - 10, y],
      [x + r + 10, y],
    ],
    "#619a8744",
  );
  p.line(
    [
      [x, y - r - 10],
      [x, y + r + 10],
    ],
    "#619a8744",
  );
  p.line(
    [
      [x, y],
      [px, py],
    ],
    color.amber,
    3,
  );
  p.circle(px, py, 4, "#ffe2a2");
  p.circle(x, y, 3, color.mint);
}
export function results(p, box, s, on) {
  const { x, y, w, h } = box;
  p.frame(x, y, w, h, "SEASON TEST");
  const r = s.result;
  if (!r) {
    p.text(
      "BUILD → RUN → REPAIR",
      x + w / 2,
      y + h / 2,
      20,
      color.amber,
      "center",
    );
    return;
  }
  const left = x + 50,
    top = y + 82,
    cw = w - 80,
    ch = Math.max(30, h - 141),
    max =
      Math.max(
        ...r.actual,
        ...r.predicted,
        ...(s.previous?.round === s.round ? s.previous.predicted : []),
        r.baseline,
      ) * 1.15;
  for (let j = 0; j <= 2; j++) {
    const py = top + ch * (1 - j / 2);
    p.line(
      [
        [left, py],
        [left + cw, py],
      ],
      "#5c86722a",
    );
    p.text(((max * j) / 2).toFixed(0), left - 8, py, 10, color.dim, "right");
  }
  const growth = s.runAt ? Math.min(1, (performance.now() - s.runAt) / 650) : 1;
  const step = cw / 4;
  r.actual.forEach((v, i) => {
    const px = left + step * (i + 0.5),
      bw = Math.min(22, step * 0.18),
      base = top + ch;
    p.rect(
      px - bw - 3,
      base - ((ch * v) / max) * growth,
      bw,
      ((ch * v) / max) * growth,
      color.amber,
    );
    p.rect(
      px + 3,
      base - ((ch * r.predicted[i]) / max) * growth,
      bw,
      ((ch * r.predicted[i]) / max) * growth,
      color.mint,
    );
    if (s.previous?.round === s.round) {
      const py = base - (ch * s.previous.predicted[i]) / max;
      p.line(
        [
          [px - bw - 4, py],
          [px + bw + 4, py],
        ],
        color.blue,
        2,
      );
    }
    p.button(
      `year-${i}`,
      String(r.years[i]),
      px - step * 0.34,
      y + h - 44,
      step * 0.68,
      28,
      () => on("year", i),
      { active: s.selectedYear === i },
    );
  });
  const by = top + ch - (ch * r.baseline) / max;
  p.line(
    [
      [left, by],
      [left + cw, by],
    ],
    "#85afa57a",
    1,
  );
  p.text("ha/fire", x + 24, y + 47, 10, color.dim);
  p.text("■ OBSERVED", x + w - 240, y + 47, 10, color.amber);
  p.text("■ MODEL", x + w - 130, y + 47, 10, color.mint);
  p.text("─ MEAN", x + w - 240, y + 63, 10, color.dim);
  if (s.previous?.round === s.round)
    p.text("─ PREVIOUS", x + w - 130, y + 63, 10, color.blue);
}

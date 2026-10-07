import { color } from "./paint.js";
import { beatrice } from "./beatrice.js";
import { sphere } from "./instruments.js";
export function lessonVisual(p, lesson, box, value, time, assets) {
  const { x, y, w, h } = box,
    cx = x + w / 2,
    cy = y + h / 2;
  p.screen(x, y, w, h);
  const caption = (text) =>
    p.text(text, cx, y + h - 18, 11, color.dim, "center");
  if (lesson.kind === "mission" && assets?.forest) {
    p.c.save();
    p.c.beginPath();
    p.c.rect(x + 3, y + 3, w - 6, h - 6);
    p.c.clip();
    p.c.drawImage(assets.forest, x + 3, y + 3, w - 6, h - 6);
    p.rect(x, y, w, h, "#071e2177");
    const size = Math.min(180, h * 0.43);
    beatrice(p, cx - size / 2, y + 18, size, time);
    p.c.restore();
  }
  if (lesson.kind === "mission" || lesson.kind === "repair") {
    const labels =
      lesson.kind === "mission"
        ? ["SIGNALS", "ENGINE", "SEASON"]
        : ["BUILD", "RUN", "REPAIR"];
    const bw = Math.min(105, (w - 70) / 3),
      start = cx - (bw * 3 + 24) / 2;
    const rowY = lesson.kind === "mission" ? y + h * 0.74 : cy;
    labels.forEach((label, i) => {
      const bx = start + i * (bw + 12);
      p.frame(bx, rowY - 28, bw, 56);
      p.text(label, bx + bw / 2, rowY, 12, color.amber, "center");
      if (i < 2) p.text("→", bx + bw + 6, rowY, 15, color.mint, "center");
    });
    caption(
      lesson.kind === "mission"
        ? "ONE YEAR → ONE ESTIMATE"
        : "COMPARE AGAINST YOUR FIRST ENGINE",
    );
  }
  if (lesson.kind === "signals") {
    ["SUMMER HEAT", "RAINFALL", "FOREST COVER"].forEach((label, i) => {
      const yy = y + 30 + i * Math.max(28, (h - 75) / 3);
      p.text(label, x + 20, yy, 12);
      for (let k = 0; k < 6; k++)
        p.rect(
          x + w * 0.53 + k * (w * 0.055),
          yy - 7,
          w * 0.04,
          14,
          k === 2 ? color.amber : "#476b62",
        );
    });
    caption("YEARS ARE ROWS. SIGNALS ARE COLUMNS.");
  }
  if (lesson.kind === "angle") {
    const r = Math.min(55, h * 0.28),
      theta = value ? 2.2 : 0.45;
    sphere(p, cx - w * 0.22, cy - 8, r, theta, time);
    sphere(p, cx + w * 0.22, cy - 8, r, theta * 0.35, time);
    const k = Math.cos((theta - theta * 0.35) / 2) ** 2;
    p.text(`OVERLAP ${k.toFixed(2)}`, cx, y + 20, 12, color.amber, "center");
    p.rect(x + 30, y + h - 48, w - 60, 8, "#214040");
    p.rect(x + 30, y + h - 48, (w - 60) * k, 8, color.amber);
    caption("ONE-QUBIT ROTATION EXAMPLE");
  }
  if (lesson.kind === "strength" || lesson.kind === "epsilon") {
    const left = x + 25,
      top = y + 30,
      ww = w - 50,
      hh = h - 75;
    const fit = (t) =>
      0.5 +
      Math.sin(t * 6) * 0.12 +
      (lesson.kind === "strength" && value ? Math.sin(t * 24) * 0.11 : 0);
    if (lesson.kind === "epsilon") {
      const eps = value ? 0.23 : 0.07;
      for (let j = 0; j < ww; j += 2)
        p.rect(
          left + j,
          top + hh * (fit(j / ww) - eps),
          2,
          hh * eps * 2,
          "#74ad9630",
        );
    }
    const line = Array.from({ length: 60 }, (_, i) => [
      left + (i / 59) * ww,
      top + hh * fit(i / 59),
    ]);
    p.line(line, color.mint, 3);
    for (let i = 0; i < 12; i++) {
      const t = i / 11,
        yy = 0.5 + Math.sin(t * 6) * 0.12 + Math.sin(i * 3) * 0.15;
      p.circle(left + t * ww, top + hh * yy, 3, color.amber);
    }
    caption(
      lesson.kind === "strength"
        ? "ILLUSTRATIVE FIT · SAME TRAINING DOTS"
        : "ILLUSTRATIVE NO-PENALTY BAND",
    );
  }
  if (lesson.kind === "qaoa") {
    const names = ["COST", "MIX", "SAMPLE"],
      bw = (w - 80) / 3;
    names.forEach((name, i) => {
      const bx = x + 20 + i * (bw + 20);
      p.frame(bx, y + (h < 130 ? 10 : 24), bw, h < 130 ? 35 : 45);
      p.text(
        name,
        bx + bw / 2,
        y + (h < 130 ? 28 : 47),
        12,
        color.amber,
        "center",
      );
      if (i < 2)
        p.text(
          "→",
          bx + bw + 10,
          y + (h < 130 ? 28 : 47),
          15,
          color.mint,
          "center",
        );
    });
    for (let i = 0; h >= 130 && i < 8; i++) {
      const bh =
        (0.2 + (Math.sin(i * 1.9 + value) + 1) * 0.3) * Math.max(20, h - 120);
      p.rect(
        x + 25 + (i * (w - 50)) / 8,
        y + h - 45 - bh,
        (w - 70) / 8,
        bh,
        i === 4 ? color.amber : "#679b86",
      );
    }
    caption(
      h < 130 ? "COST → MIX → SAMPLE" : "ILLUSTRATIVE CANDIDATE PROBABILITIES",
    );
  }
  if (lesson.kind === "sqd") {
    const costs = [0.7, 0.4, 0.2, 0.6],
      side = Math.min(h - 42, w * 0.46),
      cell = side / 4;
    costs.forEach((cost, i) => {
      for (let j = 0; j < 4; j++)
        p.rect(
          x + 25 + j * cell,
          y + 8 + i * cell,
          cell - 3,
          cell - 3,
          i === j ? (i === 2 ? color.amber : "#467265") : "#102d2e",
        );
      p.text(
        cost.toFixed(1),
        x + 25 + side + 22,
        y + 8 + (i + 0.5) * cell,
        Math.min(13, cell),
        i === 2 ? color.amber : color.mint,
      );
    });
    p.text(
      "KEEP",
      x + 25 + side + 65,
      y + 8 + 2.5 * cell,
      Math.min(11, cell),
      color.amber,
    );
    caption("EXAMPLE: SAMPLED DIAGONAL COSTS");
  }
  p.scan(x, y, w, h);
}

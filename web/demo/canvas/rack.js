import { color } from "./paint.js";
import { widths, angles } from "./session.js";
import { sphere } from "./instruments.js";
const angleNames = ["π/32", "π/16", "π/8", "π/4", "π/2"];
export function rack(p, b, s, data, on) {
  const { x, y, w, h } = b;
  p.frame(x, y, w, h, "SIGNAL RACK");
  const gap = 8,
    bw = (w - 48 - gap * 3) / 4;
  widths.forEach((n, i) =>
    p.button(
      `width-${n}`,
      `${n} INPUTS`,
      x + 24 + i * (bw + gap),
      y + 51,
      bw,
      32,
      () => on("width", n),
      { active: s.width === n },
    ),
  );
  const paged = h < 410,
    slots = paged ? Math.max(1, Math.floor((h - 135) / 35)) : 10,
    perPage = slots * 2,
    pages = Math.ceil(20 / perPage),
    page = paged ? (s.rackPage || 0) % pages : 0;
  const top = y + 92,
    row = Math.min(37, (h - 126) / slots),
    col = (w - 58) / 2;
  data.features
    .slice(page * perPage, page * perPage + perPage)
    .forEach((f, position) => {
      const i = position + page * perPage;
      const active = s.features.includes(i),
        bx = x + 24 + (i % 2) * (col + 10),
        by = top + Math.floor(position / 2) * row;
      p.button(
        `signal-${i}`,
        f.label,
        bx,
        by,
        col,
        row - 5,
        () => on("feature", i),
        { active, disabled: false },
      );
      p.circle(bx + 7, by + (row - 5) / 2, 2, active ? color.amber : "#627e6b");
    });
  if (paged)
    p.button(
      "rack-page",
      `${page + 1} / ${pages} ▶`,
      x + 24,
      y + h - 40,
      94,
      28,
      () => on("rack-page", pages),
    );
  else
    p.text(
      `${s.features.length}/${s.width} CONNECTED`,
      x + 25,
      y + h - 24,
      11,
      color.dim,
    );
  p.button("foundry", "SUBSET FOUNDRY", x + w - 173, y + h - 40, 148, 28, () =>
    on("foundry"),
  );
}
export function controls(p, b, s, on, time, bloch) {
  const { x, y, w, h } = b;
  p.frame(x, y, w, h, "ENCODER");
  const r = Math.min(w * 0.26, 55);
  sphere(p, x + w / 2, y + 65 + r, r, s.angle, time, bloch);
  const yy = y + 142 + r * 0.7;
  p.text("ANGLE", x + 24, yy, 11, color.dim);
  p.button("angle-down", "−", x + 23, yy + 18, 33, 31, () => on("angle", -1), {
    disabled: s.angle === angles[0],
  });
  p.text(
    angleNames[angles.indexOf(s.angle)],
    x + w / 2,
    yy + 33,
    18,
    color.amber,
    "center",
  );
  p.button("angle-up", "+", x + w - 56, yy + 18, 33, 31, () => on("angle", 1), {
    disabled: s.angle === angles.at(-1),
  });
  [
    ["C", s.C, "strength"],
    ["ε", s.epsilon, "epsilon"],
  ].forEach(([label, value, id], i) => {
    const py = yy + 85 + i * 64;
    p.text(label, x + 24, py, 15, color.dim);
    p.button(`${id}-down`, "−", x + 23, py + 15, 33, 29, () => on(id, -1), {
      disabled:
        (id === "angle" ? s.angle : id === "strength" ? s.C : s.epsilon) ===
        (id === "angle" ? angles[0] : id === "strength" ? 0.3 : 0.05),
    });
    p.text(String(value), x + w / 2, py + 29, 17, color.amber, "center");
    p.button(`${id}-up`, "+", x + w - 56, py + 15, 33, 29, () => on(id, 1), {
      disabled:
        (id === "angle" ? s.angle : id === "strength" ? s.C : s.epsilon) ===
        (id === "angle" ? angles.at(-1) : id === "strength" ? 10 : 0.5),
    });
  });
  if (s.result && h > 420) {
    const r = s.result;
    p.text("SUPPORT SEASONS", x + 24, y + h - 82, 10, color.dim);
    p.text(String(r.support.length), x + 24, y + h - 51, 26);
    p.text(`/${r.trainYears.length}`, x + 70, y + h - 47, 12, color.dim);
  }
}
export function controlsCompact(p, b, s, on, time, bloch) {
  const { x, y, w, h } = b;
  p.frame(x, y, w, h, "ENCODER");
  const horizontal = h < 215 && w >= 300;
  if (!horizontal)
    sphere(
      p,
      x + w * 0.23,
      y + h / 2,
      Math.min(39, w * 0.18),
      s.angle,
      0,
      bloch,
    );
  [
    ["angle", angleNames[angles.indexOf(s.angle)]],
    ["strength", s.C],
    ["epsilon", s.epsilon],
  ].forEach(([id, v], i) => {
    const py = horizontal ? y + 48 : y + 56 + i * 57,
      cx = horizontal ? x + 24 + ((i + 0.5) * (w - 48)) / 3 : x + w * 0.7,
      offset = horizontal ? Math.min(52, (w - 48) / 6 - 14) : 52,
      bh = horizontal ? 26 : 30,
      buttonW = horizontal ? 20 : 27;
    p.text(
      id === "angle" ? "ANGLE" : id === "strength" ? "C" : "ε",
      cx,
      py,
      11,
      color.dim,
      "center",
    );
    p.button(
      `${id}-down`,
      "−",
      cx - offset,
      py + 13,
      buttonW,
      bh,
      () => on(id, -1),
      {
        disabled:
          (id === "angle" ? s.angle : id === "strength" ? s.C : s.epsilon) ===
          (id === "angle" ? angles[0] : id === "strength" ? 0.3 : 0.05),
      },
    );
    p.text(String(v), cx, py + 29, horizontal ? 11 : 13, color.amber, "center");
    p.button(
      `${id}-up`,
      "+",
      cx + offset - buttonW,
      py + 13,
      buttonW,
      bh,
      () => on(id, 1),
      {
        disabled:
          (id === "angle" ? s.angle : id === "strength" ? s.C : s.epsilon) ===
          (id === "angle" ? angles.at(-1) : id === "strength" ? 10 : 0.5),
      },
    );
  });
}

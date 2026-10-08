import { frameMaterial, screwMaterial } from "./materials.js";
import { choiceControl } from "./contract-lock.js";
import { buttonSurface } from "./button-surface.js";

export const color = {
  ink: "#081b1c",
  panel: "#163637",
  mint: "#aed6b6",
  dim: "#749b92",
  amber: "#ffb653",
  copper: "#ce6733",
  red: "#ec6f56",
  blue: "#72bfd2",
};
export class Paint {
  constructor(ctx) {
    this.c = ctx;
    this.hits = [];
    this.focus = "";
    this.hover = "";
  }
  rect(x, y, w, h, fill) {
    this.c.fillStyle = fill;
    this.c.fillRect(x, y, w, h);
  }
  line(points, stroke, width = 1) {
    const c = this.c;
    c.beginPath();
    points.forEach(([x, y], i) => (i ? c.lineTo(x, y) : c.moveTo(x, y)));
    c.strokeStyle = stroke;
    c.lineWidth = width;
    c.stroke();
  }
  text(s, x, y, size = 14, fill = color.mint, align = "left") {
    const c = this.c;
    c.font = `${size >= 22 ? "bold " : ""}${size}px ui-monospace, SFMono-Regular, Menlo, Consolas, monospace`;
    c.textAlign = align;
    c.textBaseline = "middle";
    c.fillStyle = fill;
    c.fillText(s, x, y);
  }
  circle(x, y, r, fill, stroke) {
    const c = this.c;
    c.beginPath();
    c.arc(x, y, r, 0, Math.PI * 2);
    c.fillStyle = fill;
    c.fill();
    if (stroke) {
      c.strokeStyle = stroke;
      c.lineWidth = 2;
      c.stroke();
    }
  }
  screw(x, y) {
    screwMaterial(this.c, x, y);
  }
  frame(x, y, w, h, title = "") {
    const c = this.c,
      g = c.createLinearGradient(x, y, x + w, y + h);
    g.addColorStop(0, "#345c5b");
    g.addColorStop(0.25, "#1c3c3d");
    g.addColorStop(1, "#112c2f");
    this.rect(x, y, w, h, g);
    const face = c.createLinearGradient(x, y, x + w * 0.8, y + h);
    face.addColorStop(0, "#244546");
    face.addColorStop(0.45, "#193b3d");
    face.addColorStop(1, "#102c30");
    this.rect(x + 7, y + 7, w - 14, h - 14, face);
    for (let i = 10; i < h - 10; i += 4)
      this.rect(x + 8, y + i, w - 16, 1, "#8bb9a104");
    this.line(
      [
        [x + 5, y + h - 8],
        [x + 5, y + 5],
        [x + w - 8, y + 5],
      ],
      "#a0c5b232",
    );
    this.line(
      [
        [x + 10, y + h - 9],
        [x + w - 10, y + h - 9],
        [x + w - 10, y + 10],
      ],
      "#061f2377",
    );
    this.line(
      [
        [x, y + h],
        [x, y],
        [x + w, y],
      ],
      "#72998c",
      2,
    );
    this.line(
      [
        [x + w, y],
        [x + w, y + h],
        [x, y + h],
      ],
      "#051416",
      3,
    );
    frameMaterial(c, x, y, w, h);
    for (const [a, b] of [
      [x + 13, y + 13],
      [x + w - 13, y + 13],
      [x + 13, y + h - 13],
      [x + w - 13, y + h - 13],
    ])
      this.screw(a, b);
    if (title) {
      this.rect(x + 24, y + 13, w - 48, 28, "#0b2527");
      this.text(title, x + 34, y + 27, 13);
    }
  }
  screen(x, y, w, h) {
    this.rect(x, y, w, h, "#030e13");
    this.rect(x + 4, y + 4, w - 8, h - 8, "#071e21");
    this.line(
      [
        [x, y + h],
        [x + w, y + h],
        [x + w, y],
      ],
      "#517c72",
      2,
    );
  }
  button(
    id,
    label,
    x,
    y,
    w,
    h,
    action,
    { active = false, disabled = false, tone = "normal" } = {},
  ) {
    disabled ||= this.choiceLocked && choiceControl(id);
    const backward = /[◀←↔]/.test(label), forward = /[▶→↔]/.test(label);
    label = label.replace(/[◀←▶→↔]/g, "").trim();
    const focused = this.focus === id || this.hover === id;
    const fill = disabled
      ? "#203c3b"
      : active || tone === "hot"
        ? "#bb682b"
        : focused
          ? "#366663"
          : "#244849";
    this.rect(x + 2, y + 3, w, h, "#041719");
    const gradient = this.c.createLinearGradient(x, y, x, y + h);
    gradient.addColorStop(0, fill);
    gradient.addColorStop(0.55, fill);
    gradient.addColorStop(
      1,
      disabled ? "#193332" : active || tone === "hot" ? "#9b4924" : "#1b393c",
    );
    this.rect(x, y, w, h, gradient);
    buttonSurface(this.c, x, y, w, h, disabled);
    this.line(
      [
        [x, y + h],
        [x, y],
        [x + w, y],
      ],
      disabled ? "#4d6962" : active || tone === "hot" ? "#ffd080" : "#87ac9d",
      2,
    );
    this.line(
      [
        [x + w, y],
        [x + w, y + h],
        [x, y + h],
      ],
      "#091d21",
      2,
    );
    if (focused)
      this.line(
        [
          [x, y],
          [x + w, y],
          [x + w, y + h],
          [x, y + h],
          [x, y],
        ],
        color.amber,
      );
    this.text(
      label,
      x + w / 2 + (backward ? 10 : 0) - (forward ? 10 : 0),
      y + h / 2,
      Math.max(10, Math.min(14, (w - 16 - (forward || backward ? 24 : 0)) / (label.length * 0.62))),
      disabled ? "#758b83" : active || tone === "hot" ? "#151c1c" : color.mint,
      "center",
    );
    const arrow = (cx, direction) => {
      const cy = y + h / 2, tint = disabled ? color.dim : color.amber;
      this.line([[cx - direction * 12, cy + 2], [cx + direction * 3, cy + 2]], "#041719", 4);
      this.line([[cx - direction * 12, cy], [cx + direction * 2, cy]], color.mint, 2);
      this.line([[cx - direction * 5, cy - 6], [cx + direction * 3, cy],
        [cx - direction * 5, cy + 6]], tint, 3);
    };
    if (forward) arrow(x + w - 17, 1);
    if (backward) arrow(x + 19, -1);
    this.hits.push({ id, label, x, y, w, h, action, disabled });
  }
  cable(x, y, tx, ty, t = 0) {
    const c = this.c;
    c.beginPath();
    c.moveTo(x, y);
    c.bezierCurveTo(x + 55, y, tx - 70, ty, tx, ty);
    c.strokeStyle = "#071519";
    c.lineWidth = 12;
    c.stroke();
    c.strokeStyle = "#c16532";
    c.lineWidth = 7;
    c.stroke();
    c.strokeStyle = "#ffa64f";
    c.lineWidth = 2;
    c.stroke();
    this.circle(x, y, 6, "#193839", "#e38947");
    this.circle(tx, ty, 6, "#193839", "#e38947");
    if (t) {
      c.setLineDash([3, 32]);
      c.lineDashOffset = -t * 60;
      c.strokeStyle = "#ffe0a2";
      c.lineWidth = 3;
      c.stroke();
      c.setLineDash([]);
    }
  }
  scan(x, y, w, h) {
    for (let i = y; i < y + h; i += 3) this.rect(x, i, w, 1, "#00000012");
  }
}
export function pixelTitle(p, title, x, y, scale = 7) {
  const glyphs = {
    F: ["11111", "10000", "10000", "11110", "10000", "10000", "10000"],
    I: ["111", "010", "010", "010", "010", "010", "111"],
    R: ["11110", "10001", "10001", "11110", "10100", "10010", "10001"],
    E: ["11111", "10000", "10000", "11110", "10000", "10000", "11111"],
    L: ["10000", "10000", "10000", "10000", "10000", "10000", "11111"],
    N: ["10001", "11001", "11001", "10101", "10011", "10011", "10001"],
  };
  for (const letter of title) {
    const rows = glyphs[letter];
    if (!rows) continue;
    rows.forEach((row, j) =>
      [...row].forEach((v, i) => {
        if (v === "1") {
          p.rect(x + i * scale + 2, y + j * scale + 3, scale, scale, "#041517");
          p.rect(
            x + i * scale,
            y + j * scale,
            scale - 1,
            scale - 1,
            color.amber,
          );
        }
      }),
    );
    x += (rows[0].length + 1) * scale;
  }
}

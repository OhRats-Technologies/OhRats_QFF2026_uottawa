// Canvas panel renderer for Fireline presentation slides.
// Matches the visual language of web/demo/canvas/paint.js and workbench.js.

export const color = {
  ink: "#081b1c",
  panel: "#163637",
  panelDark: "#0c2324",
  mint: "#aed6b6",
  dim: "#749b92",
  amber: "#ffb653",
  copper: "#ce6733",
  red: "#ec6f56",
  blue: "#72bfd2",
};

export class PanelPainter {
  constructor(ctx) {
    this.c = ctx;
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

  text(s, x, y, size = 12, fill = color.mint, align = "left") {
    const c = this.c;
    c.font = `${size >= 20 ? "bold " : ""}${size}px ui-monospace, SFMono-Regular, Menlo, Consolas, monospace`;
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
      c.lineWidth = 1.5;
      c.stroke();
    }
  }

  screw(x, y) {
    this.circle(x, y, 4.5, "#0c2326", "#496c68");
    this.line(
      [
        [x - 2, y + 2],
        [x + 2, y - 2],
      ],
      "#8bb1a2",
      1.5,
    );
  }

  frame(x, y, w, h, title = "") {
    const c = this.c;
    const g = c.createLinearGradient(x, y, x + w, y + h);
    g.addColorStop(0, "#345c5b");
    g.addColorStop(0.25, "#1c3c3d");
    g.addColorStop(1, "#112c2f");
    this.rect(x, y, w, h, g);
    this.rect(x + 7, y + 7, w - 14, h - 14, color.panel);
    for (let i = 10; i < h - 10; i += 4) {
      this.rect(x + 8, y + i, w - 16, 1, "#8bb9a104");
    }
    this.line(
      [
        [x + 5, y + h - 8],
        [x + 5, y + 5],
        [x + w - 8, y + 5],
      ],
      "#a0c5b232",
      1,
    );
    this.line(
      [
        [x + 10, y + h - 9],
        [x + w - 10, y + h - 9],
        [x + w - 10, y + 10],
      ],
      "#061f2377",
      1,
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
    for (const [a, b] of [
      [x + 13, y + 13],
      [x + w - 13, y + 13],
      [x + 13, y + h - 13],
      [x + w - 13, y + h - 13],
    ]) {
      this.screw(a, b);
    }
    if (title) {
      this.rect(x + 24, y + 12, w - 48, 26, "#0b2527");
      this.line(
        [
          [x + 24, y + 38],
          [x + 24, y + 12],
          [x + w - 24, y + 12],
        ],
        "#345c5b",
        1,
      );
      this.text(title, x + 34, y + 25, 11, color.amber);
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
}

let metalPattern = null;
export function getMetalPattern(ctx) {
  if (metalPattern) return metalPattern;
  const canvas = document.createElement("canvas");
  canvas.width = 128;
  canvas.height = 128;
  const m = canvas.getContext("2d");
  m.fillStyle = "#123638";
  m.fillRect(0, 0, 128, 128);
  let seed = 163;
  const random = () => {
    seed = (seed * 16807) % 2147483647;
    return seed / 2147483647;
  };
  for (let i = 0; i < 2400; i++) {
    m.fillStyle = random() > 0.5 ? "#aedbb40b" : "#00000015";
    m.fillRect(random() * 128, random() * 128, random() * 5 + 1, 1);
  }
  metalPattern = ctx.createPattern(canvas, "repeat");
  return metalPattern;
}

export function drawSlidePanels(canvas, slideId) {
  const dpr = typeof window !== "undefined" ? window.devicePixelRatio || 1 : 1;
  canvas.width = 1280 * dpr;
  canvas.height = 720 * dpr;
  const ctx = canvas.getContext("2d");
  if (ctx.resetTransform) ctx.resetTransform();
  ctx.scale(dpr, dpr);
  const p = new PanelPainter(ctx);
  const W = 1280;
  const H = 720;

  // Background chassis
  const pattern = getMetalPattern(ctx);
  if (pattern) {
    p.rect(0, 0, W, H, pattern);
  } else {
    p.rect(0, 0, W, H, "#081b1c");
  }

  // Outer workstation chassis frame around slide perimeter
  p.frame(6, 6, W - 12, H - 12);

  switch (slideId) {
    case "question": {
      // Left hero info panel
      p.frame(60, 50, 560, 600, "QISKIT FALL FEST 2026 · FIRELINE");
      // Right map chassis & CRT screen
      p.frame(645, 50, 575, 600, "ONTARIO CONTEXT · 2021 LAND COVER");
      p.screen(660, 95, 545, 535);
      break;
    }
    case "data": {
      // Left map & pixels panel
      p.frame(60, 105, 555, 360, "INPUT STAGE · ALGONQUIN & ONTARIO");
      // Right join story panel
      p.frame(645, 105, 575, 360, "ANNUAL RECORD AGGREGATION");
      // Bottom year strip panel
      p.frame(60, 480, 1160, 140, "1988–2024 TIMELINE · 31 TRAIN / 6 TEST");
      break;
    }
    case "selection": {
      // Left subset search panel
      p.frame(60, 105, 555, 515, "CANDIDATE SELECTION · QAOA & SQD");
      // Right selector evaluation benchmark panel
      p.frame(645, 105, 575, 515, "EVALUATION BENCHMARK · FIXED RIDGE");
      break;
    }
    case "development": {
      // Main chart panel
      p.frame(60, 115, 1160, 505, "CHRONOLOGICAL DEVELOPMENT · RBF VS QSVR");
      p.screen(76, 175, 1128, 335);
      break;
    }
    case "evaluation": {
      // Main holdout evaluation panel
      p.frame(60, 115, 1160, 505, "2019–2024 HOLDOUT EVALUATION · REUSED YEARS");
      p.screen(76, 175, 1128, 335);
      break;
    }
    case "geometry": {
      // Left angle side panel
      p.frame(60, 115, 565, 505, "INPUT ANGLE ENCODING · θ = a tanh(z/2)");
      // Right matrix heatmap panel
      p.frame(655, 115, 565, 505, "KERNEL ENGINE · MEASURED GRAM MATRIX");
      p.screen(740, 175, 395, 395);
      break;
    }
    case "conclusions": {
      // Three distinct finding panels side-by-side
      p.frame(60, 120, 360, 500, "1 · ENCODING GEOMETRY");
      p.frame(460, 120, 360, 500, "2 · QAOA OPTIMIZATION");
      p.frame(860, 120, 360, 500, "3 · HARDWARE NOISE");
      break;
    }
    case "encoding": {
      // Appendix: circuit panel
      p.frame(60, 110, 675, 510, "CIRCUIT · FOUR-QUBIT LINEAR ZZ FEATURE MAP");
      p.screen(76, 160, 643, 380);
      // Explanation panel
      p.frame(765, 110, 455, 510, "FIDELITY QUANTUM KERNEL + QSVR");
      break;
    }
    case "resources": {
      // Appendix: shot sweep panel
      p.frame(60, 110, 850, 510, "HARDWARE SHOT SWEEP · MARRAKESH & QUEBEC");
      p.screen(76, 160, 818, 435);
      // Resource receipt ledger panel
      p.frame(940, 110, 280, 510, "RESOURCE LEDGER");
      break;
    }
    default: {
      p.frame(60, 110, 1160, 510, "FIRELINE WORKBENCH");
      break;
    }
  }
}

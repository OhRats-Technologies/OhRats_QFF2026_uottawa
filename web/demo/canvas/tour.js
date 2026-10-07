import { color } from "./paint.js";
import { drawWorkbench } from "./workbench.js";
import { foundry } from "./overlays.js";
import { sampleCandidates } from "./foundry.js";
import { beatrice, bettyCue } from "./beatrice.js";
import { settle } from "./glide.js";
export const tour = [
  {
    name: "ONTARIO",
    tab: "map",
    zone: "map",
    text: "I'm Betty. This is your workshop. These are recorded Ontario fires and forest cover. Our engine estimates the average hectares per fire for a year.",
  },
  {
    name: "SIGNAL RACK",
    tab: "rack",
    zone: "rack",
    text: "Choose your inputs here: heat, rain or forest signals. Lit buttons are connected. Start with a few; more signals mean more computation.",
  },
  {
    name: "ANGLE",
    tab: "kernel",
    ids: ["angle-down", "angle-up"],
    text: "These buttons change the encoding angle range. Scaled signals become quantum rotations; their state overlaps form the similarity grid. Wider isn't always better.",
  },
  {
    name: "C",
    tab: "kernel",
    ids: ["strength-down", "strength-up"],
    text: "C controls how strongly SVR penalizes errors outside its tolerance band. Higher C pushes harder to fit training rows; lower C favors a simpler fit.",
  },
  {
    name: "EPSILON",
    tab: "kernel",
    ids: ["epsilon-down", "epsilon-up"],
    text: "Epsilon sets the no-penalty band. Wider tolerates more small deviations; narrower asks for a closer fit. Its units are scaled log targets, not hectares.",
  },
  {
    name: "SUBSET FOUNDRY",
    tab: "rack",
    ids: ["foundry"],
    text: "This opens the subset foundry. QAOA—the Quantum Approximate Optimization Algorithm—alternates cost and mixing operations to reshape which four-signal subsets get sampled.",
  },
  {
    name: "SQD SHORTLIST",
    tab: "rack",
    foundry: true,
    text: "SQD means Sample-based Quantum Diagonalization: solve a smaller matrix formed from sampled states. Here it is diagonal, so the starred row is the cheapest sampled subset. Patch it, then test its prediction.",
  },
  {
    name: "RUN YOUR ENGINE",
    tab: "rack",
    ids: ["run"],
    text: "Run once to set your starting score. Change something and run again. Win by cutting error 5%, or effort 25% with at most 5% extra error. You're ready—start here.",
  },
];
export function tourView(s) {
  const lesson = tour[s.guideStep || 0];
  return { ...s, menu: false, tab: lesson.tab, toast: "", foundry: false };
}
function lines(c, text, width, size) {
  c.font = `${size}px ui-monospace, SFMono-Regular, Menlo, Consolas, monospace`;
  const result = [];
  let line = "";
  for (const word of text.split(" ")) {
    const next = line ? `${line} ${word}` : word;
    if (line && c.measureText(next).width > width) {
      result.push(line);
      line = word;
    } else line = next;
  }
  result.push(line);
  return result;
}
function union(hits) {
  if (!hits.length) return null;
  const x = Math.min(...hits.map((h) => h.x)),
    y = Math.min(...hits.map((h) => h.y));
  return {
    x: x - 7,
    y: y - 18,
    w: Math.max(...hits.map((h) => h.x + h.w)) - x + 14,
    h: Math.max(...hits.map((h) => h.y + h.h)) - y + 25,
  };
}
function overlap(a, b) {
  return (
    Math.max(0, Math.min(a.x + a.w, b.x + b.w) - Math.max(a.x, b.x)) *
    Math.max(0, Math.min(a.y + a.h, b.y + b.h) - Math.max(a.y, b.y))
  );
}
export function spotlight(p, s, on, W, H, time, zones) {
  const step = s.guideStep || 0,
    lesson = tour[step],
    hits = p.hits;
  let target = lesson.zone
    ? zones[lesson.zone]
    : union(hits.filter((h) => lesson.ids?.includes(h.id)));
  if (lesson.foundry)
    target = union(hits.filter((h) => h.id.startsWith("candidate-")));
  target ||= { x: 20, y: 65, w: W - 40, h: 120 };
  target = {
    x: Math.max(7, target.x),
    y: Math.max(7, target.y),
    w: Math.min(target.w, W - 14),
    h: Math.min(target.h, H - 14),
  };
  target.w = Math.min(target.w, W - target.x - 7);
  target.h = Math.min(target.h, H - target.y - 7);
  const { x, y, w, h } = target;
  // The bubble's width follows its text, so steps resize it as they change.
  const font = W < 500 ? 12 : 13,
    bw = Math.min(W - 28, Math.max(300, Math.min(420, lesson.text.length * 2))),
    textW = bw - 34,
    body = lines(p.c, lesson.text, textW, font),
    bh = 68 + body.length * font * 1.4 + 43,
    clampX = (v) => Math.max(14, Math.min(W - bw - 14, v)),
    clampY = (v) => Math.max(12, Math.min(H - bh - 12, v));
  const candidates = [
    [x + w + 20, y],
    [x - bw - 20, y],
    [x, y + h + 18],
    [x, y - bh - 18],
    [14, H - bh - 14],
    [W - bw - 14, H - bh - 14],
    [14, 70],
    [W - bw - 14, 70],
  ].map(([xx, yy]) => ({ x: clampX(xx), y: clampY(yy), w: bw, h: bh }));
  const score = (b) =>
    overlap(b, target) * 100 +
    Math.hypot(b.x + bw / 2 - (x + w / 2), b.y + bh / 2 - (y + h / 2));
  const landscape = W >= 650 && W < 920 && H < 500;
  const box = landscape
    ? { x: W - bw - 14, y: clampY(y), w: bw, h: bh }
    : candidates.sort((a, b) => score(a) - score(b))[0];
  // Draw the eased highlight and bubble; the final layout is still returned.
  const shown = settle(step, target, box, time),
    { x: sx, y: sy, w: sw, h: sh } = shown.target,
    { x: bx, y: by, w: cw, h: ch } = shown.box,
    veil = "#031218b8";
  p.rect(0, 0, W, sy, veil);
  p.rect(0, sy, sx, sh, veil);
  p.rect(sx + sw, sy, W - sx - sw, sh, veil);
  p.rect(0, sy + sh, W, H - sy - sh, veil);
  p.line(
    [
      [sx, sy],
      [sx + sw, sy],
      [sx + sw, sy + sh],
      [sx, sy + sh],
      [sx, sy],
    ],
    color.amber,
    2,
  );
  // A tether visibly connects the small dialogue to its actual UI target.
  const tx = Math.max(sx, Math.min(sx + sw, bx + cw / 2)),
    ty = Math.max(sy, Math.min(sy + sh, by + ch / 2));
  p.line(
    [
      [bx + cw / 2, by + ch / 2],
      [tx, ty],
    ],
    "#ffc57799",
    2,
  );
  p.circle(tx, ty, 4, color.amber);
  p.rect(bx + 3, by + 4, cw, ch, "#00000066");
  p.rect(bx, by, cw, ch, "#102c2ff5");
  p.line(
    [
      [bx, by + ch],
      [bx, by],
      [bx + cw, by],
      [bx + cw, by + ch],
      [bx, by + ch],
    ],
    "#83aaa0",
    1,
  );
  beatrice(
    p,
    bx + 10,
    by + 8,
    46,
    time,
    bettyCue("tour", step, time, lesson.text),
  );
  p.c.save();
  p.c.globalAlpha = shown.fade;
  p.text(
    `BETTY · ${step + 1}/${tour.length}`,
    bx + 67,
    by + 20,
    11,
    color.amber,
  );
  p.text(lesson.name, bx + 67, by + 42, 12, color.mint);
  body.forEach((line, i) =>
    p.text(line, bx + 17, by + 70 + i * font * 1.4, font),
  );
  p.c.restore();
  p.hits = [];
  p.button(
    "guide-back",
    "◀",
    bx + 16,
    by + ch - 36,
    35,
    25,
    () => on("guide-step", -1),
    { disabled: step === 0 },
  );
  p.button("guide-skip", "SKIP", bx + 61, by + ch - 36, 58, 25, () =>
    on("guide-play"),
  );
  p.button(
    "guide-next",
    step === 7 ? "LET'S BUILD ▶" : "NEXT ▶",
    bx + cw - 145,
    by + ch - 36,
    129,
    25,
    () => on(step === 7 ? "guide-play" : "guide-step", 1),
    { tone: "hot" },
  );
  return { target, bubble: box, topic: lesson.name };
}

const tutorialSamples = new Map();
export function drawTour(p, s, data, assets, on, W, H, time, geometry) {
  const view = tourView(s),
    tourW = W >= 650 && W < 920 && H < 500 ? W / 2 : W,
    tourH = W < 650 ? H - 235 : H;
  p.rect(0, 0, W, H, color.ink);
  const zones = drawWorkbench(
    p,
    view,
    data,
    assets,
    on,
    tourW,
    tourH,
    time,
    null,
    geometry,
  );
  if (tour[s.guideStep || 0].foundry) {
    const round = data.rounds[s.round];
    if (!tutorialSamples.has(round))
      tutorialSamples.set(
        round,
        sampleCandidates(round.objective, 64, 31, "qaoa"),
      );
    p.hits = [];
    foundry(
      p,
      { ...view, sample: tutorialSamples.get(round), candidate: 0 },
      data,
      on,
      tourW,
      tourH,
    );
  }
  return spotlight(p, s, on, W, H, time, zones);
}

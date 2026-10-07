import { color } from "./paint.js";
import { beatrice, bettyCue } from "./beatrice.js";
import { lessons } from "./guide-lessons.js";
import { lessonVisual } from "./guide-visuals.js";
export { lessons } from "./guide-lessons.js";
function wrapped(p, text, x, y, width, size, fill = color.mint) {
  p.c.font = `${size}px ui-monospace, SFMono-Regular, Menlo, Consolas, monospace`;
  const lines = [],
    words = text.split(" ");
  let line = "";
  for (const word of words) {
    const next = line ? `${line} ${word}` : word;
    if (line && p.c.measureText(next).width > width) {
      lines.push(line);
      line = word;
    } else line = next;
  }
  lines.push(line);
  lines.forEach((line, i) => p.text(line, x, y + i * size * 1.5, size, fill));
  return lines.length * size * 1.5;
}
export function drawGuide(p, s, on, W, H, time, assets) {
  p.rect(0, 0, W, H, "#031218f5");
  const w = Math.min(W - 24, 1100),
    h = Math.min(H - 24, 700),
    x = (W - w) / 2,
    y = (H - h) / 2,
    mobile = w < 650,
    short = h < 470,
    step = Math.max(0, Math.min(7, s.guideStep || 0)),
    lesson = lessons[step];
  p.frame(x, y, w, h, s.guideIntro ? "BETTY'S BRIEFING" : "BETTY'S GUIDE");
  if (s.guideIntro) {
    p.text(
      `${step + 1} / ${lessons.length}`,
      x + w - 100,
      y + 27,
      12,
      color.amber,
    );
    for (let i = 0; i < lessons.length; i++)
      p.rect(
        x + 25 + i * ((w - 50) / 8),
        y + 51,
        (w - 66) / 8,
        3,
        i <= step ? color.amber : "#355953",
      );
  } else {
    const columns = mobile ? 4 : 8,
      rows = mobile ? 2 : 1,
      tw = (w - 50) / columns;
    lessons.forEach((item, i) =>
      p.button(
        `guide-topic-${i}`,
        item.tab,
        x + 25 + (i % columns) * tw,
        y + 51 + Math.floor(i / columns) * 31,
        tw - 5,
        26,
        () => on("guide-topic", i),
        { active: i === step },
      ),
    );
    p.button("close-help", "×", x + w - 58, y + 14, 31, 27, () =>
      on("guide-close"),
    );
  }
  const top = y + (s.guideIntro ? 73 : mobile ? 121 : 90),
    bottom = y + h - 64,
    left = x + 25,
    textW = mobile ? w - 50 : w * 0.45 - 35,
    portrait = short ? 32 : 72;
  beatrice(
    p,
    left,
    top,
    portrait,
    time,
    bettyCue("guide", step, time, `${lesson.title} ${lesson.text}`),
  );
  p.text(
    "BETTY",
    left + portrait + 15,
    top + (short ? 8 : 20),
    short ? 13 : 16,
    color.amber,
  );
  p.text(
    "YOUR FIELD GUIDE",
    left + portrait + 15,
    top + (short ? 26 : 43),
    short ? 9 : 10,
    color.dim,
  );
  const titleY = top + portrait + (short ? 12 : 18),
    font = short ? 11 : 14;
  const titleH = wrapped(
    p,
    lesson.title,
    left,
    titleY,
    textW,
    short ? 14 : 20,
    color.amber,
  );
  const textY = titleY + titleH + (short ? 6 : 12);
  const textH = wrapped(p, lesson.text, left, textY, textW, font);
  const tipY = textY + textH + (short ? 6 : 13);
  const tipH = wrapped(
    p,
    lesson.tip,
    left,
    tipY,
    textW,
    short ? 10 : 12,
    color.blue,
  );
  const visualY = mobile ? tipY + tipH + 17 : top,
    visualX = mobile ? left : x + w * 0.5,
    visualW = mobile ? textW : w * 0.5 - 25,
    visualH = Math.max(80, bottom - visualY - 36),
    box = { x: visualX, y: visualY, w: visualW, h: visualH };
  lessonVisual(p, lesson, box, s.guideValue || 0, time, assets);
  const interactive = ["angle", "strength", "epsilon", "qaoa"].includes(
    lesson.kind,
  );
  if (interactive) {
    const labels = {
      angle: ["NARROW RANGE", "WIDE RANGE"],
      strength: ["LOWER C", "HIGHER C"],
      epsilon: ["NARROW BAND", "WIDE BAND"],
      qaoa: ["COST + MIX", "CHANGE ANGLES"],
    }[lesson.kind];
    p.button(
      "guide-demo",
      labels[s.guideValue ? 1 : 0] + " ↔",
      visualX + (visualW - 200) / 2,
      bottom - 28,
      200,
      25,
      () => on("guide-demo"),
    );
  }
  p.button(
    "guide-back",
    "◀ BACK",
    x + 25,
    y + h - 47,
    95,
    29,
    () => on("guide-step", -1),
    { disabled: step === 0 },
  );
  if (s.guideIntro) {
    p.button("guide-skip", "SKIP", x + 132, y + h - 47, 65, 29, () =>
      on("guide-play"),
    );
    p.button(
      "guide-next",
      step === 7 ? "BUILD ENGINE ▶" : "NEXT ▶",
      x + w - 164,
      y + h - 47,
      139,
      29,
      () => on(step === 7 ? "guide-play" : "guide-step", 1),
      { tone: "hot" },
    );
  } else {
    p.button(
      "guide-tour",
      "SHOW ME",
      x + (w - 82) / 2,
      y + h - 47,
      82,
      29,
      () => on("guide-tour"),
    );
    p.button(
      "guide-next",
      "NEXT ▶",
      x + w - 132,
      y + h - 47,
      107,
      29,
      () => on("guide-step", 1),
      { disabled: step === 7 },
    );
  }
}

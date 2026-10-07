import { color } from "./paint.js";
// An indeterminate instrument, not a fake percentage or clickable action.
export function evaluation(p, x, y, w, time) {
  p.text("EVALUATING", x + w / 2, y + 8, 10, color.amber, "center");
  const count = 12, gap = 3, cell = (w - gap * (count - 1)) / count;
  const head = time ? Math.floor(time * 12) % (count + 4) : -1;
  for (let i = 0; i < count; i++) {
    const distance = head - i;
    const lit = !time || (distance >= 0 && distance < 4);
    p.rect(x + i * (cell + gap), y + 22, cell, 4,
      lit ? color.amber : "#365852");
    if (time && distance === 0)
      p.rect(x + i * (cell + gap), y + 22, cell, 1, "#ffe3a6");
  }
}

import { color } from "./paint.js";
export function trim(p, W, H, time, running) {
  // Cast corner brackets, inset vents and copper relay pipes; all code-native.
  for (const [x, y, dx, dy] of [
    [4, 4, 1, 1],
    [W - 4, 4, -1, 1],
    [4, H - 4, 1, -1],
    [W - 4, H - 4, -1, -1],
  ]) {
    p.line(
      [
        [x, y + dy * 35],
        [x, y],
        [x + dx * 35, y],
      ],
      "#90b1a577",
      3,
    );
    p.line(
      [
        [x + dx * 6, y + dy * 28],
        [x + dx * 6, y + dy * 6],
        [x + dx * 28, y + dy * 6],
      ],
      "#071f22",
      2,
    );
  }
  if (W < 920) return;
  const vx = W * 0.69;
  for (let i = 0; i < 15; i++) {
    p.rect(vx + i * 8, 17, 4, 18, "#092427");
    p.rect(vx + i * 8 + 1, 18, 1, 16, "#79998a44");
  }
  for (let i = 0; i < 3; i++) {
    p.circle(
      W - 220 + i * 17,
      29,
      4,
      running ? ["#ffc871", "#ed9d48", "#b78953"][i] : "#4e7366",
      "#071c20",
    );
  }
}
export function relay(p, box, time) {
  const { x, y, w, h } = box,
    t = (time * 0.35) % 1;
  const g = p.c.createLinearGradient(x, y, x + w, y);
  g.addColorStop(0, "#ffc06c00");
  g.addColorStop(0.5, "#ffc06c3f");
  g.addColorStop(1, "#ffc06c00");
  p.rect(x + w * t - 12, y, 24, h, g);
}

import { color } from "./paint.js";

export function hintButton(p, on, x, y) {
  p.button("hint", "", x, y, 34, 30, () => on("hint"));
  p.hits.at(-1).label = "Ask Betty for a hint";
  const cx = x + 17, cy = y + 14;
  // Stepped amber glass and a mint screw base match the console's pixel metalwork.
  p.rect(cx - 4, cy - 8, 8, 2, "#ffe4a2");
  p.rect(cx - 6, cy - 6, 12, 6, color.amber);
  p.rect(cx - 4, cy, 8, 3, "#e6973c");
  p.rect(cx - 3, cy + 3, 6, 2, "#e6973c");
  p.rect(cx - 4, cy - 5, 2, 4, "#ffe4a2");
  p.line([[cx - 2, cy - 2], [cx, cy + 1], [cx + 2, cy - 2]], "#855126", 1);
  p.rect(cx - 3, cy + 6, 6, 2, color.mint);
  p.rect(cx - 2, cy + 9, 4, 1, "#759d8a");
  for (const direction of [-1, 1]) {
    p.line([[cx + direction * 10, cy - 7], [cx + direction * 12, cy - 9]], "#edbd72", 1);
    p.rect(cx + direction * 11 - 1, cy - 1, 3, 1, "#edbd72");
  }
}

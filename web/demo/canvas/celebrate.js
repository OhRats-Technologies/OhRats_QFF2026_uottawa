import { color } from "./paint.js";
import { beatrice } from "./beatrice.js";
// Finish screen: Betty cheers over pixel confetti; reduced motion stays still.
const confettiColors = [
  color.amber,
  color.mint,
  color.copper,
  color.blue,
  "#f3c46a",
];
function confetti(p, W, H, time) {
  for (let i = 0; i < 90; i++) {
    const speed = 38 + ((i * 37) % 50),
      sway = Math.sin(time * 2 + i) * 6,
      x = ((i * 97.3) % W) + sway,
      y = ((time * speed + i * 71) % (H + 40)) - 20,
      size = 3 + (i % 3);
    p.rect(
      x,
      y,
      size,
      size + (i % 2),
      confettiColors[i % confettiColors.length],
    );
  }
}
export function celebration(p, s, on, W, H, time) {
  p.rect(0, 0, W, H, "#031218d9");
  confetti(p, W, H, time);
  const seasons = on.rounds || 3,
    w = Math.min(W - 32, 470),
    size = Math.min(130, (H - 24) * 0.34),
    head = size * 0.3,
    h = Math.min(H - 24, size + head + 200),
    x = (W - w) / 2,
    y = (H - h) / 2;
  p.rect(x + 3, y + 4, w, h, "#00000066");
  p.rect(x, y, w, h, "#102c2ff8");
  p.line(
    [
      [x, y],
      [x + w, y],
      [x + w, y + h],
      [x, y + h],
      [x, y],
    ],
    color.amber,
    2,
  );
  // Twinkling pixel stars around Betty while she cheers.
  const spots = [
    [-0.8, -0.1],
    [0.8, -0.1],
    [-0.6, -0.5],
    [0.6, -0.5],
    [-0.95, 0.3],
    [0.95, 0.3],
  ];
  spots.forEach(([dx, dy], i) => {
    if (time && Math.floor(time * 4 + i * 1.7) % 3 === 0) return;
    const sx = x + w / 2 + dx * size,
      sy = y + 24 + head + size / 2 + dy * size,
      tone = i % 2 ? color.amber : "#fff3cf";
    p.rect(sx - 1, sy - 4, 2, 8, tone);
    p.rect(sx - 4, sy - 1, 8, 2, tone);
  });
  // Headroom above Betty keeps her bounce inside the panel.
  const by = y + 24 + head;
  beatrice(p, x + w / 2 - size / 2, by, size, time, { cheer: true });
  const top = by + 6 + size;
  p.text(
    "CONGRATULATIONS!",
    x + w / 2,
    top,
    W < 500 ? 18 : 22,
    color.amber,
    "center",
  );
  p.text(
    `You finished all ${seasons} seasons. Great engineering!`,
    x + w / 2,
    top + 30,
    W < 500 ? 11 : 13,
    color.mint,
    "center",
  );
  // Best recorded error per season from the saved run history.
  const best = Array.from({ length: seasons }, (_, round) => {
    const runs = (s.history || []).filter((r) => r.round === round);
    return runs.length ? Math.min(...runs.map((r) => r.mae)).toFixed(1) : "—";
  });
  p.text(
    `BEST MAE · ${best.map((v, i) => `S${i + 1} ${v}`).join("  ")}`,
    x + w / 2,
    top + 56,
    W < 500 ? 10 : 11,
    color.dim,
    "center",
  );
  // Only the dismiss control is live over the finished workbench.
  p.hits = [];
  p.button(
    "celebrate-done",
    "BACK TO MENU",
    x + w / 2 - 80,
    y + h - 52,
    160,
    32,
    () => on("celebrate-done"),
    { tone: "hot" },
  );
}

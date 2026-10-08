import { color } from "./paint.js";
import { beatrice } from "./beatrice.js";
import { animal } from "./animals.js";
import { pixelForest } from "./pixel-forest.js";
// Finish scene: Betty and a forest cast hop in a rolling wave on the forest
// floor, like an ending cast roll. Reduced motion (time 0) stays still.
const confettiColors = [
  color.amber,
  color.mint,
  color.copper,
  color.blue,
  "#f3c46a",
];
function sparkles(p, W, top, time) {
  for (let i = 0; i < 70; i++) {
    const speed = 30 + ((i * 37) % 45),
      x = ((i * 97.3) % W) + Math.sin(time * 2 + i) * 6,
      y = ((time * speed + i * 71) % (top + 30)) - 20,
      size = 3 + (i % 3);
    p.rect(x, y, size, size, confettiColors[i % confettiColors.length]);
  }
  // Fireflies drift low over the forest floor.
  for (let i = 0; i < 14; i++) {
    const x = (i * 131.7 + Math.sin(time * 0.7 + i) * 30) % W,
      y = top - 40 - ((i * 53) % 120) + Math.cos(time * 1.3 + i) * 8;
    if (!time || Math.sin(time * 3 + i * 2) > -0.3)
      p.rect(x, y, 3, 3, "#fff3a8");
  }
}
function shadow(p, x, y, rx) {
  p.c.fillStyle = "#00000055";
  p.c.beginPath();
  p.c.ellipse(x, y, Math.max(2, rx), 4, 0, 0, Math.PI * 2);
  p.c.fill();
}
// Rolling-wave hop: each member peaks a little after its neighbour.
const hop = (time, phase, height) =>
  time ? Math.abs(Math.sin(Math.PI * (time / 0.7 + phase))) * height : 0;
export function celebration(p, s, on, W, H, time) {
  const seasons = on.rounds || 3,
    narrow = W < 640,
    hero = Math.min(150, W * 0.27, H * 0.24);
  // Code-drawn pixel forest; its grass line is where the cast stands.
  const top = Math.round(pixelForest(p, W, H, time));
  sparkles(p, W, top, time);
  const lineup = narrow
    ? [
        ["fox", 0.12, 0.6],
        ["hare", 0.27, 0.48],
        ["bear", 0.76, 0.58],
        ["owl", 0.91, 0.46],
      ]
    : [
        ["moose", 0.13, 1.05],
        ["fox", 0.27, 0.62],
        ["hare", 0.39, 0.5],
        ["owl", 0.62, 0.48],
        ["bear", 0.74, 0.66],
        ["hare", 0.87, 0.5],
      ];
  lineup.forEach(([kind, at, scale], i) => {
    const size = hero * scale,
      lift = hop(time, i * 0.14, size * 0.35),
      x = W * at;
    shadow(p, x, top + 2, size * 0.35 * (1 - lift / (size * 0.9)));
    animal(p, kind, x, top - lift, size, at > 0.5);
  });
  // Betty takes centre stage with her own cheering bounce.
  shadow(p, W / 2, top + 2, hero * 0.32);
  beatrice(p, W / 2 - hero / 2, top - hero * 1.02, hero, time, {
    cheer: true,
  });
  // Title in the sky with hard pixel drop shadows instead of a dark band.
  const ty = Math.max(40, H * 0.13),
    say = (text, y, size, tone) => {
      const d = Math.max(2, Math.round(size / 8));
      p.text(text, W / 2 + d, y + d, size, "#0b1418", "center");
      p.text(text, W / 2, y, size, tone, "center");
    };
  say("CONGRATULATIONS!", ty, narrow ? 22 : 34, color.amber);
  say(
    `You finished all ${seasons} seasons. The whole forest is cheering!`,
    ty + (narrow ? 28 : 38),
    narrow ? 11 : 15,
    "#f4ead8",
  );
  const best = Array.from({ length: seasons }, (_, round) => {
    const runs = (s.history || []).filter((r) => r.round === round);
    return runs.length ? Math.min(...runs.map((r) => r.mae)).toFixed(1) : "—";
  });
  say(
    `BEST MAE · ${best.map((v, i) => `S${i + 1} ${v}`).join("  ")}`,
    ty + (narrow ? 50 : 64),
    narrow ? 10 : 12,
    color.mint,
  );
  // Only the dismiss control is live over the finished workbench.
  p.hits = [];
  p.button(
    "celebrate-done",
    "BACK TO MENU",
    W / 2 - 80,
    Math.min(H - 44, top + (H - top) / 2 - 16),
    160,
    32,
    () => on("celebrate-done"),
    { tone: "hot" },
  );
}

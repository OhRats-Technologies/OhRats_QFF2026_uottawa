import { beatrice } from "./beatrice.js";
import { color } from "./paint.js";
import { dialogueArrow } from "./dialogue.js";
import { FULL_HELP_DEPTH } from "./coach-copy.js";

function wrap(c, text, width) {
  const lines = []; let line = "";
  for (const word of text.split(" ")) {
    const next = line ? `${line} ${word}` : word;
    if (line && c.measureText(next).width > width) { lines.push(line); line = word; }
    else line = next;
  }
  return [...lines, line];
}
export function drawCoach(p, coach, on, W, H, time) {
  if (!coach.open) return;
  const underlying = [...p.hits];
  coach.boardHits = underlying;
  p.hits = underlying.filter((hit) => hit.id === "sound");
  const w = Math.min(500, W - 24), size = 12,
    text = coach.busy
      ? "I'm checking specific input combinations and settings against this season's contract. Your current engine stays right where it is."
      : coach.solving
        ? "Watch my paw connect the signals and dial in the tested settings. Your engine tests next."
        : coach.waiting
          ? "The settings are connected. Let's run the normal season test and check whether this engine meets your contract."
          : coach.pages?.[coach.page] || "Ask me for a specific build, and I'll check its inputs and settings against this season's challenge.",
    key = `${coach.generation}:${coach.page}:${coach.busy}:${coach.solving}:${coach.waiting}`;
  p.c.font = `${size}px ui-monospace, SFMono-Regular, Menlo, Consolas, monospace`;
  const lines = wrap(p.c, text, w - 106), h = Math.max(coach.solving ? 140 : 170, 86 + lines.length * 18),
    x = W - w - 12, bottom = Math.max(60, H - h - 76),
    target = underlying.find((hit) => hit.id === coach.cursor?.id),
    overlaps = target && target.x + target.w > x && target.y + target.h > bottom && target.y < bottom + h,
    y = coach.solving && overlaps ? 60 : bottom;
  p.frame(x, y, w, h);
  beatrice(p, x + 16, y + 34, 63, time, { greet: true, fireAt: time - 1 });
  p.text("BETTY", x + 90, y + 29, 12, color.amber);
  const speech = coach.dialogue.read(key, text, time);
  if (speech.voice) on.audio.voice(text, speech.count);
  let left = speech.text.length;
  lines.forEach((line, i) => {
    p.text(line.slice(0, Math.max(0, left)), x + 90, y + 52 + i * 18, size);
    left -= line.length + 1;
  });
  p.button("coach-close", "×", x + w - 45, y + 16, 28, 27, () => on("coach-close"));
  p.hits.at(-1).label = coach.solving ? "Stop Betty assistance" : "Close Betty hint";
  const by = y + h - 43;
  if (coach.depth >= FULL_HELP_DEPTH && coach.plan?.recommendation && !coach.busy && !coach.solving && !coach.waiting)
    p.button("coach-solve", "SHOW ME", x + 90, by, 118, 29, () => on("coach-solve"), { tone: "hot" });
  if (!coach.busy && !coach.solving && !coach.waiting) {
    const more = coach.depth < FULL_HELP_DEPTH && !coach.plan?.complete;
    p.button("coach-next", "", x + w - (more ? 172 : 72), by,
      more ? 148 : 48, 29, () => on("coach-next"));
    p.hits.at(-1).label = "Continue Betty hint";
    if (more) p.text("MORE HINT", x + w - 113, by + 14, 11, color.mint, "center");
    dialogueArrow(p, x + w - 46, by + 14, time, 1, !speech.typing);
  } else {
    for (let i = 0; i < 3; i++)
      p.circle(x + w - 65 + i * 13, by + 14, 3,
        !time || Math.floor(time * 3) % 3 === i ? color.amber : color.dim);
  }
  if (coach.cursor) {
    const cursor = coach.cursor, hit = underlying.find((h) => h.id === cursor.id),
      target = hit ? { x: hit.x + hit.w / 2, y: hit.y + hit.h / 2 } : { x: W / 2, y: 120 },
      t = time ? Math.min(1, (performance.now() - cursor.start) / 320) : 1,
      ease = t * t * (3 - 2 * t),
      cx = cursor.from.x + (target.x - cursor.from.x) * ease,
      cy = cursor.from.y + (target.y - cursor.from.y) * ease;
    cursor.position = { x: cx, y: cy };
    cursor.targetVisible = !!hit;
    if (hit) {
      p.line([[hit.x, hit.y], [hit.x + hit.w, hit.y], [hit.x + hit.w, hit.y + hit.h],
        [hit.x, hit.y + hit.h], [hit.x, hit.y]], color.amber, 2);
    }
    p.circle(cx, cy, 11 + (time ? Math.sin(time * 12) * 2 : 0), "#ffb65322", color.amber);
    beatrice(p, cx + 8, cy - 35, 34, time, { cheer: true });
    p.line([[cx + 9, cy + 13], [cx, cy], [cx + 2, cy + 18]], color.mint, 3);
  }
}

import { color } from "./paint.js";
// Permanent foundry strip: explains whichever selector cartridge is loaded.
const notes = {
  none: [
    "SELECTOR CARTRIDGES",
    "Pick a cartridge to find four signals for your engine.",
  ],
  mi: [
    "MI · MUTUAL INFORMATION",
    "Pick the four signals most related to fire size.",
  ],
  exact: [
    "EXACT",
    "Search all 4,845 combinations and pick the lowest-cost subset.",
  ],
  qaoa: [
    "QAOA + SQD",
    "QAOA samples signal combinations. SQD picks the lowest-cost sample.",
  ],
  uniform: [
    "UNIFORM",
    "Sample random combinations and keep the lowest-cost subset.",
  ],
};
function wrap(c, line, width, size) {
  c.font = `${size}px ui-monospace, SFMono-Regular, Menlo, Consolas, monospace`;
  const out = [];
  let row = "";
  for (const word of line.split(" ")) {
    const next = row ? `${row} ${word}` : word;
    if (row && c.measureText(next).width > width) {
      out.push(row);
      row = word;
    } else row = next;
  }
  out.push(row);
  return out;
}
// Draws the note for `method` and returns the height it used.
export function foundryNote(p, method, x, y, w, compact) {
  const [label, text] = notes[method] || notes.none,
    size = compact ? 11 : 12,
    lead = size * 1.35,
    body = wrap(p.c, `${label} — ${text}`, w - 24, size),
    h = body.length * lead + 14;
  p.rect(x, y, w, h, "#0b2427");
  p.rect(x, y, 3, h, color.amber);
  body.forEach((line, i) => {
    const ly = y + 7 + lead / 2 + i * lead;
    if (i === 0) {
      // The cartridge name leads the first line in amber.
      p.text(label, x + 12, ly, size, color.amber);
      p.c.font = `${size}px ui-monospace, SFMono-Regular, Menlo, Consolas, monospace`;
      const off = p.c.measureText(label).width;
      p.text(line.slice(label.length), x + 12 + off, ly, size, color.mint);
    } else p.text(line, x + 12, ly, size, color.mint);
  });
  return h;
}

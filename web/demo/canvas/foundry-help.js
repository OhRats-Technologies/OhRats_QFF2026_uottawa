import { color } from "./paint.js";
// Permanent foundry strip: explains whichever selector cartridge is loaded.
const notes = {
  none: [
    "SELECTOR CARTRIDGES",
    "Each cartridge applies a different feature-selection method to choose four of the twenty input signals. Select a cartridge to view its method.",
  ],
  mi: [
    "MI · MUTUAL INFORMATION",
    "Classical filter method. Signals are ranked by mutual information with the fire-size target; the four highest are retained. Redundancy between signals is not considered.",
  ],
  exact: [
    "EXACT",
    "Classical exhaustive search. All 4,845 four-signal subsets are evaluated; the subset with the minimum selection cost (relevance penalized by redundancy) is returned.",
  ],
  qaoa: [
    "QAOA + SQD",
    "Simulated quantum heuristic. A QAOA circuit raises the probability of low-cost subsets and is sampled; SQD returns the lowest-cost sampled subset. Optimality is not guaranteed.",
  ],
  uniform: [
    "UNIFORM",
    "Random-sampling baseline. Subsets are drawn with equal probability and the lowest-cost sample is returned, providing a control for QAOA sampling.",
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

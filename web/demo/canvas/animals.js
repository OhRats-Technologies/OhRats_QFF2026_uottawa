// Original code-drawn pixel forest cast for the finish scene. Each sprite is a
// list of [x, y, w, h, colour] blocks on its own grid, feet on the bottom row,
// facing right; mirrored sprites face left.
const ink = "#112429";
export const cast = {
  hare: {
    w: 20,
    h: 20,
    blocks: [
      [6, 0, 2, 7, "#c9b79a"], [10, 0, 2, 7, "#c9b79a"],
      [7, 1, 1, 5, "#e8a0a0"], [10, 1, 1, 5, "#e8a0a0"],
      [5, 6, 9, 6, "#c9b79a"], [3, 11, 12, 7, "#c9b79a"],
      [6, 13, 6, 5, "#efe6d2"], [2, 12, 2, 2, "#efe6d2"],
      [11, 8, 1, 1, ink], [13, 9, 1, 1, "#e8a0a0"],
      [4, 18, 4, 2, "#b3a084"], [11, 18, 4, 2, "#b3a084"],
    ],
  },
  fox: {
    w: 24,
    h: 20,
    blocks: [
      [0, 7, 7, 4, "#d9702e"], [0, 7, 2, 4, "#f4ead8"],
      [6, 9, 12, 6, "#d9702e"], [8, 13, 8, 2, "#f4ead8"],
      [16, 2, 2, 3, "#d9702e"], [19, 2, 2, 3, "#d9702e"],
      [16, 3, 1, 2, ink], [20, 3, 1, 2, ink],
      [15, 5, 7, 6, "#d9702e"], [21, 8, 3, 2, "#d9702e"],
      [17, 9, 5, 2, "#f4ead8"], [23, 8, 1, 1, ink], [19, 7, 1, 1, ink],
      [7, 15, 2, 5, "#3b2418"], [10, 15, 2, 5, "#3b2418"],
      [14, 15, 2, 5, "#3b2418"], [17, 15, 2, 5, "#3b2418"],
    ],
  },
  moose: {
    w: 28,
    h: 26,
    blocks: [
      [16, 1, 8, 2, "#d8c39a"], [16, 0, 1, 2, "#d8c39a"],
      [19, 0, 1, 1, "#d8c39a"], [23, 0, 1, 3, "#d8c39a"],
      [8, 7, 8, 3, "#5b3a26"], [4, 9, 16, 9, "#5b3a26"],
      [18, 4, 4, 7, "#5b3a26"], [20, 4, 6, 5, "#6b4630"],
      [24, 6, 4, 4, "#7a5236"], [27, 7, 1, 1, ink],
      [22, 5, 1, 1, ink], [21, 9, 2, 3, "#4a2f1f"],
      [5, 18, 2, 8, "#3a251a"], [9, 18, 2, 8, "#3a251a"],
      [15, 18, 2, 8, "#3a251a"], [18, 18, 2, 8, "#3a251a"],
      [3, 10, 1, 3, "#4a2f1f"],
    ],
  },
  owl: {
    w: 16,
    h: 20,
    blocks: [
      [3, 2, 2, 3, "#8a6a4a"], [11, 2, 2, 3, "#8a6a4a"],
      [3, 4, 10, 14, "#8a6a4a"], [4, 5, 8, 6, "#c9b089"],
      [5, 6, 2, 2, "#ffcf5a"], [9, 6, 2, 2, "#ffcf5a"],
      [6, 7, 1, 1, ink], [10, 7, 1, 1, ink],
      [7, 9, 2, 2, "#e0a040"], [2, 9, 2, 7, "#6e5238"],
      [12, 9, 2, 7, "#6e5238"], [6, 13, 1, 1, "#efe6d2"],
      [9, 14, 1, 1, "#efe6d2"], [7, 16, 1, 1, "#efe6d2"],
      [5, 18, 2, 2, "#e0a040"], [9, 18, 2, 2, "#e0a040"],
    ],
  },
  bear: {
    w: 20,
    h: 18,
    blocks: [
      [11, 1, 2, 2, "#4a3324"], [17, 1, 2, 2, "#4a3324"],
      [3, 7, 14, 9, "#4a3324"], [11, 2, 8, 7, "#4a3324"],
      [6, 11, 7, 4, "#5e4230"], [16, 5, 4, 3, "#8a6a4a"],
      [19, 5, 1, 1, ink], [15, 4, 1, 1, ink],
      [4, 16, 3, 2, "#3a281c"], [8, 16, 3, 2, "#3a281c"],
      [12, 16, 3, 2, "#3a281c"], [2, 9, 1, 2, "#4a3324"],
    ],
  },
};
// Draws `kind` with its feet centred at (x, ground), `size` pixels tall.
export function animal(p, kind, x, ground, size, flip = false) {
  const sprite = cast[kind],
    unit = size / sprite.h,
    c = p.c;
  c.save();
  c.translate(x - (sprite.w * unit) / 2, ground - size);
  c.scale(unit, unit);
  if (flip) {
    c.translate(sprite.w, 0);
    c.scale(-1, 1);
  }
  for (const [bx, by, bw, bh, tone] of sprite.blocks) p.rect(bx, by, bw, bh, tone);
  c.restore();
  return sprite.w * unit;
}

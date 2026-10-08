// Stationary brushed grain: bake once, reuse across every button and frame.
const patterns = new WeakMap();
export function buttonSurface(c, x, y, w, h, disabled) {
  let pattern = patterns.get(c);
  if (!pattern) {
    const tile = document.createElement("canvas");
    tile.width = 128; tile.height = 64;
    const t = tile.getContext("2d");
    let seed = 17491;
    const random = () => {
      seed = Math.imul(seed, 1664525) + 1013904223 | 0;
      return (seed >>> 0) / 4294967296;
    };
    for (let i = 0; i < 650; i++) {
      t.fillStyle = i % 3 ? "#06141724" : "#e4d5b11b";
      t.fillRect(random() * 128 | 0, random() * 64 | 0, 2 + (random() * 14 | 0), 1);
    }
    for (let i = 0; i < 28; i++) {
      t.fillStyle = i % 2 ? "#573d272b" : "#c2a47915";
      t.fillRect(random() * 128 | 0, random() * 64 | 0, 1 + (random() * 3 | 0), 2);
    }
    pattern = c.createPattern(tile, "repeat");
    patterns.set(c, pattern);
  }
  c.save();
  c.translate(x, y);
  c.globalAlpha *= disabled ? 0.18 : 0.4;
  c.fillStyle = pattern;
  c.fillRect(2, 2, w - 4, h - 4);
  c.restore();
}

// Original code-drawn pixel portrait; Beatrice is a fictional Fireline guide.
export function beatrice(p, x, y, size, time = 0) {
  const c = p.c;
  c.save();
  c.translate(x, y);
  c.scale(size / 52, size / 52);
  const ink = "#112429",
    fur = "#8f563c",
    light = "#bf8150",
    gold = "#ffb653";
  const block = (x, y, w, h, color) => p.rect(x, y, w, h, color);
  // Broad, crosshatched tail behind the jacket.
  block(34, 31, 14, 18, ink);
  block(37, 33, 9, 15, "#633e32");
  for (let j = 0; j < 4; j++) {
    block(37, 35 + j * 3, 9, 1, "#9b6644");
    block(38 + j * 2, 33, 1, 15, "#3b302c");
  }
  block(12, 44, 10, 7, ink);
  block(27, 44, 10, 7, ink);
  block(10, 49, 13, 3, "#385353");
  block(27, 49, 13, 3, "#385353");
  block(10, 29, 29, 18, ink);
  block(13, 29, 23, 16, "#d37c31");
  block(12, 34, 25, 3, gold);
  block(15, 39, 19, 3, "#e3d7a1");
  block(23, 31, 2, 14, "#75492e");
  block(7, 29, 7, 11, "#d37c31");
  block(34, 29, 7, 9, "#d37c31");
  block(6, 38, 8, 5, fur);
  block(35, 35, 7, 5, light);
  // Rounded cheeks, ears and muzzle, all on the same pixel grid.
  block(11, 10, 28, 21, ink);
  block(8, 12, 7, 8, fur);
  block(35, 12, 7, 8, fur);
  block(14, 12, 22, 15, fur);
  block(11, 20, 28, 8, fur);
  block(14, 26, 22, 5, light);
  block(16, 20, 18, 8, light);
  block(22, 20, 7, 4, ink);
  const blink = time && Math.floor(time * 1.8) % 9 === 0;
  block(16, 16, 4, blink ? 1 : 4, ink);
  block(31, 16, 4, blink ? 1 : 4, ink);
  if (!blink) {
    block(17, 16, 1, 1, "#f6e9c7");
    block(32, 16, 1, 1, "#f6e9c7");
  }
  block(22, 26, 4, 5, "#f9e7b3");
  block(27, 26, 4, 5, "#f9e7b3");
  // Copper firefighter helmet, with a simple fictional chevron crest.
  block(12, 4, 26, 10, ink);
  block(15, 3, 20, 10, gold);
  block(18, 1, 14, 3, "#f3c46a");
  block(25, 3, 3, 10, "#d18035");
  block(8, 12, 34, 3, ink);
  block(10, 11, 30, 3, gold);
  block(20, 5, 10, 8, "#214345");
  block(23, 6, 4, 2, "#f4d385");
  block(24, 8, 2, 3, "#f4d385");
  // Clipboard: the engineering side of a forest-fire workshop.
  block(35, 35, 12, 15, ink);
  block(37, 37, 8, 11, "#afc2a1");
  block(39, 35, 4, 3, "#67847a");
  for (let j = 0; j < 3; j++) block(38, 40 + j * 2, 6, 1, "#56776c");
  c.restore();
}

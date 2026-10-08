// Bake the wear once. Its pixels stay still as instruments and lights animate.
const surfaces = new WeakMap();
let atlas;

function random(seed) {
  return () => {
    seed = Math.imul(seed, 1664525) + 1013904223 | 0;
    return (seed >>> 0) / 4294967296;
  };
}

function tile(w, h, draw) {
  const canvas = document.createElement("canvas");
  canvas.width = w;
  canvas.height = h;
  draw(canvas.getContext("2d"));
  return canvas;
}

function metalGrain() {
  return tile(128, 128, (c) => {
    const rng = random(8193);
    for (let i = 0; i < 2700; i++) {
      c.fillStyle = i % 3 ? "#020e1214" : "#c5d5aa08";
      c.fillRect(rng() * 128 | 0, rng() * 128 | 0, 1 + (rng() * 4 | 0), 1);
    }
    for (let i = 0; i < 90; i++) {
      c.fillStyle = i % 2 ? "#85b3a509" : "#010b1212";
      c.fillRect(rng() * 128 | 0, rng() * 128 | 0, 8 + (rng() * 27 | 0), 1);
    }
  });
}

function rail(seed, button = false) {
  return tile(1024, 8, (c) => {
    const rng = random(seed);
    c.fillStyle = "#000d1550";
    c.fillRect(0, 5, 1024, 3);
    c.fillStyle = "#aec9af26";
    c.fillRect(0, 1, 1024, 1);
    c.fillStyle = "#00080c85";
    c.fillRect(0, 6, 1024, 1);
    const patches = button ? 7 : 12;
    for (let i = 0; i < patches; i++) {
      const x = rng() * 1024 | 0, width = 3 + (rng() * 8 | 0);
      for (let j = 0; j < width; j++) {
        const depth = 1 + (rng() * (button ? 2 : 4) | 0);
        c.fillStyle = "#201b17";
        c.fillRect(x + j, 2, 1, depth + 1);
        c.fillStyle = j % 3 ? "#735239" : "#a77b48";
        c.fillRect(x + j, 2, 1, depth);
        if (rng() < 0.6) {
          c.fillStyle = "#c7a171";
          c.fillRect(x + j, 1, 1, 1);
        }
        if (rng() < 0.4) {
          c.fillStyle = "#497969";
          c.fillRect(x + j, 3 + depth, 1, 1);
        }
      }
    }
  });
}

function corner(seed) {
  return tile(32, 32, (c) => {
    const rng = random(seed);
    c.beginPath();
    c.moveTo(0, 0);
    for (const [x, y] of [[32, 0], [32, 7], [24, 7], [7, 24], [7, 32], [0, 32]])
      c.lineTo(x, y);
    c.closePath();
    c.clip();
    const face = c.createLinearGradient(0, 0, 24, 24);
    face.addColorStop(0, "#6c8b7a");
    face.addColorStop(0.25, "#3b5f57");
    face.addColorStop(1, "#0c252a");
    c.fillStyle = face;
    c.fillRect(0, 0, 32, 32);
    // Chipped enamel exposes copper at the diagonal casting and outer lip.
    for (let i = 0; i < 110; i++) {
      const x = rng() * 32 | 0, y = rng() * 32 | 0;
      const seam = x < 5 || y < 5 || x + y > 24;
      if (!seam && rng() > 0.09) continue;
      c.fillStyle = ["#1b2422", "#654127", "#a2673b", "#c18b4f", "#527b65"][i % 5];
      c.fillRect(x, y, 1 + (rng() * 3 | 0), 1 + (rng() * 2 | 0));
    }
    c.strokeStyle = "#021419";
    c.lineWidth = 2;
    c.beginPath();
    c.moveTo(30, 7);
    c.lineTo(24, 7);
    c.lineTo(7, 24);
    c.lineTo(7, 31);
    c.stroke();
    c.strokeStyle = "#99693f";
    c.lineWidth = 2;
    c.beginPath();
    c.moveTo(23, 7);
    c.lineTo(7, 23);
    c.stroke();
    c.strokeStyle = "#c2985b80";
    c.lineWidth = 1;
    c.beginPath();
    c.moveTo(21, 7);
    c.lineTo(8, 20);
    c.stroke();
    c.fillStyle = "#a9c1a872";
    c.fillRect(1, 1, 28, 1);
    c.fillRect(1, 1, 1, 28);
  });
}

function fastener() {
  return tile(18, 18, (c) => {
    const disc = (x, y, r, fill) => {
      c.beginPath();
      c.arc(x, y, r, 0, Math.PI * 2);
      c.fillStyle = fill;
      c.fill();
    };
    disc(10, 11, 7, "#031013a0");
    disc(9, 9, 7, "#071a1e");
    disc(9, 9, 6, "#9d7448");
    const face = c.createLinearGradient(4, 3, 13, 15);
    face.addColorStop(0, "#a4b69a");
    face.addColorStop(0.35, "#44665b");
    face.addColorStop(1, "#162c2e");
    disc(9, 9, 4.8, face);
    c.lineWidth = 2;
    c.strokeStyle = "#031719";
    c.beginPath();
    c.moveTo(6, 12);
    c.lineTo(12, 6);
    c.stroke();
    c.lineWidth = 1;
    c.strokeStyle = "#acc3a67a";
    c.beginPath();
    c.moveTo(7, 12);
    c.lineTo(13, 6);
    c.stroke();
    c.fillStyle = "#5c967c";
    c.fillRect(4, 11, 2, 2);
    c.fillStyle = "#dfbc7e";
    c.fillRect(6, 3, 2, 1);
  });
}

function textures(c) {
  if (!atlas) atlas = {
    grain: metalGrain(),
    rail: rail(6931),
    button: rail(337, true),
    corners: [corner(419), corner(765), corner(177), corner(935)],
    screw: fastener(),
  };
  if (!surfaces.has(c)) surfaces.set(c, {
    grain: c.createPattern(atlas.grain, "repeat"),
    rail: c.createPattern(atlas.rail, "repeat"),
    button: c.createPattern(atlas.button, "repeat"),
  });
  return surfaces.get(c);
}

function edge(c, pattern, x, y, length, turn) {
  c.save();
  c.translate(x, y);
  c.rotate(turn * Math.PI / 2);
  c.fillStyle = pattern;
  c.fillRect(0, 0, length, 8);
  c.restore();
}

export function frameMaterial(c, x, y, w, h) {
  const surface = textures(c), alpha = c.globalAlpha;
  c.save();
  c.translate(x, y);
  c.imageSmoothingEnabled = false;
  c.globalAlpha = alpha * 0.55;
  c.fillStyle = surface.grain;
  c.fillRect(8, 8, w - 16, h - 16);
  c.globalAlpha = alpha;
  edge(c, surface.rail, 0, 0, w, 0);
  edge(c, surface.rail, w, 0, h, 1);
  edge(c, surface.rail, w, h, w, 2);
  edge(c, surface.rail, 0, h, h, 3);
  for (const [i, px, py, turn] of [[0, 0, 0, 0], [1, w, 0, 1],
    [2, w, h, 2], [3, 0, h, 3]]) {
    c.save();
    c.translate(px, py);
    c.rotate(turn * Math.PI / 2);
    c.drawImage(atlas.corners[i], 0, 0);
    c.restore();
  }
  // A few worn copper collars punctuate the casting; most paint stays intact.
  for (const px of [2, w - 6]) {
    const py = Math.round(h * 0.5 - 10);
    c.fillStyle = "#07181b";
    c.fillRect(px, py - 2, 5, 24);
    c.fillStyle = "#9c683b";
    c.fillRect(px, py, 3, 20);
    c.fillStyle = "#d2ad74";
    c.fillRect(px, py + 1, 1, 16);
    c.fillStyle = "#4a3829";
    c.fillRect(px + 2, py + 2, 1, 17);
    c.fillStyle = "#497261";
    c.fillRect(px, py + 15, 2, 3);
  }
  c.restore();
}

export function buttonMaterial(c, x, y, w, h, disabled) {
  const surface = textures(c), alpha = c.globalAlpha;
  c.save();
  c.translate(x, y);
  c.beginPath();
  c.rect(0, 0, w, h);
  c.clip();
  c.globalAlpha = alpha * (disabled ? 0.18 : 0.32);
  c.fillStyle = surface.grain;
  c.fillRect(3, 3, w - 6, h - 6);
  c.globalAlpha = alpha * (disabled ? 0.35 : 0.75);
  edge(c, surface.button, 0, 0, w, 0);
  edge(c, surface.button, w, h, w, 2);
  // Recessed bronze end caps leave the label's face unobstructed.
  for (const px of [2, w - 4]) {
    c.fillStyle = "#05161990";
    c.fillRect(px, 5, 3, h - 10);
    c.fillStyle = "#a3724566";
    c.fillRect(px, 6, 1, h - 13);
    c.fillStyle = "#acc7a246";
    c.fillRect(px + 1, 6, 1, 4);
  }
  c.restore();
}

export function screwMaterial(c, x, y) {
  textures(c);
  c.save();
  c.imageSmoothingEnabled = false;
  c.drawImage(atlas.screw, x - 9, y - 9);
  c.restore();
}

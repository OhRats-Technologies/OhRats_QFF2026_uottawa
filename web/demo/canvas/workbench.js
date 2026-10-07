import { trim, relay } from "./chrome.js";
import { color, pixelTitle } from "./paint.js";
import { assessment } from "./session.js";
import { mapPanel, matrixPanel, results } from "./instruments.js";
import { rack, controls, controlsCompact } from "./rack.js";
export function drawWorkbench(
  p,
  s,
  data,
  assets,
  on,
  W,
  H,
  time,
  hover,
  geometry,
) {
  const mobile = W < 920,
    zones = {};
  p.rect(0, 0, W, H, p.c.createPattern(assets.metal, "repeat"));
  p.frame(4, 4, W - 8, H - 8);
  pixelTitle(p, "FIRELINE", 20, 20, mobile ? 2 : 3);
  const header = mobile ? 48 : 56;
  p.button("menu", "≡", W - 136, 13, 34, 30, () => on("menu"));
  p.button(
    "sound",
    on.audio.enabled ? "♫" : "♪",
    W - 92,
    13,
    34,
    30,
    () => on("sound"),
    { active: on.audio.enabled },
  );
  p.button("help", "?", W - 48, 13, 34, 30, () => on("help"));
  if (!mobile) p.text(`SEASON ${s.round + 1} / 3`, 240, 30, 12, color.dim);
  const bottom = H - 65;
  p.frame(12, bottom, W - 24, 53);
  p.button(
    "run",
    s.running ? "RUNNING…" : s.result ? "REPAIR & RUN ▶" : "RUN ENGINE ▶",
    W - 220,
    bottom + 10,
    196,
    33,
    () => on("run"),
    { tone: "hot", disabled: s.running || s.features.length !== s.width },
  );
  p.button(
    "undo",
    "PREVIOUS BUILD",
    24,
    bottom + 10,
    mobile ? 145 : 165,
    33,
    () => on("restore"),
    { disabled: !s.previous },
  );
  if (!mobile && s.result) {
    const i = s.selectedYear;
    p.text(
      `${s.result.years[i]}  OBSERVED ${s.result.actual[i].toFixed(1)}  /  MODEL ${s.result.predicted[i].toFixed(1)} ha/fire`,
      224,
      bottom + 27,
      12,
      color.dim,
    );
  }
  if (mobile) {
    const tabs = [
      ["rack", "BUILD"],
      ["kernel", "ENCODE"],
      ["map", "MAP"],
      ["results", "RESULTS"],
    ];
    tabs.forEach(([id, label], i) =>
      p.button(
        `tab-${id}`,
        label,
        15 + (i * (W - 30)) / 4,
        header + 7,
        (W - 30) / 4 - 5,
        36,
        () => on("tab", id),
        { active: s.tab === id },
      ),
    );
    const box = { x: 12, y: header + 55, w: W - 24, h: bottom - header - 64 };
    Object.assign(zones, { map: box, rack: box, results: box });
    if (s.tab === "rack") rack(p, box, s, data, on);
    if (s.tab === "map") mapPanel(p, box, assets, time, hover);
    if (s.tab === "results") {
      if (H < 500) {
        results(p, { ...box, w: box.w * 0.64 - 6 }, s, on);
        scoreHorizontal(
          p,
          {
            x: box.x + box.w * 0.64 + 6,
            y: box.y,
            w: box.w * 0.36 - 6,
            h: box.h,
          },
          s,
          on,
        );
      } else {
        results(p, { ...box, h: box.h * 0.6 }, s, on);
        scoreHorizontal(
          p,
          { x: box.x, y: box.y + box.h * 0.61, w: box.w, h: box.h * 0.38 },
          s,
          on,
        );
      }
    }
    if (s.tab === "kernel") {
      const rh = Math.min(260, box.h * 0.48);
      zones.encoder = { x: box.x, y: box.y + box.h - rh, w: box.w, h: rh };
      zones.kernel = { ...box, h: box.h - rh - 10 };
      matrixPanel(p, { ...box, h: box.h - rh - 10 }, geometry, time, hover);
      controlsCompact(
        p,
        { x: box.x, y: box.y + box.h - rh, w: box.w, h: rh },
        s,
        on,
        time,
        geometry?.bloch,
      );
    }
  } else {
    const x = 14,
      y = header + 8,
      gap = 12,
      avail = W - 28 - 3 * gap;
    const mapW = avail * 0.21,
      rackW = avail * 0.3,
      kernelW = avail * 0.31,
      controlW = avail * 0.18;
    const chartH = H < 720 ? 168 : Math.min(242, H * 0.28),
      topH = bottom - y - chartH - 17;
    const map = { x, y, w: mapW, h: topH },
      rackBox = { x: x + mapW + gap, y, w: rackW, h: topH };
    const kernel = { x: rackBox.x + rackW + gap, y, w: kernelW, h: topH };
    const ctrl = { x: kernel.x + kernelW + gap, y, w: controlW, h: topH };
    Object.assign(zones, { map, rack: rackBox, kernel, encoder: ctrl });
    mapPanel(p, map, assets, time, hover);
    rack(p, rackBox, s, data, on);
    matrixPanel(p, kernel, geometry, time, hover);
    (ctrl.h < 420 ? controlsCompact : controls)(
      p,
      ctrl,
      s,
      on,
      time,
      geometry?.bloch,
    );
    const lowerY = y + topH + 12;
    zones.results = { x, y: lowerY, w: W * 0.7 - 20, h: chartH };
    results(p, { x, y: lowerY, w: W * 0.7 - 20, h: chartH }, s, on);
    scoreHorizontal(
      p,
      { x: W * 0.7 + 6, y: lowerY, w: W * 0.3 - 20, h: chartH },
      s,
      on,
    );
    // Routed signals cross the mechanical seam, with pulses during calculation.
    for (let j = 0; j < Math.min(s.features.length, 10); j++)
      p.cable(
        rackBox.x + rackW - 6,
        y + 93 + j * 13,
        kernel.x + 7,
        y + 93 + j * 13,
        s.running ? time : 0,
      );
  }
  trim(p, W, H, time, s.running);
  if (s.running)
    relay(
      p,
      { x: W * 0.51, y: header + 60, w: W * 0.3, h: Math.max(50, H * 0.45) },
      time,
    );
  if (s.toast) {
    p.rect(W * 0.2, header + 4, W * 0.6, 30, "#061f24f0");
    p.text(
      s.toast,
      W / 2,
      header + 19,
      Math.min(12, (W * 0.6) / (s.toast.length * 0.62)),
      color.amber,
      "center",
    );
  }
  return zones;
}
function scoreHorizontal(p, b, s, on) {
  const { x, y, w, h } = b;
  p.frame(x, y, w, h, "RUN LOG");
  const a = assessment(s),
    r = s.result;
  if (h < 210) {
    p.text(r ? r.mae.toFixed(1) : "—", x + 26, y + 65, 28, color.amber);
    p.text("ha/fire MAE", x + 26, y + 90, 11, color.dim);
    if (r) {
      p.text(`RBF ${r.rbfMAE.toFixed(1)}`, x + w * 0.55, y + 60, 11);
      p.text(
        `MEAN ${r.meanMAE.toFixed(1)}`,
        x + w * 0.55,
        y + 82,
        11,
        color.dim,
      );
      p.text(`${r.effort} QUBIT·PAIRS`, x + 26, y + 113, 10, color.dim);
    }
    p.text(
      a.won ? "CONTRACT COMPLETE" : "−5% error / −25% effort",
      x + 26,
      y + h - 24,
      10,
      a.won ? color.amber : color.dim,
    );
    if (a.won)
      p.button(
        "next",
        s.round === 2 ? "FINISH →" : "NEXT →",
        x + w - 110,
        y + h - 43,
        85,
        29,
        () => on("next"),
        { tone: "hot" },
      );
    return;
  }
  p.text(r ? r.mae.toFixed(1) : "—", x + 26, y + 81, 38, color.amber);
  p.text("ha/fire MAE", x + 26, y + 113, 12, color.dim);
  if (r) {
    p.text(`RBF ${r.rbfMAE.toFixed(1)}`, x + w * 0.55, y + 62, 12);
    p.text(`MEAN ${r.meanMAE.toFixed(1)}`, x + w * 0.55, y + 89, 12, color.dim);
    p.text(
      `${r.effort} QUBIT·PAIRS`,
      h < 210 ? x + w * 0.55 : x + 26,
      y + (h < 210 ? 120 : 148),
      11,
      color.dim,
    );
  }
  p.text(
    a.won ? "CONTRACT COMPLETE" : "−5% error OR −25% effort",
    x + 26,
    y + h - 39,
    12,
    a.won ? color.amber : color.dim,
  );
  if (a.won)
    p.button(
      "next",
      s.round === 2 ? "FINISH →" : "NEXT →",
      x + w - 114,
      y + h - 53,
      88,
      30,
      () => on("next"),
      { tone: "hot" },
    );
}

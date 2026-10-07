import { trim, relay } from "./chrome.js";
import { color } from "./paint.js";
import { evaluation } from "./evaluation.js";
import { currentResult } from "./auto-test.js";
import { assessment } from "./session.js";
import { scoreHorizontal } from "./runlog.js";
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
  if (!mobile)
    p.text(
      `SEASON ${s.round + 1} / ${on.rounds || 3}${s.round === 3 ? " · 2019–24" : ""}`,
      240,
      30,
      12,
      color.dim,
    );
  const bottom = H - 65;
  p.frame(12, bottom, W - 24, 53);
  const ready = !s.evaluating && !s.running && currentResult(s) && assessment(s).won;
  zones.execution = { x: W - 220, y: bottom + 8, w: 196, h: 37 };
  if (s.evaluating) evaluation(p, W - 200, bottom + 10, 170, time);
  else if (ready) p.button(
    "next", s.round === (on.rounds || 3) - 1 ? "FINISH ▶" : "NEXT SEASON ▶",
    W - 220, bottom + 10, 196, 33, () => on("next"), { tone: "hot" });
  else if (currentResult(s)) p.text(
    `${s.result.mae.toFixed(1)} ha/fire MAE`, W - 34, bottom + 27,
    11, color.dim, "right");
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
  }
  trim(p, W, H, time, s.running);
  if (s.running)
    relay(
      p,
      { x: W * 0.51, y: header + 60, w: W * 0.3, h: Math.max(50, H * 0.45) },
      time,
    );
  if (s.toast) {
    // Desktop messages sit in the free top-bar gap, never over panel titles.
    const tx = mobile ? W * 0.2 : 430,
      tw = mobile ? W * 0.6 : Math.min(460, W * 0.69 - 445),
      ty = mobile ? header + 4 : 13;
    p.rect(tx, ty, tw, 30, "#061f24f0");
    p.text(
      s.toast,
      tx + tw / 2,
      ty + 15,
      Math.min(12, tw / (s.toast.length * 0.62)),
      color.amber,
      "center",
    );
  }
  return zones;
}

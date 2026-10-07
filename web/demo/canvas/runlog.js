import { color } from "./paint.js";
import { assessment } from "./session.js";
// Run log: last error, verdicts against the mean and RBF, contract progress.
const pct = (v) =>
  Math.abs(v) < 0.0005
    ? "0%"
    : `${v > 0 ? "−" : "+"}${Math.abs(v * 100).toFixed(1)}%`;
function verdict(p, label, value, mae, x, right, y, size) {
  const diff = mae - value,
    better = diff < 0;
  p.text(`${label} ${value.toFixed(1)}`, x, y, size, color.dim);
  p.text(
    `${better ? "BEAT" : "BEHIND"} ${better ? "−" : "+"}${Math.abs(diff).toFixed(1)}`,
    right,
    y,
    size,
    better ? color.mint : color.red,
    "right",
  );
}
function progress(s, a) {
  const rows = s.history.filter((r) => r.round === s.round);
  if (a.won) return ["CONTRACT COMPLETE", color.amber];
  if (rows.length < 2) {
    const first = s.starts?.[s.round];
    return first
      ? [
          `TARGET ≤${(first.mae * 0.95).toFixed(1)} MAE OR ≤${Math.floor(first.effort * 0.75)} PAIRS`,
          color.dim,
        ]
      : ["−5% error OR −25% effort", color.dim];
  }
  return [
    `ERROR ${pct(a.gain)} (need −5%) · EFFORT ${pct(a.cost)} (need −25%)`,
    color.dim,
  ];
}
export function scoreHorizontal(p, b, s, on) {
  const { x, y, w, h } = b;
  p.frame(x, y, w, h, "RUN LOG");
  const a = assessment(s),
    r = s.result,
    compact = h < 210,
    size = compact ? 10 : 12,
    col = x + w * 0.5,
    right = x + w - 26;
  p.text(
    r ? r.mae.toFixed(1) : "—",
    x + 26,
    y + (compact ? 65 : 81),
    compact ? 28 : 38,
    color.amber,
  );
  p.text("ha/fire MAE", x + 26, y + (compact ? 90 : 113), size - 1, color.dim);
  if (r) {
    const vy = y + (compact ? 60 : 64),
      gap = compact ? 20 : 26;
    verdict(p, "MEAN", r.meanMAE, r.mae, col, right, vy, size);
    verdict(p, "RBF", r.rbfMAE, r.mae, col, right, vy + gap, size);
    p.text(
      `${r.effort} QUBIT·PAIRS`,
      compact ? col : x + 26,
      y + (compact ? 100 : 148),
      size - 1,
      color.dim,
    );
  }
  const [line, tone] = progress(s, a),
    room = (w - 52) / (line.length * 0.62);
  p.text(
    line,
    x + 26,
    y + h - (compact ? 24 : 39),
    Math.min(size, room),
    tone,
  );
}

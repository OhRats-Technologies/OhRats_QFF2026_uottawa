// Moves dialogue between steps while keeping highlights on their controls.
// time 0 (reduced motion) shows the new layout immediately.
const keys = ["x", "y"],
  duration = 0.42;
let glide = null;
const mix = (a, b, k) =>
  ({ ...b, ...Object.fromEntries(keys.map((key) => [key, a[key] + (b[key] - a[key]) * k])) });

const intersects = (a, b) => a.x < b.x + b.w && a.x + a.w > b.x &&
  a.y < b.y + b.h && a.y + a.h > b.y;

export function settle(step, target, box, time, bounds, protectedAreas = []) {
  if (!time || !glide) glide = { step, at: time, from: { target, box } };
  if (glide.step !== step)
    glide = { step, at: time, from: glide.shown || { target, box } };
  const k = Math.min(1, Math.max(0, (time - glide.at) / duration)),
    e = 1 - (1 - k) ** 3;
  glide.shown = {
    // A moving highlight would cut across labels and point to the wrong control.
    target,
    box: mix(glide.from.box, box, e),
  };
  if (bounds) {
    glide.shown.box.x = Math.max(14, Math.min(bounds.w - box.w - 14, glide.shown.box.x));
    glide.shown.box.y = Math.max(12, Math.min(bounds.h - box.h - 12, glide.shown.box.y));
  }
  // Never sweep the dialogue through the active control. Text always has its
  // final-size container; only position animates on collision-free segments.
  if ([target, ...protectedAreas].some((area) => intersects(glide.shown.box, area)))
    glide.shown.box = box;
  // Fade dialogue after its movement; reduced motion displays it immediately.
  return { ...glide.shown, fade: !time ? 1 : Math.min(1, Math.max(0, (k - 0.55) / 0.45)) };
}

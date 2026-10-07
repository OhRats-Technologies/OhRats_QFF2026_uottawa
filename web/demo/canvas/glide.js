// Eases the tour highlight and speech bubble between steps instead of
// swapping them. time 0 (reduced motion) snaps straight to the new layout.
const keys = ["x", "y", "w", "h"],
  duration = 0.42;
let glide = null;
const mix = (a, b, k) =>
  Object.fromEntries(keys.map((key) => [key, a[key] + (b[key] - a[key]) * k]));

export function settle(step, target, box, time) {
  if (!time || !glide) glide = { step, at: time, from: { target, box } };
  if (glide.step !== step)
    glide = { step, at: time, from: glide.shown || { target, box } };
  const k = Math.min(1, Math.max(0, (time - glide.at) / duration)),
    e = 1 - (1 - k) ** 3;
  glide.shown = {
    target: mix(glide.from.target, target, e),
    box: mix(glide.from.box, box, e),
  };
  // Text waits for the bubble to reach its new size, then fades in.
  return { ...glide.shown, fade: Math.min(1, Math.max(0, (k - 0.55) / 0.45)) };
}

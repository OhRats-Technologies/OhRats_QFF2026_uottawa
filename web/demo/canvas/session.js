export const widths = [2, 4, 6, 10],
  angles = [Math.PI / 32, Math.PI / 16, Math.PI / 8, Math.PI / 4, Math.PI / 2];
export const fresh = () => ({
  menu: true,
  tab: "rack",
  width: 4,
  features: [0, 1, 2, 3],
  angle: Math.PI / 16,
  C: 1,
  epsilon: 0.2,
  round: 0,
  history: [],
  starts: {},
  result: null,
  previous: null,
  foundry: false,
  help: false,
  onboarded: false,
  guideStep: 0,
  guidePage: 0,
  guideValue: 0,
  guideIntro: false,
  selectedYear: 0,
  attempts: 0,
});
export const build = (s) => ({
  features: [...s.features],
  angle: s.angle,
  C: s.C,
  epsilon: s.epsilon,
});
export function load() {
  try {
    const s = JSON.parse(localStorage.getItem("fireline-canvas-v2"));
    if (
      !s ||
      !widths.includes(s.width) ||
      !Array.isArray(s.features) ||
      s.features.length > s.width ||
      new Set(s.features).size !== s.features.length ||
      s.features.some((j) => !Number.isInteger(j) || j < 0 || j >= 20) ||
      !angles.includes(s.angle) ||
      ![0.3, 1, 3, 10].includes(s.C) ||
      ![0.05, 0.2, 0.5].includes(s.epsilon) ||
      ![0, 1, 2].includes(s.round)
    )
      return fresh();
    return {
      ...fresh(),
      ...s,
      menu: true,
      foundry: false,
      help: false,
      guideIntro: false,
      history: (s.history || []).slice(-18),
      toast: "",
      running: false,
      // performance.now() restarts per page load; a saved run starts settled.
      runAt: 0,
    };
  } catch {
    return fresh();
  }
}
export function save(s) {
  try {
    localStorage.setItem("fireline-canvas-v2", JSON.stringify(s));
  } catch {
    /* Storage is optional. */
  }
}
export function toggle(s, j) {
  if (s.features.includes(j)) {
    s.features = s.features.filter((v) => v !== j);
    return "remove";
  }
  if (s.features.length < s.width) {
    s.features.push(j);
    return "patch";
  }
  return null;
}
export function setWidth(s, n) {
  s.width = n;
  s.features = s.features.slice(0, n);
}
export function record(s, result) {
  s.previous = s.result;
  s.result = result;
  s.attempts++;
  s.selectedYear = 0;
  s.starts ||= {};
  s.starts[s.round] ||= { mae: result.mae, effort: result.effort };
  s.history.push({
    round: s.round,
    mae: result.mae,
    effort: result.effort,
    build: result.build,
  });
  s.history = s.history.slice(-18);
}
export function assessment(s) {
  const rows = s.history.filter((r) => r.round === s.round);
  if (!rows.length)
    return { status: "BUILD YOUR FIRST ENGINE", gain: 0, cost: 0 };
  const first = s.starts?.[s.round] || rows[0],
    last = rows.at(-1),
    gain = (first.mae - last.mae) / Math.max(1, first.mae),
    cost = (first.effort - last.effort) / first.effort;
  const won =
    rows.length > 1 &&
    (gain >= 0.05 || (cost >= 0.25 && last.mae <= first.mae * 1.05));
  return {
    status: won
      ? "CONTRACT COMPLETE"
      : rows.length === 1
        ? "TRY ANOTHER BUILD"
        : "KEEP TUNING",
    gain,
    cost,
    won,
  };
}

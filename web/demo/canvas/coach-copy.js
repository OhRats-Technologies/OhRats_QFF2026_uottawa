import { angles } from "./session.js";
export const FULL_HELP_DEPTH = 4;
export const angleLabel = (angle) => ["π/32", "π/16", "π/8", "π/4", "π/2"][angles.indexOf(angle)];
export function coachPages(data, plan) {
  if (plan.complete) return [
    "You met this season's contract! Your choices are locked. Inspect the result, then use Next Season to continue.",
  ];
  if (plan.baseline) return [
    "Your first complete engine sets this season's challenge. Let's assemble four weather signals and measure that starting point first.",
    "Start with Annual Temp. Connect that signal in the rack; we need a complete engine before comparing different builds.",
    "Add Summer Temp next. It describes the hotter part of the year, giving your first engine another climate signal.",
    "Add Annual Rain and Summer Rain next. Leave the angle and regression settings steady while building your starting engine.",
    "Your starting build uses Annual Temp, Summer Temp, Annual Rain and Summer Rain. I can connect it if you'd like.",
  ];
  const r = plan.recommendation, b = r.build,
    names = b.features.map((j) => data.features[j].label),
    missing = b.features.filter((j) => !plan.current.features.includes(j)),
    extra = plan.current.features.filter((j) => !b.features.includes(j)),
    target = (plan.first.mae * 0.95).toFixed(1), limit = (plan.first.mae * 1.05).toFixed(1),
    gain = ((plan.first.mae - r.mae) / plan.first.mae * 100).toFixed(1),
    cheaper = r.effort <= plan.first.effort * 0.75,
    changeWidth = plan.currentWidth !== b.features.length;
  const nudge = (i) => {
    const label = data.features[missing[i] ?? b.features[i % b.features.length]].label;
    return extra[i] !== undefined
      ? `Swap ${data.features[extra[i]].label} for ${label}. Keep the other settings steady while comparing your engine's result.`
      : `Connect ${label} next. It belongs to my checked build; compare the result before changing another setting.`;
  };
  const tuning = b.angle !== plan.current.angle
    ? `Try angle ${angleLabel(b.angle)}. It changes which seasons look similar; keep C and epsilon steady while inspecting the new grid.`
    : b.C !== plan.current.C
      ? `Try C ${b.C}. It changes the penalty for prediction errors; keep epsilon and angle steady while comparing your engine.`
      : b.epsilon !== plan.current.epsilon
        ? `Try epsilon ${b.epsilon}. It changes the error tolerance before penalties apply; keep C and angle steady while comparing your engine.`
        : `Keep angle ${angleLabel(b.angle)}, C ${b.C} and epsilon ${b.epsilon} steady. Concentrate on connecting the suggested signals before changing these settings.`;
  return [
    `Your contract: error below ${target} ha/fire, or 25% less effort while keeping error below ${limit}. Let's choose a tested route.`,
    changeWidth
      ? `Switch to ${b.features.length} inputs first. My checked engine uses that many signals; we'll choose each connection before adjusting its encoding.`
      : missing.length ? nudge(0) : tuning,
    changeWidth ? nudge(0) : missing.length > 1 ? nudge(1) : tuning,
    changeWidth ? tuning : missing.length > 1 ? tuning : nudge(0),
    `Use ${names.slice(0, -1).join(", ")} and ${names.at(-1)}. I tested this exact combination against the current season.`,
    `Set angle ${angleLabel(b.angle)}, C ${b.C} and epsilon ${b.epsilon}. This engine scored ${r.mae.toFixed(1)} ha/fire in my check.`,
    plan.winner
      ? cheaper
        ? `This combination meets the effort contract using ${b.features.length} signals. Betty can connect them and apply those settings for you.`
        : `This combination cuts starting error by ${gain}%, meeting the contract. Betty can connect the inputs and apply these settings for you.`
      : `My best checked build still misses ${target} ha/fire. Try its exact settings to inspect the improvement; the contract stays unchanged.`,
  ];
}

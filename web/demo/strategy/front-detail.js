// Progression prompts expire after a choice; source weather/mechanics stay intact.
export function frontDetail(state, weather) {
  if (state.status !== "playing")
    return "Season finished. Inspect the map or open the season report.";
  if (!state.upgradePending && state.turn === 4)
    return "Heat lifts pressure. Keep crews moving as new fires arrive.";
  if (!state.upgradePending && state.turn === 8)
    return "Two new fires. Rain slows growth; relief is temporary.";
  return weather.detail.replace(/\bturn(s)?\b/g, (_, plural) => `front${plural ?? ""}`);
}

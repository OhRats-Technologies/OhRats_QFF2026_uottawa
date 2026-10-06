// Status shapes describe simulated response, never historical fire footprints.
export function markerDescription(fire, terminal = false) {
  const contained = fire.status === "contained";
  const crew = fire.crew ? terminal ? "Crew assigned · season ended"
    : `Crew returns in ${fire.crew} front${fire.crew === 1 ? "" : "s"}` : "";
  return {
    glyph: contained ? "✓" : String(fire.id),
    badge: fire.crew ? terminal ? "◇" : String(fire.crew) : "",
    tooltip: `${fire.name}\n${contained ? "Contained" : crew || "Burning"}`,
    aria: `${fire.name}, ${fire.status}, pressure ${fire.size.toFixed(1)}${crew ? `, ${crew}` : ""}`,
  };
}

// Source classes: DATA_SCHEMA.md; exact display colours: presentation/assets/map.json.
export const coverClasses = [
  { codes: [210], name: "Coniferous", color: "#245e4b" },
  { codes: [220], name: "Broadleaf", color: "#97b77a" },
  { codes: [230], name: "Mixedwood", color: "#57896a" },
  { codes: [81], name: "Treed wetland", color: "#4d7761" },
  { codes: [80], name: "Wetland", color: "#667f67" },
  { codes: [50], name: "Shrubs", color: "#a4ad73" },
  { codes: [100], name: "Herbs", color: "#b6aa69" },
  { codes: [40], name: "Bryoids", color: "#8b9470" },
  { codes: [32], name: "Rock / rubble", color: "#7f8479" },
  { codes: [33], name: "Exposed / barren", color: "#817b67" },
  { codes: [31], name: "Snow / ice", color: "#c5d5dc" },
  { codes: [20], name: "Water", color: "#163c50" },
  { codes: [0, 255], name: "Unclassified / missing", color: "#40545b" },
];

export function coverLegend() {
  const rows = coverClasses.map(({ codes, name, color }) =>
    `<div class="legend-row" data-cover-codes="${codes.join(",")}" title="Source code ${codes.join(" / ")}"><i aria-hidden="true" style="background:${color}"></i>${name}</div>`,
  ).join("");
  return `<div class="cover-legend-grid">${rows}</div><small>Grey is unclassified or missing, not no vegetation. Categories are not tree density.</small>`;
}

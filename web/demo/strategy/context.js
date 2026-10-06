import { coverLegend } from "./cover-legend.js";

const $ = id => document.getElementById(id);
const descriptions = {
  cover: "Forest cover · 2021", canopy: "Mean canopy height · 2015",
  lorey: "Basal-area-weighted height · 2015", recovery: "Spectral recovery · through 2017",
  water: "Mapped water · 2022", fuel: "Fuel classification · 2026",
};

export class MapContext {
  constructor(layers, series, change) {
    this.layers = layers;
    this.series = series;
    this.change = change;
    this.epoch = 1985;
    $("legend-toggle").setAttribute("aria-controls", "map-legend");
    const option = document.createElement("option");
    option.value = "height";
    option.textContent = "Height history ’85–’15";
    $("layer").append(option);
    const difference = document.createElement("option");
    difference.value = "height-change";
    difference.textContent = "Height difference ’85–’15";
    $("layer").append(difference);
    const strip = document.createElement("div");
    strip.id = "height-epochs";
    strip.setAttribute("role", "group");
    strip.setAttribute("aria-label", "SCANFI height epoch");
    for (const row of series.records) {
      const button = document.createElement("button");
      button.textContent = row.year;
      button.dataset.epoch = row.year;
      button.onclick = () => {this.epoch = row.year; this.render();};
      strip.append(button);
    }
    $("incident-list").before(strip);
    $("layer").onchange = () => this.render();
    $("legend-toggle").onclick = () => {
      $("map-legend").hidden = !$("map-legend").hidden;
      $("legend-toggle").setAttribute("aria-expanded", !$("map-legend").hidden);
      this.legend();
    };
    this.render();
  }
  render() {
    const key = $("layer").value;
    const historical = key === "height";
    const changed = key === "height-change";
    const label = historical ? `Reconstructed height · ${this.epoch} · 480 m samples`
      : changed ? "Estimated height difference · 2015 − 1985 · 480 m samples" : descriptions[key];
    $("map-image").src = key === "cover" ? "../presentation/assets/ontario-cover.png"
      : historical ? this.series.records.find(row => row.year === this.epoch).image
      : changed ? this.change.map.image
      : `assets/context/${key}.png`;
    $("cities").hidden = key === "cover";
    $("map-image").alt = `Full Ontario ${label}; dated visual context, not a game predictor.`;
    $("layer-caption").textContent = label;
    $("height-epochs").hidden = !historical;
    for (const button of document.querySelectorAll("[data-epoch]"))
      button.setAttribute("aria-pressed", Number(button.dataset.epoch) === this.epoch);
    this.legend();
  }
  legend() {
    const key = $("layer").value;
    if (key === "cover") {
      $("map-legend").innerHTML = coverLegend();
    } else if (key === "height") {
      $("map-legend").innerHTML = '<img src="assets/context/height-legend.png" alt="Fixed height scale, zero to thirty metres or higher">'
        + '<small>Nearest 480 m samples. Grey = missing. Zero can include water/nonforest. Retrospective reconstruction; game conditions do not change with epoch.</small>';
    } else if (key === "height-change") {
      $("map-legend").innerHTML = `<img src="${this.change.map.legend}" alt="Estimated height difference: orange minus ten, neutral zero, teal plus ten metres">`
        + '<small>2015 minus 1985. Colour stops at ±10 m; numeric values are retained. Grey = missing. Estimated differences do not identify growth, disturbance or fire effects.</small>';
    } else {
      const layer = this.layers.layers.find(row => row.key === key);
      $("map-legend").innerHTML = `<img src="assets/context/${key}-legend.png" alt="Official ${layer.title} legend">`
        + `<small>${descriptions[key]}. Styled WMS image; no numeric inference from colours.</small>`;
    }
  }
}

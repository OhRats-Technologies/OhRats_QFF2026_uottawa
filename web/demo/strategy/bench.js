import { shuffle } from "./random.js";
import { BenchDetail } from "./bench-detail.js";

const names = [
  "Annual temperature",
  "Summer temperature",
  "Annual rain",
  "Summer rain",
  "Spring rain",
  "Snowfall",
  "Maximum temperature",
  "Minimum temperature",
  "Heating days",
  "Cooling days",
];

export function cost(indices, record) {
  const relevance =
    indices.reduce((sum, index) => sum + record.relevance[index], 0) / 4;
  let redundancy = 0;
  for (let a = 0; a < 4; a++)
    for (let b = a + 1; b < 4; b++)
      redundancy += record.redundancy[indices[a]][indices[b]];
  return -relevance + (0.5 * redundancy) / 6;
}

export class FeatureBench {
  constructor(data) {
    this.data = data;
    this.rng = { rng: 271828 };
    this.subsets = [
      { indices: [0, 1, 2, 3], cost: cost([0, 1, 2, 3], data.record) },
    ];
    this.optimum = data.record.exact_objective;
    this.detail = new BenchDetail(this, names);
    document.querySelector("#sample").onclick = () => this.sample();
    const inspect = document.createElement("button");
    inspect.id = "matrix-mode";
    inspect.textContent = "Inspect ↗";
    inspect.setAttribute("aria-label", "Inspect sampled feature space");
    inspect.onclick = () => this.detail.open();
    document.querySelector(".matrix-panel .section-heading").append(inspect);
    const matrix = document.querySelector("#matrix");
    matrix.setAttribute("role", "button");
    matrix.tabIndex = 0;
    matrix.onclick = () => this.detail.open();
    matrix.onkeydown = (event) => {
      if (event.key === "Enter" || event.key === " ") {
        event.preventDefault();
        this.detail.open();
      }
    };
    this.render();
  }
  get best() {
    return this.subsets.reduce((a, b) => (a.cost < b.cost ? a : b));
  }
  get retained() {
    return [...this.subsets].sort((a, b) => a.cost - b.cost).slice(0, 8);
  }
  sample() {
    for (let count = 0; count < 4; count++) {
      const indices = shuffle(
        Array.from({ length: 10 }, (_, i) => i),
        this.rng,
      )
        .slice(0, 4)
        .sort((a, b) => a - b);
      if (
        !this.subsets.some((item) => item.indices.join() === indices.join())
      ) {
        this.subsets.push({ indices, cost: cost(indices, this.data.record) });
      }
    }
    this.render();
  }
  render() {
    const best = this.best,
      retained = this.retained,
      n = retained.length;
    document.querySelector("#sample-count").textContent = this.subsets.length;
    document.querySelector("#energy").textContent = best.cost.toFixed(3);
    const features = document.querySelector("#feature-subset");
    features.textContent = best.indices.map((i) => names[i]).join(" / ");
    features.title = features.textContent;
    const matrix = document.querySelector("#matrix");
    matrix.setAttribute(
      "aria-label",
      "Inspect diagonal sampled-subspace Hamiltonian; minimum highlighted",
    );
    matrix.style.gridTemplateColumns = `repeat(${n},minmax(0,1fr))`;
    matrix.classList.toggle("dense-preview", n > 4);
    matrix.style.setProperty("--basis-font", n < 3 ? "20px" : "9px");
    matrix.replaceChildren();
    for (let a = 0; a < n; a++) {
      for (let b = 0; b < n; b++) {
        const cell = document.createElement("span");
        cell.className = "projected-cell";
        cell.textContent = a === b ? retained[a].cost.toFixed(2) : "·";
        cell.title =
          a === b
            ? `S${a + 1}: ${retained[a].indices.map((i) => names[i]).join(", ")}; cost ${retained[a].cost.toFixed(6)}`
            : "Off-diagonal exactly zero";
        if (a === b) cell.classList.add("diagonal");
        if (a === 0 && b === 0) cell.classList.add("minimum");
        matrix.append(cell);
      }
    }
    const sample = document.querySelector("#sample");
    sample.title =
      "Four uniform draws on saved coefficients; duplicates do not add another basis state. Not the original QAOA stream.";
    sample.disabled = this.subsets.length === 210;
    const note = document.querySelector(".instrument-note");
    note.textContent = `Gap to all 210 subsets: ${(best.cost - this.optimum).toFixed(3)}. Diagonal H; inspect to compare SQD and classical minima.`;
    note.title = note.textContent;
    if (this.detail.dialog.open) this.detail.render();
  }
}

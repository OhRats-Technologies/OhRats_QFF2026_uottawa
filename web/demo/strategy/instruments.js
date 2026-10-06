import { eigensystem, repair, matrixError, readout, correctReadout, feasible } from "./quantum.js";
import { random } from "./random.js";
import { compareChannel, channelDiagram } from "./channel-comparison.js";
import { matrixCellStyle } from "./matrix-ink.js";

export const techniques = [
  {
    id: "dd",
    name: "Echo sequence",
    kind: "Suppression",
    detail: "XpXm: cancels static idle Z drift in this ideal-pulse toy. Does not undo damping.",
  },
  {
    id: "twirl",
    name: "Pauli twirling",
    kind: "Noise tailoring",
    detail: "Average ± coherent Z over-rotations. Removes directional bias; does not erase the error.",
  },
  {
    id: "postselect",
    name: "Cardinality filter",
    kind: "Error detection",
    detail:
      "Keep only four-of-ten strings. Some corrupted strings still pass; discarded shots reduce your sample.",
  },
  {
    id: "readout",
    name: "Readout calibration",
    kind: "Mitigation",
    detail: "Invert a known symmetric 8% assignment error. Sampling error remains.",
  },
  {
    id: "psd",
    name: "PSD repair",
    kind: "Classical repair",
    detail: "Clip negative eigenvalues of the noisy four-year kernel. Restores PSD, not ideal data.",
  },
  {
    id: "lowrank",
    name: "Low-rank repair",
    kind: "Classical regularization",
    detail: "Retain two positive eigenmodes. Compression can remove noise or useful structure.",
  },
];
const $ = (id) => document.getElementById(id);
export class InstrumentLab {
  constructor(evidence, lens, onChange = () => {}) {
    this.onChange = onChange;
    this.lens = lens;
    this.credits = 1;
    this.unlocked = [];
    this.milestones = new Set();
    const saved = evidence.geometry.find((row) => row.inputs === 4 && row.amplitude_pi_denominator === 32);
    const indices = [0, 8, 16, 24];
    this.ideal = indices.map((i) => indices.map((j) => saved.matrix[i][j]));
    const rng = { rng: 20261006 };
    this.noisy = this.ideal.map((row, i) =>
      row.map((value, j) => readout(value) + (i === j ? 0 : (random(rng) - 0.5) * 0.22)),
    );
    for (let i = 0; i < 4; i++) for (let j = i + 1; j < 4; j++) this.noisy[j][i] = this.noisy[i][j];
    this.strings = Array.from({ length: 32 }, () => {
      const bits = [1, 1, 1, 1, 0, 0, 0, 0, 0, 0];
      return bits.map((bit) => (random(rng) < 0.09 ? 1 - bit : bit));
    });
    this.build();
    this.render();
  }
  build() {
    const panel = document.createElement("section");
    panel.className = "research-panel";
    panel.innerHTML =
      '<div class="section-heading"><span class="eyebrow">Instrument upgrades</span><button id="lab-open">1 credit · Equip ↗</button></div><div id="lab-loadout"></div><p id="lab-summary"></p>';
    document.querySelector(".operations").append(panel);
    document.body.insertAdjacentHTML(
      "beforeend",
      '<dialog id="instrument-dialog"><button id="instrument-close" class="close" aria-label="Close instrument bench">×</button><span class="eyebrow">Separate from fire response</span><h2>Improve the instrument.</h2><p id="instrument-feedback" role="status">Choose a technique. Credits arrive at the start and after fronts 4 and 8.</p><div class="lab-comparisons"><section><h3>Channel control</h3><div id="lab-channel"></div><div id="channel-fidelity"></div><p class="channel-key"><i></i> input <i></i> without techniques <i></i> loadout</p><p class="channel-assumption">Same input · idle 0.7 rad / gate 0.3 rad.<br>Damping/dephasing follow the lens controls.</p></section><section><h3>Kernel / samples</h3><div id="lab-matrix"></div><div id="lab-metrics"></div></section></div><div id="instrument-options"></div><p id="lab-caveat"></p></dialog>',
    );
    $("lab-open").onclick = () => {
      this.render();
      $("instrument-dialog").showModal();
    };
    $("instrument-close").onclick = () => $("instrument-dialog").close();
  }
  progress(state) {
    for (const turn of [4, 8])
      if (state.turn >= turn && !this.milestones.has(turn)) {
        this.milestones.add(turn);
        this.credits++;
      }
    this.render();
  }
  reset() {
    this.credits = 1;
    this.unlocked = [];
    this.milestones.clear();
    this.render();
  }
  restore(ids, turn) {
    this.unlocked = [...ids];
    this.milestones = new Set([4, 8].filter(front => turn >= front));
    this.credits = 1 + this.milestones.size - ids.length;
    if (ids.includes("dd") || ids.includes("twirl")) {
      this.lens.setNoise({management: true});
      $("coherent-noise").checked = true;
    }
    this.render();
  }
  equip(id) {
    if (this.credits < 1 || this.unlocked.includes(id)) return;
    this.credits--;
    this.unlocked.push(id);
    if (["dd", "twirl"].includes(id)) {
      this.lens.setNoise({management: true});
      document.querySelector("#coherent-noise").checked = true;
    }
    const result = this.render();
    const name = techniques.find(item => item.id === id).name;
    const effect = ["dd", "twirl"].includes(id)
      ? `Channel fidelity ${result.channel.beforeFidelity.toFixed(3)} → ${result.channel.afterFidelity.toFixed(3)}.`
      : id === "postselect"
        ? `Samples kept ${result.accepted}/32; ${result.invalid} wrong-cardinality.`
        : `Kernel error ${matrixError(this.noisy, this.ideal).toFixed(3)} → ${result.error.toFixed(3)}.`;
    $("instrument-feedback").textContent = `${name} equipped. ${effect} Fire response unchanged.`;
    $("instrument-close").focus({ preventScroll: false });
    this.onChange();
  }
  render() {
    const owned = (id) => this.unlocked.includes(id);
    $("instrument-feedback").textContent = `${this.credits} credit${this.credits === 1 ? "" : "s"} available. Techniques do not change fire response.`;
    this.lens.setNoise({dd: owned("dd"), twirl: owned("twirl")});
    const theta = this.lens.target, phi = this.lens.phi;
    const input = [Math.sin(theta) * Math.cos(phi), Math.sin(theta) * Math.sin(phi), Math.cos(theta)];
    const channel = compareChannel(input, { idle: 0.7, gate: 0.3,
      dd: owned("dd"), twirl: owned("twirl"),
      damping: this.lens.damping, dephasing: this.lens.dephasing });
    $("lab-channel").innerHTML = channelDiagram(channel);
    $("channel-fidelity").innerHTML =
      `<span>Fidelity to input</span><b data-fidelity="before">${channel.beforeFidelity.toFixed(3)}</b><span>→</span><b data-fidelity="after">${channel.afterFidelity.toFixed(3)}</b>`;
    $("lab-open").textContent = `${this.credits} credit${this.credits === 1 ? "" : "s"} · Equip ↗`;
    $("lab-loadout").textContent = this.unlocked.length
      ? this.unlocked.map((id) => techniques.find((item) => item.id === id).name).join(" / ")
      : "No techniques equipped";
    let matrix = this.noisy.map((row) => row.slice());
    if (owned("readout")) matrix = matrix.map((row) => row.map((value) => correctReadout(value)));
    if (owned("psd") || owned("lowrank")) matrix = repair(matrix, owned("lowrank") ? 2 : 4);
    const eigen = eigensystem(matrix),
      error = matrixError(matrix, this.ideal);
    const accepted = owned("postselect") ? this.strings.filter(feasible) : this.strings;
    const invalid = accepted.filter((bits) => !feasible(bits)).length;
    $("lab-summary").textContent =
      `${accepted.length}/32 samples kept · ${invalid} wrong-cardinality · kernel error ${error.toFixed(3)}`;
    $("instrument-options").innerHTML = techniques
      .map(
        (item) =>
          `<button data-technique="${item.id}" ${owned(item.id) || !this.credits ? "disabled" : ""}><b>${item.name}</b><span>${owned(item.id) ? "Equipped" : item.kind + " / 1 credit"}</span><small>${item.detail}</small></button>`,
      )
      .join("");
    for (const button of document.querySelectorAll("[data-technique]"))
      button.onclick = () => this.equip(button.dataset.technique);
    const matrixBase = getComputedStyle($("instrument-dialog")).backgroundColor.match(/[\d.]+/g).slice(0, 3).map(Number);
    $("lab-matrix").innerHTML = matrix
      .flat()
      .map(
        (value) =>
          `<span style="${matrixCellStyle(value, matrixBase)}">${value.toFixed(2)}</span>`,
      )
      .join("");
    $("lab-metrics").textContent =
      `Minimum eigenvalue ${eigen.at(-1).value.toFixed(4)} · Frobenius error ${error.toFixed(4)} · kept ${accepted.length}/32 · invalid ${invalid}`;
    $("lab-caveat").textContent =
      "Saved ideal 4-qubit kernel, four training years; synthetic readout and entry perturbations added locally. Matrix error is not forecast error. Filtering does not detect all flips; twirling/echo are idealized, and low-rank repair can worsen this example. None of these creates a logical qubit or fault-tolerant QEC.";
    return { channel, error, accepted: accepted.length, invalid };
  }
}

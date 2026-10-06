// Inspect the same local sample costs at readable size; no separate algorithm run.
export class BenchDetail {
  constructor(bench, names) {
    this.bench = bench;
    this.names = names;
    this.mode = "projected";
    this.dialog = document.createElement("dialog");
    this.dialog.id = "bench-dialog";
    this.dialog.setAttribute("aria-labelledby", "bench-title");
    this.dialog.innerHTML = `
      <button class="close" id="bench-close" aria-label="Close feature inspection">×</button>
      <span class="eyebrow">Sample-based feature selection</span>
      <h2 id="bench-title">Sampled Hamiltonian</h2>
      <p class="bench-scope">Selection-proxy costs, not forecast errors. Classical minimum = diagonal SQD.</p>
      <div class="bench-controls">
        <button id="bench-draw">Draw 4 subsets</button>
        <button id="bench-projected" aria-pressed="true">Sampled H</button>
        <button id="bench-redundancy" aria-pressed="false">Redundancy</button>
      </div>
      <div id="bench-visual"></div>
      <div class="bench-minima">
        <div><span>Sampled SQD minimum</span><b id="bench-sqd"></b></div>
        <div><span>Classical sampled minimum</span><b id="bench-classical"></b></div>
        <div><span>All 210 subsets</span><b id="bench-exact"></b></div>
      </div>
      <div id="bench-basis"></div>
      <p id="bench-explanation"></p>
      <small>Local browser arithmetic on saved training coefficients; no addon or hardware runs here.
        These costs measure relevance/redundancy, not predictive error. Diagonal SQD equals the best sampled cost.</small>`;
    document.body.append(this.dialog);
    this.dialog.querySelector("#bench-close").onclick = () =>
      this.dialog.close();
    this.dialog.querySelector("#bench-draw").onclick = () => bench.sample();
    for (const mode of ["projected", "redundancy"]) {
      this.dialog.querySelector(`#bench-${mode}`).onclick = () => {
        this.mode = mode;
        this.render();
      };
    }
  }
  open() {
    this.render();
    this.dialog.showModal();
  }
  render() {
    const { bench, names, mode } = this;
    this.dialog.querySelector("#bench-title").textContent =
      mode === "projected" ? "Sampled Hamiltonian" : "Feature redundancy";
    const retained = bench.retained;
    const labels =
      mode === "projected"
        ? retained.map((_, i) => `S${i + 1}`)
        : names.map((_, i) => String(i + 1));
    const values =
      mode === "projected"
        ? retained.map((subset, a) =>
            retained.map((_, b) => (a === b ? subset.cost : 0)),
          )
        : bench.data.record.redundancy;
    const caption =
      mode === "projected"
        ? `Diagonal Hamiltonian on ${retained.length} lowest-cost distinct samples`
        : "Absolute feature redundancy; numbered inputs listed below";
    const head = labels
      .map((label) => `<th scope="col">${label}</th>`)
      .join("");
    const rows = values
      .map(
        (row, a) =>
          `<tr><th scope="row">${labels[a]}</th>${row
            .map((value, b) => {
              const minimum = mode === "projected" && a === 0 && b === 0;
              return `<td class="${minimum ? "minimum" : ""}" style="--cell:${mode === "redundancy" ? value : 0.08}">${value === 0 ? "0" : value.toFixed(3)}</td>`;
            })
            .join("")}</tr>`,
      )
      .join("");
    this.dialog.querySelector("#bench-visual").innerHTML =
      `<table><caption>${caption}</caption><thead><tr><th></th>${head}</tr></thead><tbody>${rows}</tbody></table>`;
    for (const choice of ["projected", "redundancy"]) {
      this.dialog
        .querySelector(`#bench-${choice}`)
        .setAttribute("aria-pressed", choice === mode);
    }
    for (const id of ["sqd", "classical"])
      this.dialog.querySelector(`#bench-${id}`).textContent =
        bench.best.cost.toFixed(6);
    this.dialog.querySelector("#bench-exact").textContent =
      bench.optimum.toFixed(6);
    const basis =
      mode === "projected"
        ? retained.map(
            (subset, i) =>
              `<div class="bench-basis-row"><b>S${i + 1}</b><code>${names.map((_, j) => (subset.indices.includes(j) ? "1" : "0")).join("")}</code><span>${subset.indices.map((j) => names[j]).join(" · ")}</span></div>`,
          )
        : names.map(
            (name, i) =>
              `<div class="bench-feature-key"><b>${i + 1}</b><span>${name}</span></div>`,
          );
    this.dialog.querySelector("#bench-basis").innerHTML = basis.join("");
    this.dialog.querySelector("#bench-explanation").textContent =
      `${bench.subsets.length} distinct four-of-ten subsets sampled. ` +
      (mode === "projected"
        ? "Each bit string selects four inputs. Projecting this diagonal objective keeps their costs on the diagonal; the lowest eigenvalue is simply the smallest retained cost."
        : "Lighter cells indicate more redundancy between inputs. The objective rewards relevance and penalizes average pairwise redundancy; it is a selection proxy, not the QSVR fidelity kernel.");
  }
}

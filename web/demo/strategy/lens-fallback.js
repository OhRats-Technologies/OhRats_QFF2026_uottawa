// Fixed x/z projection of the same Bloch vector; no WebGL or second noise model.
export class LensFallback {
  constructor(host) {
    host.classList.add("lens-fallback");
    host.innerHTML = `<svg viewBox="0 0 220 210" role="img" aria-label="Bloch-vector x/z projection">
      <desc id="fallback-description"></desc>
      <circle cx="110" cy="100" r="70" class="fallback-grid"/>
      <ellipse cx="110" cy="100" rx="70" ry="18" class="fallback-grid"/>
      <ellipse cx="110" cy="100" rx="24" ry="70" class="fallback-grid"/>
      <path d="M40 100H180 M110 30V170" class="fallback-grid"/>
      <text x="110" y="22">|0⟩</text><text x="110" y="184">|1⟩</text>
      <line id="fallback-vector" x1="110" y1="100" x2="110" y2="100"/>
      <circle id="fallback-tip" cx="110" cy="100" r="3"/>
      <text id="fallback-readout" x="110" y="205"></text>
    </svg>`;
    this.host = host;
    this.line = host.querySelector("#fallback-vector");
    this.tip = host.querySelector("#fallback-tip");
    this.readout = host.querySelector("#fallback-readout");
    this.description = host.querySelector("#fallback-description");
  }
  render([x, y, z]) {
    const px = 110 + 70 * x,
      py = 100 - 70 * z;
    this.line.setAttribute("x2", px);
    this.line.setAttribute("y2", py);
    this.tip.setAttribute("cx", px);
    this.tip.setAttribute("cy", py);
    const length = Math.hypot(x, y, z);
    this.readout.textContent = `x/z projection · |r| ${length.toFixed(2)}`;
    this.description.textContent = `GPU unavailable. Same illustrative Bloch vector: x ${x.toFixed(3)}, y ${y.toFixed(3)}, z ${z.toFixed(3)}. Probability of zero ${((1 + z) / 2).toFixed(3)}. The y coordinate is outside this projection; projected length is not purity.`;
    this.host.dataset.vector = JSON.stringify([x, y, z]);
  }
}

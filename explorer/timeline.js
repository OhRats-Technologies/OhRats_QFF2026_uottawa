// Pointer and keyboard scrubbing, independent of browser range styling.
export class Timeline {
  constructor(element, onChange) {
    this.element = element;
    this.value = 0;
    this.change = onChange;
    element.innerHTML =
      '<div class="scrub-ticks"></div><div class="scrub-rail"></div><div class="scrub-fill"></div><div class="scrub-thumb"><i></i><span></span></div>';
    for (let i = 0; i <= 40; i++) {
      const tick = document.createElement("i");
      tick.style.left = `${i * 2.5}%`;
      tick.className = i % 5 === 0 ? "major" : "";
      element.querySelector(".scrub-ticks").appendChild(tick);
    }
    const update = (e) => {
      const r = element.getBoundingClientRect();
      this.set(Math.max(0, Math.min(8, ((e.clientX - r.left) / r.width) * 8)));
      onChange(this.value);
    };
    element.addEventListener("pointerdown", (e) => {
      if (e.button !== 0) return;
      this.dragging = true;
      element.setPointerCapture(e.pointerId);
      element.classList.add("scrubbing");
      update(e);
    });
    element.addEventListener("pointermove", (e) => {
      if (this.dragging) update(e);
    });
    const end = () => {
      this.dragging = false;
      element.classList.remove("scrubbing");
    };
    element.addEventListener("pointerup", end);
    element.addEventListener("pointercancel", end);
    element.addEventListener("lostpointercapture", end);
    element.addEventListener("keydown", (e) => {
      const step = e.shiftKey ? 0.5 : 0.05;
      const map = {
        ArrowLeft: this.value - step,
        ArrowDown: this.value - step,
        ArrowRight: this.value + step,
        ArrowUp: this.value + step,
        Home: 0,
        End: 8,
      };
      if (!(e.key in map)) return;
      e.preventDefault();
      this.set(Math.max(0, Math.min(8, map[e.key])));
      onChange(this.value);
    });
  }
  set(value) {
    this.value = value;
    const percent = (value / 8) * 100;
    this.element.style.setProperty("--progress", `${percent}%`);
    this.element.setAttribute("aria-valuenow", value.toFixed(3));
    this.element.setAttribute(
      "aria-valuetext",
      `Model time ${value.toFixed(2)} of 8`,
    );
    this.element.querySelector(".scrub-thumb span").textContent =
      value.toFixed(2);
  }
}

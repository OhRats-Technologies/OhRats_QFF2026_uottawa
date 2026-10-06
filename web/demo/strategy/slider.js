// Pointer + keyboard control with a numeric readout; no native range styling.
export class ValueSlider {
  constructor(input, label, onChange) {
    this.min = Number(input.min);
    this.max = Number(input.max);
    this.step = Number(input.step);
    this.onChange = onChange;
    this.node = document.createElement("div");
    this.node.id = input.id;
    this.node.className = "value-slider";
    this.node.tabIndex = 0;
    this.node.setAttribute("role", "slider");
    this.node.setAttribute("aria-label", label);
    this.node.setAttribute("aria-valuemin", this.min);
    this.node.setAttribute("aria-valuemax", this.max);
    this.node.innerHTML =
      '<span class="slider-rail"><i></i><b></b></span><output></output>';
    input.replaceWith(this.node);
    this.set(Number(input.value), false);
    this.node.addEventListener("pointerdown", (event) => {
      if (event.button !== 0) return;
      this.node.focus({ preventScroll: true });
      this.node.setPointerCapture(event.pointerId);
      this.pointer(event);
    });
    this.node.addEventListener("pointermove", (event) => {
      if (this.node.hasPointerCapture(event.pointerId)) this.pointer(event);
    });
    this.node.addEventListener("pointerup", (event) => {
      if (this.node.hasPointerCapture(event.pointerId))
        this.node.releasePointerCapture(event.pointerId);
    });
    this.node.addEventListener("keydown", (event) => {
      const delta = (event.shiftKey ? 10 : 1) * this.step;
      const value = {
        ArrowRight: this.value + delta,
        ArrowUp: this.value + delta,
        ArrowLeft: this.value - delta,
        ArrowDown: this.value - delta,
        PageUp: this.value + this.step * 10,
        PageDown: this.value - this.step * 10,
        Home: this.min,
        End: this.max,
      }[event.key];
      if (value === undefined) return;
      event.preventDefault();
      this.set(value);
    });
  }
  pointer(event) {
    const rect = this.node
      .querySelector(".slider-rail")
      .getBoundingClientRect();
    this.set(
      this.min +
        ((event.clientX - rect.left) / rect.width) * (this.max - this.min),
    );
  }
  set(value, notify = true) {
    this.value = Math.min(
      this.max,
      Math.max(
        this.min,
        Math.round((value - this.min) / this.step) * this.step + this.min,
      ),
    );
    const text = this.value.toFixed(2);
    this.node.style.setProperty(
      "--at",
      `${(100 * (this.value - this.min)) / (this.max - this.min)}%`,
    );
    this.node.setAttribute("aria-valuenow", text);
    this.node.setAttribute("aria-valuetext", text);
    this.node.querySelector("output").textContent = text;
    if (notify) this.onChange(this.value);
  }
}

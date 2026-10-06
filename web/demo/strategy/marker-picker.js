// Disambiguate overlapping pointer hits without moving source coordinates.
export class MarkerPicker {
  constructor(onSelect) {
    this.onSelect = onSelect;
    this.panel = document.createElement("dialog");
    this.panel.id = "nearby-fires";
    this.panel.setAttribute("aria-label", "Nearby fires");
    document.body.append(this.panel);
    window.addEventListener("resize", () => this.close());
    this.panel.addEventListener("close", () => {
      this.opener?.removeAttribute("aria-expanded");
      this.returnFocus?.focus({ preventScroll: true });
    });
    this.panel.addEventListener("click", event => {
      const box = this.panel.getBoundingClientRect();
      if (event.clientX < box.left || event.clientX > box.right ||
          event.clientY < box.top || event.clientY > box.bottom) this.close();
    });
  }
  close() {
    if (this.panel.open) this.panel.close();
  }
  select(event, id, state, buttons) {
    if (!event.detail) return this.onSelect(id);
    const choices = state.incidents.filter(fire => {
      const marker = buttons.get(fire.id);
      if (!marker) return false;
      const box = marker.getBoundingClientRect();
      return fire.id === id || Math.hypot(event.clientX - box.left - box.width / 2,
        event.clientY - box.top - box.height / 2) <= box.width / 2;
    }).sort((a, b) => Number(a.status === "contained") - Number(b.status === "contained") || a.id - b.id);
    if (choices.length < 2) return this.onSelect(id);
    this.opener = this.returnFocus = buttons.get(id);
    this.opener.setAttribute("aria-expanded", "true");
    this.panel.replaceChildren();
    const heading = document.createElement("div");
    heading.className = "nearby-heading";
    heading.innerHTML = '<span>Nearby fires</span><button aria-label="Close nearby fires">×</button>';
    heading.querySelector("button").onclick = () => this.close();
    this.panel.append(heading);
    for (const fire of choices) {
      const button = document.createElement("button");
      button.dataset.pickFire = fire.id;
      button.setAttribute("aria-pressed", fire.id === state.selected);
      const name = document.createElement("b"), detail = document.createElement("span");
      name.textContent = fire.name;
      detail.textContent = fire.status === "contained" ? "Contained"
        : `${fire.size.toFixed(1)} pressure${fire.crew ? " · crew assigned" : ""}`;
      button.append(name, detail);
      button.onclick = () => {
        this.returnFocus = buttons.get(fire.id);
        this.close();
        this.onSelect(fire.id);
      };
      this.panel.append(button);
    }
    this.panel.showModal();
    const box = this.panel.getBoundingClientRect();
    this.panel.style.left = `${Math.max(8, Math.min(event.clientX + 12, innerWidth - box.width - 8))}px`;
    this.panel.style.top = `${Math.max(8, Math.min(event.clientY - box.height / 2, innerHeight - box.height - 8))}px`;
    this.panel.querySelector("[data-pick-fire]").focus({ preventScroll: true });
  }
}

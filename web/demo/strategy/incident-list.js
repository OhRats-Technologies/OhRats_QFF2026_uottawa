// Keep fire controls stable while their pressure ranking and status change.
import { markerDescription } from "./marker-description.js";

export class IncidentList {
  constructor(container, onSelect, fallback) {
    this.container = container;
    this.onSelect = onSelect;
    this.fallback = fallback;
    this.buttons = new Map();
  }
  render(fires, selected, terminal = false) {
    const focused = document.activeElement;
    const hadFocus = this.container.contains(focused);
    const focusedId = focused.dataset.incident;
    const ids = new Set(fires.map((fire) => fire.id));
    for (const [id, button] of this.buttons) {
      if (!ids.has(id)) {
        button.remove();
        this.buttons.delete(id);
      }
    }
    fires.forEach((fire, index) => {
      let button = this.buttons.get(fire.id);
      if (!button) {
        button = document.createElement("button");
        button.className = "incident-chip";
        button.dataset.incident = fire.id;
        button.onclick = () => this.onSelect(fire.id);
        this.buttons.set(fire.id, button);
      }
      button.textContent = `${fire.name} · ${fire.size.toFixed(1)}${fire.crew ? " ◇" : ""}`;
      button.setAttribute("aria-label", markerDescription(fire, terminal).aria);
      button.setAttribute("aria-pressed", selected === fire.id);
      if (this.container.children[index] !== button)
        this.container.insertBefore(button, this.container.children[index] ?? null);
    });
    if (hadFocus) {
      const target = this.buttons.get(Number(focusedId))
        ?? this.buttons.get(selected) ?? this.buttons.get(fires[0]?.id)
        ?? this.fallback;
      target.focus({ preventScroll: true });
    }
  }
}

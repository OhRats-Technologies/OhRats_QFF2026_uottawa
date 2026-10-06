import { markerDescription } from "./marker-description.js";
import { MarkerPicker } from "./marker-picker.js";

export class IncidentMap {
  constructor(source, onSelect) {
    this.frame = document.querySelector("#map-frame");
    this.markers = document.querySelector("#markers");
    this.canvas = document.querySelector("#map-effects");
    this.ctx = this.canvas.getContext("2d");
    this.onSelect = onSelect;
    this.picker = new MarkerPicker(onSelect);
    this.buttons = new Map();
    this.effects = [];
    this.reduced = matchMedia("(prefers-reduced-motion: reduce)").matches;
    this.draw = this.draw.bind(this);
    document.addEventListener("visibilitychange", () => {
      if (document.hidden) {
        cancelAnimationFrame(this.pending);
        this.pending = null;
      } else this.schedule();
    });
    matchMedia("(prefers-reduced-motion: reduce)").addEventListener(
      "change",
      (event) => {
        this.reduced = event.matches;
        this.effects = [];
        this.schedule();
      },
    );
    for (const city of source.city_controls) {
      const label = document.createElement("span");
      label.className = "city";
      label.textContent = city.name;
      label.style.left = `${(city.x / source.width) * 100}%`;
      label.style.top = `${(city.y / source.height) * 100}%`;
      document.querySelector("#cities").append(label);
    }
    new ResizeObserver(() => this.resize()).observe(this.frame);
    this.resize();
    this.schedule();
  }
  resize() {
    const stage = this.frame.parentElement.getBoundingClientRect();
    const width = Math.min(stage.width, (stage.height * 1118) / 1200);
    this.frame.style.width = `${width}px`;
    this.frame.style.height = `${(width * 1200) / 1118}px`;
    const bounds = this.frame.getBoundingClientRect();
    this.width = bounds.width;
    this.height = bounds.height;
    const ratio = Math.min(devicePixelRatio, 2);
    this.canvas.width = Math.round(this.width * ratio);
    this.canvas.height = Math.round(this.height * ratio);
    this.ctx.setTransform(ratio, 0, 0, ratio, 0, 0);
    this.schedule();
  }
  reset() {
    this.picker.close();
    this.buttons.clear();
    this.markers.replaceChildren();
    this.effects = [];
    this.schedule();
  }
  update(state) {
    this.picker.close();
    this.state = state;
    for (const fire of state.incidents.filter((f) => f.status !== "waiting")) {
      let button = this.buttons.get(fire.id);
      if (!button) {
        button = document.createElement("button");
        button.innerHTML = '<span class="fire-number" aria-hidden="true"></span><span class="fire-crew" aria-hidden="true" hidden></span><span class="fire-name" aria-hidden="true"></span>';
        button.style.left = `${fire.x * 100}%`;
        button.style.top = `${fire.y * 100}%`;
        button.style.setProperty("--label-left", fire.x < 0.25 ? "0%" : fire.x > 0.75 ? "100%" : "50%");
        button.style.setProperty("--label-shift", fire.x < 0.25 ? "0%" : fire.x > 0.75 ? "-100%" : "-50%");
        button.onclick = event => this.picker.select(event, fire.id, this.state, this.buttons);
        button.dataset.fire = fire.id;
        this.markers.append(button);
        this.buttons.set(fire.id, button);
      }
      button.className = `fire ${fire.status}${state.selected === fire.id ? " selected" : ""}${fire.crew ? " has-crew" : ""}`;
      const label = markerDescription(fire, state.status !== "playing");
      button.querySelector(".fire-number").textContent = label.glyph;
      button.querySelector(".fire-name").textContent = label.tooltip;
      const badge = button.querySelector(".fire-crew");
      badge.textContent = label.badge;
      badge.hidden = !label.badge;
      button.setAttribute("aria-label", label.aria);
      button.setAttribute("aria-pressed", state.selected === fire.id);
      button.style.setProperty("--pressure", fire.size);
    }
    this.schedule();
  }
  effect(fire, kind) {
    if (this.reduced) return;
    this.effects.push({ x: fire.x, y: fire.y, kind, time: performance.now() });
    this.schedule();
  }
  schedule() {
    if (this.pending != null || document.hidden) return;
    this.pending = requestAnimationFrame((now) => {
      this.pending = null;
      if (!document.hidden) this.draw(now);
    });
  }
  draw(now) {
    const ctx = this.ctx,
      w = this.width,
      h = this.height;
    ctx.clearRect(0, 0, w, h);
    if (this.state) {
      for (const fire of this.state.incidents.filter(
        (f) => f.status === "burning",
      )) {
        const x = fire.x * w,
          y = fire.y * h,
          radius = 7 + Math.min(fire.size, 5) * 4;
        const glow = ctx.createRadialGradient(x, y, 0, x, y, radius * 2.6);
        glow.addColorStop(0, "#ee6e4435");
        glow.addColorStop(1, "#ee6e4400");
        ctx.fillStyle = glow;
        ctx.beginPath();
        ctx.arc(x, y, radius * 2.6, 0, Math.PI * 2);
        ctx.fill();
        if (!this.reduced) {
          for (let n = 0; n < 6; n++) {
            const life = (now * 0.00022 + n * 0.19 + fire.id * 0.1) % 1;
            ctx.globalAlpha = (1 - life) * 0.65;
            ctx.fillStyle = "#ffbd79";
            ctx.beginPath();
            ctx.arc(
              x + Math.sin(n * 8 + fire.id) * 7 + life * 12,
              y - life * radius * 3,
              1.3 * (1 - life),
              0,
              Math.PI * 2,
            );
            ctx.fill();
          }
          ctx.globalAlpha = 1;
        }
        if (fire.crew) {
          ctx.strokeStyle = "#a5e0ca88";
          ctx.lineWidth = 1;
          ctx.setLineDash([3, 4]);
          ctx.beginPath();
          ctx.moveTo(x - 23, y + 23);
          ctx.lineTo(x - 8, y + 8);
          ctx.stroke();
          ctx.setLineDash([]);
          ctx.fillStyle = "#a5e0ca";
          ctx.fillRect(x - 25, y + 21, 4, 4);
        }
      }
    }
    this.effects = this.effects.filter((effect) => now - effect.time < 1400);
    for (const effect of this.effects) {
      const t = (now - effect.time) / 1400,
        x = effect.x * w,
        y = effect.y * h;
      ctx.strokeStyle =
        effect.kind === "water"
          ? `rgba(114,202,235,${1 - t})`
          : `rgba(175,223,179,${1 - t})`;
      ctx.lineWidth = 2;
      ctx.beginPath();
      ctx.arc(x, y, 10 + t * 55, 0, Math.PI * 2);
      ctx.stroke();
      if (effect.kind === "water") {
        ctx.fillStyle = `rgba(114,202,235,${(1 - t) * 0.18})`;
        ctx.beginPath();
        ctx.arc(x, y, 10 + t * 25, 0, Math.PI * 2);
        ctx.fill();
      }
    }
    if (
      !this.reduced &&
      (this.effects.length ||
        this.state?.incidents.some((fire) => fire.status === "burning"))
    )
      this.schedule();
  }
}

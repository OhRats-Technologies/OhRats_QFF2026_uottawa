import { beatrice, bettyCue } from "./beatrice.js";

export const bettyBriefings = {
  question: "Welcome to Fireline! Can 4 qubits and a shallow ZZ kernel predict Ontario's annual wildfire size? Let's check the receipts.",
  data: "One Ontario year, one row: 39,616 NFDB fires aggregated into 31 training years. Extreme fire seasons like 2021 dominate the mean.",
  selection: "8 selectors on 210 candidate subsets. Classical exact QUBO and QAOA + SQD settle on the exact same 4 climate features!",
  development: "Inside chronological training folds, classical RBF holds a clear lead over the quantum ZZ kernel: 77.0 vs 86.6 ha/fire.",
  evaluation: "Six held-out years (2019–2024). Extreme fire years dwarf all models—neither quantum nor classical beats the training baseline.",
  geometry: "Rotating the angle scale changes kernel similarity, but narrow angles become ill-conditioned. Scale is geometry, not advantage!",
  conclusions: "Three core lessons: encoding changes geometry, lower energy ≠ lower error, and more shots don't cure circuit noise.",
  encoding: "Four-qubit linear ZZ circuit: Hadamards for superposition, feature phases P(2θ), and adjacent couplings for state overlap.",
  resources: "Hardware receipts from IBM Marrakesh and Quebec: 12 jobs, 108 QPU seconds, and 301k shots measuring valid candidate yields.",
};

export class BettyPresenter {
  constructor(container, onNotes) {
    this.container = container;
    this.onNotes = onNotes;
    this.canvas = container.querySelector("#betty-canvas");
    this.ctx = this.canvas?.getContext("2d");
    this.textEl = container.querySelector(".betty-text");
    this.bubbleEl = container.querySelector(".betty-bubble");
    this.closeBtn = container.querySelector("#betty-close");
    this.reduced = matchMedia("(prefers-reduced-motion: reduce)");
    this.startTime = performance.now();
    this.currentIndex = 0;
    this.currentId = "question";
    this.minimized = false;
    this.typingTimer = null;
    this.fullText = "";
    this.p = {
      c: this.ctx,
      rect: (x, y, w, h, fill) => {
        if (!this.ctx) return;
        this.ctx.fillStyle = fill;
        this.ctx.fillRect(Math.round(x), Math.round(y), Math.round(w), Math.round(h));
      },
    };
    this.init();
  }

  init() {
    if (!this.canvas) return;
    this.closeBtn?.addEventListener("click", (e) => {
      e.stopPropagation();
      this.toggle();
    });
    this.canvas.addEventListener("click", () => {
      if (this.minimized) this.toggle();
      else if (this.onNotes) this.onNotes();
    });
    this.bubbleEl?.addEventListener("click", () => {
      if (this.typingTimer) {
        this.finishTyping();
      } else if (this.onNotes) {
        this.onNotes();
      }
    });

    const loop = (now) => {
      this.render(now);
      requestAnimationFrame(loop);
    };
    requestAnimationFrame(loop);
  }

  getTime(now) {
    if (this.reduced.matches) return 0;
    return (now - this.startTime) / 1000;
  }

  update(slide, index) {
    this.currentIndex = index;
    this.currentId = slide.id;
    this.fullText = bettyBriefings[slide.id] || slide.notes.slice(0, 140);
    this.typeText(this.fullText);
  }

  typeText(text) {
    clearTimeout(this.typingTimer);
    if (!this.textEl) return;
    if (this.reduced.matches) {
      this.textEl.textContent = text;
      this.typingTimer = null;
      return;
    }
    this.textEl.textContent = "";
    let charIndex = 0;
    const speed = 25; // ms per char
    const step = () => {
      charIndex += 1;
      this.textEl.textContent = text.slice(0, charIndex);
      if (charIndex < text.length) {
        this.typingTimer = setTimeout(step, speed);
      } else {
        this.typingTimer = null;
      }
    };
    step();
  }

  finishTyping() {
    clearTimeout(this.typingTimer);
    this.typingTimer = null;
    if (this.textEl) this.textEl.textContent = this.fullText;
  }

  toggle() {
    this.minimized = !this.minimized;
    this.container.classList.toggle("minimized", this.minimized);
  }

  render(now) {
    if (!this.ctx || !this.canvas) return;
    const time = this.getTime(now);
    const cue = bettyCue("presentation", this.currentIndex, time, `${this.currentId} ${this.fullText}`);
    this.ctx.clearRect(0, 0, this.canvas.width, this.canvas.height);
    beatrice(this.p, 6, 6, 52, time, cue);
  }
}

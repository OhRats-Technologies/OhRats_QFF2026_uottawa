import { contractLocked, choiceAction } from "./contract-lock.js";
import { coachPages, FULL_HELP_DEPTH } from "./coach-copy.js";
import { Dialogue } from "./dialogue.js";

export class BettyCoach {
  constructor(api) {
    this.api = api; this.dialogue = new Dialogue(); this.generation = 0;
    this.clicks = []; this.offered = new Set(); this.open = false;
  }
  cancel() {
    this.generation++; this.worker?.terminate(); this.worker = null;
    this.open = this.busy = this.solving = this.waiting = false;
    this.cursor = null; this.api.state().coaching = false; this.dialogue.reset();
    this.followUp = false;
    this.clicks = []; this.offerAt = null;
  }
  blocks(type) {
    return this.open && !["sound", "auto-test", "coach-patch"].includes(type) &&
      !type.startsWith("coach-");
  }
  note(type, now = performance.now()) {
    if (!choiceAction(type) || this.open) return;
    this.clicks = this.clicks.filter((t) => now - t < 2600);
    this.clicks.push(now);
    const s = this.api.state();
    if (this.clicks.length >= 6 && !this.offered.has(s.round)) this.offerAt = now + 900;
  }
  tick(now) {
    const s = this.api.state();
    if (this.offerAt && now >= this.offerAt && !s.running && !s.menu && !s.help && !s.foundry &&
      !this.open && !contractLocked(s) && !this.api.pending()) {
      this.offered.add(s.round); this.offerAt = null; this.request(false);
    }
  }
  request(explicit = true) {
    this.cancel(); this.open = true; this.plan = null;
    const s = this.api.state(), token = this.generation;
    s.hintDepths ||= {};
    const previous = s.hintDepths[s.round];
    this.depth = Number.isInteger(previous) ? Math.min(6, Math.max(0, previous + (explicit ? 1 : 0))) : 0;
    this.remember(); this.page = this.depth;
    this.api.cancelTests();
    if (s.running) {
      this.busy = true;
      const wait = () => {
        if (token !== this.generation) return;
        if (s.running) setTimeout(wait, 50); else this.request(false);
      };
      setTimeout(wait, 50); return;
    }
    if (contractLocked(s)) {
      this.plan = { complete: true }; this.pages = coachPages(this.api.data, this.plan); this.page = 0; return;
    }
    this.busy = true; this.checked = 0;
    this.api.status("Betty is checking specific builds for this season.");
    this.worker = new Worker(new URL("./coach-worker.js", import.meta.url), { type: "module" });
    this.worker.onmessage = ({ data }) => {
      if (token !== this.generation) return;
      if (data.checked) this.checked = data.checked;
      if (data.plan) {
        this.plan = data.plan; this.pages = coachPages(this.api.data, data.plan);
        this.page = Math.min(this.depth, this.pages.length - 1);
        this.busy = false; this.worker.terminate(); this.worker = null;
        this.api.status(`Betty: ${this.pages[this.page]}`);
        if (this.followUp) { this.followUp = false; this.solve(); }
      }
      if (data.error) this.failure();
    };
    this.worker.onerror = () => { if (token === this.generation) this.failure(); };
    this.worker.postMessage({ data: this.api.data, state: structuredClone(s) });
  }
  failure() {
    this.busy = false; this.worker?.terminate(); this.worker = null;
    this.page = 0;
    this.pages = ["I couldn't finish that check. Your engine is safe; close this bubble and ask me to try again."];
  }
  remember() {
    this.api.state().hintDepths[this.api.state().round] = this.depth;
    this.api.persist();
  }
  handle(type) {
    if (type === "coach-close") { this.cancel(); this.api.schedule(); }
    if (type === "coach-next" && !this.busy && !this.solving && !this.waiting) {
      if (this.dialogue.finish()) return;
      if (this.plan?.complete || !this.plan?.recommendation) { this.cancel(); this.api.schedule(); return; }
      this.depth = Math.min(6, this.depth + 1); this.remember();
      this.page = Math.min(this.depth, this.pages.length - 1);
      this.api.status(`Betty: ${this.pages[this.page]}`);
    }
    if (type === "coach-solve" && this.depth >= FULL_HELP_DEPTH && this.plan?.recommendation &&
      !this.busy && !this.solving && !this.waiting)
      this.solve();
  }
  async solve() {
    const token = this.generation, b = this.plan.recommendation.build,
      baseline = this.plan.baseline, s = this.api.state();
    this.solving = true; s.coaching = true; s.foundry = false;
    this.api.cancelTests();
    const steps = [
      { id: `width-${b.features.length}`, patch: { width: b.features.length,
        features: s.features.slice(0, b.features.length) } },
      ...b.features.map((j, i) => ({ id: `signal-${j}`, patch: { features: b.features.slice(0, i + 1) } })),
      { id: "angle-up", patch: { angle: b.angle } },
      { id: "strength-up", patch: { C: b.C } },
      { id: "epsilon-up", patch: { epsilon: b.epsilon } },
    ];
    for (const step of steps) {
      if (token !== this.generation) return;
      await this.api.navigate(step.id);
      if (token !== this.generation) return;
      this.cursor = { id: step.id, start: performance.now(), from: this.cursor?.position || { x: 80, y: 30 } };
      await new Promise((resolve) => setTimeout(resolve, this.api.reduce ? 0 : 430));
      if (token !== this.generation) return;
      this.api.patch(step.patch);
      this.api.audio.effect("patch");
    }
    this.cursor = null; this.solving = false; this.waiting = true;
    s.coaching = false;
    await this.api.evaluate();
    if (token !== this.generation) return;
    this.waiting = false;
    if (baseline) { this.request(false); this.followUp = true; return; }
    this.plan = contractLocked(s) ? { complete: true } : this.plan;
    this.pages = coachPages(this.api.data, this.plan); this.page = 0; this.dialogue.reset();
    this.api.status(`Betty: ${this.pages[0]}`);
  }
  receipt() {
    return { open: this.open, busy: this.busy, solving: this.solving, waiting: this.waiting,
      page: this.page, depth: this.depth, text: this.pages?.[this.page], checked: this.plan?.checked || this.checked,
      recommendation: this.plan?.recommendation, winner: this.plan?.winner,
      baseline: this.plan?.baseline, complete: this.plan?.complete, cursor: this.cursor?.id || null,
      targetVisible: this.cursor?.targetVisible, position: this.cursor?.position };
  }
}

// Original theme: Ember Relay, D Dorian, 78 BPM, 16-step repeating harmonic cycle.
export class Audio {
  constructor() {
    this.enabled = false;
    this.ctx = null;
    this.timer = null;
    this.step = 0;
    document.addEventListener("visibilitychange", () => this.visibility());
  }
  tone(frequency, time, duration = 0.2, volume = 0.06, type = "triangle") {
    const c = this.ctx;
    if (!c || !this.enabled) return;
    const oscillator = c.createOscillator(),
      gain = c.createGain(),
      filter = c.createBiquadFilter();
    oscillator.type = type;
    oscillator.frequency.value = frequency;
    filter.type = "lowpass";
    filter.frequency.value = 1400;
    gain.gain.setValueAtTime(0, time);
    gain.gain.linearRampToValueAtTime(volume, time + 0.015);
    gain.gain.exponentialRampToValueAtTime(0.0001, time + duration);
    oscillator.connect(filter);
    filter.connect(gain);
    gain.connect(this.master);
    oscillator.start(time);
    oscillator.stop(time + duration + 0.02);
  }
  async toggle() {
    if (!this.ctx) {
      this.ctx = new (window.AudioContext || window.webkitAudioContext)();
      this.master = this.ctx.createGain();
      this.master.gain.value = 0.5;
      this.master.connect(this.ctx.destination);
    }
    this.enabled = !this.enabled;
    if (this.enabled) {
      await this.ctx.resume();
      this.start();
    } else {
      clearInterval(this.timer);
      this.timer = null;
      await this.ctx.suspend();
    }
    return this.enabled;
  }
  start() {
    clearInterval(this.timer);
    const notes = [
      62, 69, 72, 76, 74, 69, 67, 65, 62, 69, 71, 76, 74, 72, 69, 67,
    ];
    const tick = () => {
      if (document.hidden || !this.enabled) return;
      const t = this.ctx.currentTime + 0.03,
        midi = notes[this.step % 16];
      this.tone(440 * 2 ** ((midi - 69) / 12), t, 0.65, 0.035);
      if (this.step % 4 === 0)
        this.tone(
          440 *
            2 ** (([38, 38, 43, 45][Math.floor(this.step / 4) % 4] - 69) / 12),
          t,
          1.35,
          0.065,
          "sine",
        );
      this.step++;
    };
    tick();
    this.timer = setInterval(tick, 60000 / 78 / 2);
  }
  effect(name) {
    if (!this.enabled || document.hidden) return;
    const t = this.ctx.currentTime + 0.01;
    if (name === "run") {
      [62, 65, 69].forEach((n, i) =>
        this.tone(440 * 2 ** ((n - 69) / 12), t + i * 0.09, 0.25, 0.09),
      );
    } else if (name === "win") {
      [62, 69, 74, 76].forEach((n, i) =>
        this.tone(440 * 2 ** ((n - 69) / 12), t + i * 0.12, 0.5, 0.07),
      );
    } else this.tone(name === "remove" ? 180 : 330, t, 0.065, 0.08, "sine");
  }
  async visibility() {
    if (!this.ctx || !this.enabled) return;
    if (document.hidden) {
      clearInterval(this.timer);
      this.timer = null;
      await this.ctx.suspend();
    } else {
      await this.ctx.resume();
      this.start();
    }
  }
}

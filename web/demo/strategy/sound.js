// Generated locally; audio is opt-in after a user gesture.
export class Sound {
  enabled = false;
  async enable(value) {
    if (!value) {
      this.enabled = false;
      this.hush();
      return false;
    }
    try {
      this.context ??= new AudioContext();
      this.prepare();
      await this.context.resume();
      this.enabled = true;
      this.output.gain.setValueAtTime(this.hidden ? 0 : 1, this.context.currentTime);
    } catch {
      this.enabled = false;
      this.unavailable = true;
      this.hush();
    }
    return this.enabled;
  }
  constructor(context = null) {
    this.context = context;
    this.sources = new Set();
    this.hidden = false;
    this.unavailable = false;
    if (context) this.prepare();
  }
  prepare() {
    if (this.output) return;
    this.output = this.context.createGain();
    this.output.connect(this.context.destination);
  }
  hush() {
    this.output?.gain.setValueAtTime(0, this.context.currentTime);
    for (const source of this.sources) source.stop();
    this.sources.clear();
  }
  setHidden(value) {
    this.hidden = value;
    if (value) this.hush();
    else if (this.enabled) this.output.gain.setValueAtTime(1, this.context.currentTime);
  }
  envelope(source, duration, delay, gain, filter = null) {
    const context = this.context, volume = context.createGain();
    const time = context.currentTime + delay;
    volume.gain.setValueAtTime(0.001, time);
    volume.gain.exponentialRampToValueAtTime(gain, time + 0.015);
    volume.gain.exponentialRampToValueAtTime(0.001, time + duration);
    source.connect(filter ?? volume);
    if (filter) filter.connect(volume);
    volume.connect(this.output);
    this.sources.add(source);
    source.onended = () => {
      this.sources.delete(source);
      source.disconnect();
      filter?.disconnect();
      volume.disconnect();
    };
    source.start(time);
    source.stop(time + duration);
  }
  tone(frequency, duration = 0.14, delay = 0, type = "sine", gain = 0.06) {
    if (!this.enabled || this.hidden) return;
    const oscillator = this.context.createOscillator();
    oscillator.type = type;
    oscillator.frequency.setValueAtTime(frequency, this.context.currentTime + delay);
    this.envelope(oscillator, duration, delay, gain);
  }
  texture(frequency, duration, gain, type = "bandpass") {
    if (!this.enabled || this.hidden) return;
    const context = this.context;
    if (!this.noise) {
      this.noise = context.createBuffer(1, context.sampleRate, context.sampleRate);
      const samples = this.noise.getChannelData(0);
      let seed = 20261006;
      for (let i = 0; i < samples.length; i++) {
        seed = (Math.imul(seed, 1664525) + 1013904223) >>> 0;
        samples[i] = 2 * seed / 2 ** 32 - 1;
      }
    }
    const source = context.createBufferSource(), filter = context.createBiquadFilter();
    source.buffer = this.noise;
    filter.type = type;
    filter.frequency.value = frequency;
    filter.Q.value = 0.6;
    this.envelope(source, duration, 0, gain, filter);
  }
  play(kind) {
    if (kind === "crew") {
      this.tone(220);
      this.tone(330, 0.18, 0.06);
    }
    if (kind === "water") {
      this.texture(1200, 0.5, 0.07);
      this.tone(440, 0.2, 0, "triangle", 0.025);
      this.tone(220, 0.25, 0.08, "triangle", 0.025);
    }
    if (kind === "inspect") {
      this.tone(660);
      this.tone(990, 0.16, 0.07);
    }
    if (kind === "advance") {
      this.texture(360, 0.65, 0.06, "lowpass");
      this.tone(140, 0.2, 0, "triangle", 0.025);
    }
    if (kind === "upgrade")
      [220, 440, 660, 880].forEach((frequency, index) =>
        this.tone(frequency, 0.22, index * 0.045),
      );
    if (kind === "won")
      [523, 659, 784, 1046].forEach((frequency, index) =>
        this.tone(frequency, 0.25, index * 0.12),
      );
    if (kind === "lost") {
      this.tone(220, 0.2);
      this.tone(110, 0.35, 0.2);
    }
  }
}

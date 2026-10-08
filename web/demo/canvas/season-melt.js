export const meltOffset = (elapsed, delay, height, duration = 1050) => {
  const t = Math.max(0, Math.min(1, (elapsed - delay) / (duration - delay)));
  return Math.round(height * t * t * (2 - t));
};

export class SeasonMelt {
  start(canvas, reduced, now = performance.now()) {
    this.image = document.createElement("canvas");
    this.image.width = canvas.width;
    this.image.height = canvas.height;
    this.image.getContext("2d").drawImage(canvas, 0, 0);
    this.started = now;
    this.reduced = reduced;
    this.duration = reduced ? 140 : 1050;
    this.delays = Array.from({ length: 80 }, (_, i) =>
      95 + 65 * Math.sin(i * 0.71) + 25 * Math.sin(i * 1.93));
  }
  get active() { return !!this.image; }
  cancel() { this.image = null; }
  draw(c, now) {
    if (!this.image) return;
    const elapsed = now - this.started, image = this.image;
    if (elapsed >= this.duration) { this.cancel(); return; }
    c.save();
    c.setTransform(1, 0, 0, 1, 0, 0);
    c.imageSmoothingEnabled = false;
    if (this.reduced) {
      c.globalAlpha = 1 - elapsed / this.duration;
      c.drawImage(image, 0, 0);
    } else {
      for (let i = 0; i < this.delays.length; i++) {
        const x = Math.floor(i * image.width / this.delays.length),
          end = Math.floor((i + 1) * image.width / this.delays.length),
          y = meltOffset(elapsed, this.delays[i], image.height);
        c.drawImage(image, x, 0, end - x, image.height, x, y, end - x, image.height);
      }
    }
    c.restore();
  }
}

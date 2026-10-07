// A click completes the current line before it advances. No timers survive
// closing the tour; animation and speech are driven by its rendered clock.
export class Dialogue {
  read(key, text, time) {
    if (this.key !== key) {
      this.key = key;
      this.start = time;
      this.complete = false;
      this.spoken = 0;
    }
    const count = !time || this.complete ? text.length :
      Math.min(text.length, Math.floor(Math.max(0, time - this.start - 0.42) * 38));
    this.typing = count < text.length;
    const voice = count > this.spoken && this.typing && !!time;
    this.spoken = count;
    return { text: text.slice(0, count), count, typing: this.typing, voice };
  }
  finish() {
    if (!this.typing) return false;
    this.complete = true;
    this.typing = false;
    return true;
  }
  reset() { this.key = null; }
}
export const dialogue = new Dialogue();
export function dialogueArrow(p, x, y, time, direction = 1, ready = true) {
  const drift = ready && time ? Math.sin(time * 5) * 3 : 0,
    cx = x + drift * direction;
  p.line([[cx - direction * 7, y - 7], [cx + direction * 2, y],
    [cx - direction * 7, y + 7]], ready ? "#ffb653" : "#749b92", 3);
  p.line([[cx - direction * 16, y], [cx, y]], "#aed6b6", 2);
}

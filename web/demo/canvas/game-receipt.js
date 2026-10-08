// Read-only snapshots for browser checks; never provide hidden gameplay actions.
export function gameReceipt({ state, pending, coach, melt, reduce, tour, paint, audio }) {
  window.fireline = {
    coach: () => structuredClone(coach.receipt()),
    transition: () => ({ active: melt.active, reducedMotion: reduce }),
    snapshot: () => structuredClone({ ...state(), running: !!state().running,
      evaluating: pending() || !!state().running }),
    tour: () => structuredClone(tour()),
    controls: () => paint.hits.map(({ id, label, x, y, w, h, disabled }) =>
      ({ id, label, x, y, w, h, disabled })),
    audio: () => ({ enabled: audio.enabled, state: audio.ctx?.state,
      timer: !!audio.timer, playing: audio.playing, track: !!audio.music }),
  };
}

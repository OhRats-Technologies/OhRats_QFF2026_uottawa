export function connectInput(canvas, p, get, on, dirty) {
  function point(e) {
    const r = canvas.getBoundingClientRect();
    return {
      x: (e.clientX - r.left) / get().scale,
      y: (e.clientY - r.top) / get().scale,
    };
  }
  canvas.addEventListener("pointermove", (e) => {
    get().hover(point(e));
    p.hover = p.hits.find((h) => inside(h, get().point()))?.id || "";
    canvas.style.cursor = p.hover ? "pointer" : "default";
  });
  canvas.addEventListener("pointerleave", () => {
    get().hover(null);
    p.hover = "";
  });
  const inside = (h, v) =>
    v.x >= h.x && v.x <= h.x + h.w && v.y >= h.y && v.y <= h.y + h.h;
  canvas.addEventListener("pointerdown", (e) => {
    const pos = point(e),
      hit = p.hits.find((h) => inside(h, pos) && !h.disabled);
    if (!hit) return;
    canvas.setPointerCapture(e.pointerId);
    localDrag = { hit, start: pos, point: pos };
  });
  canvas.addEventListener("pointermove", (e) => {
    if (localDrag) localDrag.point = point(e);
  });
  canvas.addEventListener("pointerup", (e) => {
    if (!localDrag) return;
    const d = localDrag,
      pos = point(e);
    localDrag = null;
    // Controls act on release over the pressed control; dragging never links.
    if (inside(d.hit, pos)) d.hit.action();
  });
  canvas.addEventListener("pointercancel", () => (localDrag = null));
  document.addEventListener("keydown", (e) => {
    if (e.key === "Escape") {
      if (get().state.help) on("guide-close");
      get().state.foundry = false;
      dirty();
    }
    if (e.code === "Space" && e.target === document.body) {
      e.preventDefault();
      on("run");
    }
  });

  let localDrag = null;
  return () => localDrag;
}

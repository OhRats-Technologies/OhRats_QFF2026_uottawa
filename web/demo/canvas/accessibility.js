export function controlMirror(p, a11y, audio, getState) {
  let mirrored = "";
  return function mirror() {
    const s = getState();
    const signature = p.hits
      .map((h) => `${h.id}:${h.label}:${h.disabled}`)
      .join("|");
    if (signature === mirrored) return;
    mirrored = signature;
    const focused = document.activeElement?.dataset?.id;
    a11y.replaceChildren();
    for (const hit of p.hits) {
      const button = document.createElement("button");
      button.dataset.id = hit.id;
      button.textContent = hit.label;
      if (hit.id.includes("sound"))
        button.setAttribute(
          "aria-label",
          audio.enabled ? "Mute music" : "Enable music",
        );
      if (hit.id.endsWith("-down") || hit.id.endsWith("-up"))
        button.setAttribute(
          "aria-label",
          `${hit.id.endsWith("-up") ? "Increase" : "Decrease"} ${hit.id.split("-")[0]}`,
        );
      if (hit.id.startsWith("signal-"))
        button.setAttribute(
          "aria-pressed",
          String(s.features.includes(Number(hit.id.slice(7)))),
        );
      if (hit.id.startsWith("width-"))
        button.setAttribute(
          "aria-pressed",
          String(s.width === Number(hit.id.slice(6))),
        );
      if (hit.id.startsWith("year-") && s.result) {
        const i = Number(hit.id.slice(5));
        button.setAttribute(
          "aria-label",
          `${s.result.years[i]}: observed ${s.result.actual[i].toFixed(1)}, model ${s.result.predicted[i].toFixed(1)} hectares per fire`,
        );
      }
      if (hit.id.startsWith("guide-topic-"))
        button.setAttribute(
          "aria-pressed",
          String(s.guideStep === Number(hit.id.slice(12))),
        );
      button.disabled = !!hit.disabled;
      button.onclick = () => hit.action();
      button.onfocus = () => {
        p.focus = hit.id;
      };
      button.onblur = () => (p.focus = "");
      a11y.append(button);
    }
    let destination =
      a11y.querySelector(`[data-id="${focused}"]`) ||
      (focused?.includes("help")
        ? a11y.querySelector(`[data-id="${s.menu ? "menu-help" : "help"}"]`)
        : null) ||
      (focused?.includes("foundry")
        ? a11y.querySelector('[data-id="foundry"]')
        : null);
    if (destination?.disabled) {
      const id = destination.dataset.id,
        other = id.endsWith("up")
          ? id.replace(/up$/, "down")
          : id.replace(/down$/, "up");
      destination = a11y.querySelector(`[data-id="${other}"]`);
    }
    if (destination) destination.focus({ preventScroll: true });
    else if (s.help || s.foundry)
      (s.guideIntro
        ? a11y.querySelector('[data-id="guide-next"]')
        : a11y.querySelector("button:not(:disabled)")
      )?.focus({ preventScroll: true });
  };
}

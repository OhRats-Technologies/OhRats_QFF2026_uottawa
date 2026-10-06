// N advances from game controls; Space keeps its native button semantics.
export function gameKeyboard(next, respond) {
  document.addEventListener("keydown", (event) => {
    const target = event.target;
    if (
      event.defaultPrevented || event.repeat || event.isComposing ||
      event.ctrlKey || event.metaKey || event.altKey ||
      document.querySelector("dialog[open]") ||
      target.isContentEditable || target.closest?.('[role="slider"]') ||
      ["INPUT", "SELECT", "TEXTAREA"].includes(target.tagName)
    ) return;
    const nextFront = event.key.toLowerCase() === "n" ||
      (event.code === "Space" && !["BUTTON", "A"].includes(target.tagName));
    if (nextFront) {
      event.preventDefault();
      next();
    } else if (["1", "2"].includes(event.key)) {
      event.preventDefault();
      respond({ 1: "crew", 2: "water" }[event.key]);
    }
  });
}

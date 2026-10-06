import { action, advance } from "./rules.js";

// One toy front, through the actual rules. The accepted-move state stays untouched.
export function responsePreview(state, kind = null) {
  const copy = structuredClone(state);
  if (kind && !action(copy, copy.selected, kind)) return null;
  if (!advance(copy)) return null;
  return {
    reserve: copy.integrity,
    loss: copy.damage - state.damage,
    supplies: copy.supplies,
    contained: copy.contained - state.contained,
    status: copy.status,
  };
}

export function previewText(result) {
  if (!result) return "";
  const ending = result.status === "lost" ? " · line breaks" : "";
  return `After this front: ${result.reserve.toFixed(1)} reserve · ${result.supplies} supplies${ending}`;
}

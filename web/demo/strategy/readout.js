import { forecast, impact } from "./rules.js";

// The selected fire's contribution before combined reserve is clamped at zero.
export function incidentProjection(state, fire) {
  if (state.status !== "playing") return { pressure: null, loss: null };
  if (fire.status !== "burning") return { pressure: null, loss: 0 };
  const pressure = forecast(state, fire);
  return { pressure, loss: impact(pressure, fire.exposure) };
}

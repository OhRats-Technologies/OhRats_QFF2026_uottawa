import { available } from "./rules.js";

// Read completed-front history; never change the season or move replay.
export function frontOutcome(state) {
  const history = state.history.at(-1);
  if (!history) return null;
  const completed = history.turn;
  const previousReserve = state.history.at(-2)?.integrity ?? 100;
  const reserveLost = previousReserve - history.integrity;
  const contained = state.log.filter(
    (entry) => entry.turn === completed && entry.type === "contained",
  ).length;
  const ignitions = state.log.filter(
    (entry) => entry.turn === state.turn && entry.type === "ignition",
  ).length;
  const resupplied = state.supplies - history.supplies;
  const ready = available(state);
  const parts = [`Front ${completed + 1}`, `−${reserveLost.toFixed(1)} reserve`];
  if (contained) parts.push(`${contained} contained`);
  if (ignitions) parts.push(`${ignitions} new fires`);
  if (resupplied) parts.push(`+${resupplied} supplies`);
  return {
    front: completed + 1,
    reserveLost,
    contained,
    ignitions,
    resupplied,
    ready,
    supplies: state.supplies,
    feedback: parts.join(" · "),
    announcement:
      `Front ${completed + 1} complete. ${reserveLost.toFixed(1)} reserve lost. ` +
      `${contained} fires contained. ${ignitions} new fires. ` +
      `${ready} of ${state.crewTotal} crews ready. ${state.supplies} supplies.`,
  };
}

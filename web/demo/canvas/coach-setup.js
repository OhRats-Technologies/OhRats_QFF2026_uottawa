import { BettyCoach } from "./coach.js";
export function setupCoach(api) {
  const coach = new BettyCoach({ ...api, navigate: async (id) => {
    const s = api.state();
    s.tab = /^(angle|strength|epsilon)-/.test(id) ? "kernel" : "rack";
    s.rackPage = 0;
    await new Promise(requestAnimationFrame);
    if (id.startsWith("signal-") && !coach.boardHits?.some((h) => h.id === id)) {
      const count = coach.boardHits?.filter((h) => h.id.startsWith("signal-")).length || 20;
      s.rackPage = Math.floor(Number(id.slice(7)) / count);
    }
  } });
  return coach;
}

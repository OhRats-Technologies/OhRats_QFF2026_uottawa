import { shuffle } from "./random.js";
export const upgrades = [
  {
    id: "network",
    name: "Mutual aid",
    branch: "Response",
    description: "One additional crew for the rest of the season.",
    effect: (s) => s.crewTotal++,
  },
  {
    id: "training",
    name: "Crew training",
    branch: "Response",
    description: "Crew suppression: 0.90 → 1.15 pressure per turn.",
    effect: (s) => (s.crewPower = 1.15),
  },
  {
    id: "logistics",
    name: "Supply corridor",
    branch: "Logistics",
    description: "Resupply: 2 → 3 supply credits each turn.",
    effect: (s) => (s.resupply = 3),
  },
  {
    id: "precision",
    name: "Targeted drops",
    branch: "Logistics",
    description: "Water removes 70% instead of 58% of current pressure.",
    effect: (s) => (s.dropFactor = 0.3),
  },
];
export function upgradeChoices(state) {
  const choiceRng = { rng: (state.seed + state.turn * 7919) >>> 0 };
  return shuffle(
    upgrades.filter((u) => !state.upgrades.includes(u.id)),
    choiceRng,
  ).slice(0, 3);
}
export function applyUpgrade(state, id) {
  if (!state.upgradePending) return false;
  const upgrade = upgradeChoices(state).find((u) => u.id === id);
  if (!upgrade) return false;
  upgrade.effect(state);
  state.upgrades.push(id);
  state.upgradePending = false;
  state.log.push({ turn: state.turn, type: "upgrade", text: upgrade.name });
  return true;
}

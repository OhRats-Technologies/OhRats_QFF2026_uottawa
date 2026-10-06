import { random, shuffle } from "./random.js";

export const fronts = [
  {
    name: "Dry start",
    dry: 0.62,
    wind: 0.32,
    rain: 0,
    detail: "Small ignitions. Crews take two turns to return.",
  },
  {
    name: "Southwest wind",
    dry: 0.68,
    wind: 0.61,
    rain: 0,
    detail: "Wind lifts pressure. Water drops act immediately.",
  },
  {
    name: "Lightning line",
    dry: 0.74,
    wind: 0.48,
    rain: 0,
    detail: "Two new fires. Keep a crew in reserve.",
  },
  {
    name: "Patchy rain",
    dry: 0.47,
    wind: 0.27,
    rain: 0.48,
    detail: "Rain slows growth; it does not guarantee containment.",
  },
  {
    name: "Heat ridge",
    dry: 0.86,
    wind: 0.42,
    rain: 0,
    detail: "Choose your first upgrade before the next front.",
  },
  {
    name: "Smoke drift",
    dry: 0.78,
    wind: 0.67,
    rain: 0,
    detail: "Crews dispatched now need three turns.",
  },
  {
    name: "Dry lightning",
    dry: 0.9,
    wind: 0.71,
    rain: 0,
    detail: "Three new ignitions. Watch rising fires, not just new ones.",
  },
  {
    name: "Wind shift",
    dry: 0.76,
    wind: 0.81,
    rain: 0,
    detail: "Strong growth. Supplies must last through the season.",
  },
  {
    name: "Cool break",
    dry: 0.48,
    wind: 0.28,
    rain: 0.35,
    detail: "Two new fires. Choose a second upgrade; relief is temporary.",
  },
  {
    name: "Late heat",
    dry: 0.83,
    wind: 0.68,
    rain: 0,
    detail: "Returning crews can change the balance.",
  },
  {
    name: "Rain band",
    dry: 0.3,
    wind: 0.25,
    rain: 0.75,
    detail: "Two last ignitions. Rain slows growth; keep crews available.",
  },
  {
    name: "Season closes",
    dry: 0.4,
    wind: 0.29,
    rain: 0.38,
    detail: "One last turn. Reserve supplies earn a small debrief bonus.",
  },
];
const wave = { 0: 3, 2: 2, 4: 2, 6: 3, 8: 2, 10: 2 };

export function createScenario(seed, pool) {
  const rng = { rng: seed || 1 };
  const locations = shuffle(pool, rng);
  const weather = fronts.map((front) => ({
    ...front,
    dry: Math.min(1, Math.max(0, front.dry + (random(rng) - 0.5) * 0.12)),
    wind: Math.min(1, Math.max(0, front.wind + (random(rng) - 0.5) * 0.12)),
  }));
  const incidents = [];
  let index = 0;
  for (const [turn, count] of Object.entries(wave)) {
    for (let n = 0; n < count; n++) {
      const location = locations[index % locations.length];
      const region =
        location.x < 0.38
          ? "Northwest"
          : location.y < 0.46
            ? "Far north"
            : "Central";
      incidents.push({
        id: index + 1,
        name: `${region} ${String(index + 1).padStart(2, "0")}`,
        spawn: Number(turn),
        x: location.x,
        y: location.y,
        cover: location.cover,
        fuel: 0.25 + random(rng) * 0.7,
        exposure: 0.6 + random(rng) * 0.6,
        size: 0.55 + random(rng) * 0.95,
        crew: 0,
        dropTurn: -1,
        status: "waiting",
        history: [],
      });
      index++;
    }
  }
  return { weather, incidents };
}

import { createRun, action, advance } from "./rules.js";
import { applyUpgrade } from "./upgrades.js";
import { IncidentMap } from "./map.js";
import { OperationsUI } from "./ui.js";
import { QuantumLens } from "./sphere.js";
import { FeatureBench } from "./bench.js";
import { Sound } from "./sound.js";
import { InstrumentLab } from "./instruments.js";
import { MapContext } from "./context.js";
import { ValueSlider } from "./slider.js";
import { loadSession, saveSession } from "./session.js";
import { frontOutcome } from "./outcome.js";
import { gameKeyboard } from "./keyboard.js";
import { nextSeasonSeed } from "./next-season.js";

const $ = (id) => document.getElementById(id);
const [source, data, layers, evidence, heightSeries, heightChange] = await Promise.all(
  [
    "assets/context/scenario.json",
    "data.json",
    "assets/context/layers.json",
    "../presentation/evidence.json",
    "assets/context/height-series-v2.json",
    "assets/context/height-change.json",
  ].map(async (path) => {
    const response = await fetch(path);
    if (!response.ok) throw new Error(`Unable to load game context: ${path}`);
    return response.json();
  }),
);
const hashSeed = Number(
  new URLSearchParams(location.hash.slice(1)).get("season"),
);
const requestedSeed =
  Number.isInteger(hashSeed) && hashSeed > 0 && hashSeed < 2 ** 32
    ? hashSeed
    : 0;
let checkpoint = new URLSearchParams(location.search).has("qa")
  ? null
  : loadSession(source.pool);
if (checkpoint && requestedSeed && checkpoint.state.seed !== requestedSeed)
  checkpoint = null;
let state = checkpoint?.state ?? createRun(requestedSeed || 2, source.pool);
let moves = checkpoint?.moves ?? [];
const sound = new Sound();
const map = new IncidentMap(source, select);
const lens = new QuantumLens();
const instruments = new InstrumentLab(evidence, lens, persist);
if (checkpoint) instruments.restore(checkpoint.techniques, state.turn);
const ui = new OperationsUI(select, (id) => {
  if (applyUpgrade(state, id)) {
    moves.push({ type: "upgrade", id });
    sound.play("upgrade");
    render("Upgrade installed.");
  }
});
new FeatureBench(data);

function render(feedback = "") {
  const fire = ui.render(state, feedback);
  map.update(state);
  lens.update(fire);
  instruments.progress(state);
  persist();
}
function persist() {
  saveSession(state, moves, instruments.unlocked);
}
function select(id) {
  state.selected = id;
  render();
}
function respond(kind) {
  const fire = state.incidents.find((item) => item.id === state.selected);
  if (!action(state, state.selected, kind)) return;
  moves.push({ type: "action", id: state.selected, kind });
  map.effect(fire, kind);
  sound.play(kind);
  const messages = {
    crew: `Crew dispatched. Returns in ${fire.crew} fronts.`,
    water: `Pressure reduced to ${fire.size.toFixed(1)}.`,
  };
  render(messages[kind]);
  $("announcement").textContent = messages[kind];
}
function next() {
  if (state.status !== "playing") {
    ui.showDebrief(state);
    return;
  }
  if (!advance(state)) return;
  moves.push({ type: "advance" });
  sound.play(state.status === "playing" ? "advance" : state.status);
  document.body.classList.remove("front-change");
  void document.body.offsetWidth;
  document.body.classList.add("front-change");
  const outcome = frontOutcome(state);
  render(outcome.feedback);
  $("announcement").textContent = outcome.announcement;
}
function restart(seed) {
  $("debrief").close();
  $("upgrade").close();
  state = createRun(seed, source.pool);
  moves = [];
  history.replaceState(null, "", `#season=${seed}`);
  map.reset();
  instruments.reset();
  render();
}
for (const button of document.querySelectorAll("[data-action]"))
  button.onclick = () => respond(button.dataset.action);
$("advance").onclick = next;
function enterSeason() {
  $("welcome").close();
  window.scrollTo({ top: 0, behavior: "instant" });
  $("game-title").focus({ preventScroll: true });
}
$("start").onclick = enterSeason;
if (checkpoint) {
  $("start").textContent = `Continue front ${Math.min(state.turn + 1, 12)} →`;
  $("fresh").hidden = false;
}
$("fresh").onclick = () => {
  restart(nextSeasonSeed(state.seed));
  enterSeason();
};
$("retry").onclick = () => restart(state.seed);
$("new-season").onclick = () => restart(nextSeasonSeed(state.seed));
$("guide-open").onclick = () => $("guide").showModal();
$("guide-close").onclick = () => $("guide").close();
$("sound").onclick = async () => {
  const button = $("sound");
  button.disabled = true;
  await sound.enable(!sound.enabled);
  button.textContent = sound.unavailable ? "Sound unavailable" : `Sound ${sound.enabled ? "on" : "off"}`;
  button.setAttribute("aria-pressed", sound.enabled);
  button.disabled = sound.unavailable;
  sound.play("inspect");
};
document.addEventListener("visibilitychange", () => sound.setHidden(document.hidden));
$("lens-toggle").onclick = () => {
  $("lens-controls").hidden = !$("lens-controls").hidden;
  $("lens-toggle").setAttribute("aria-expanded", !$("lens-controls").hidden);
  if (!$("lens-controls").hidden && matchMedia("(max-width: 760px)").matches)
    $("lens-controls").scrollIntoView({ block: "center", behavior: "auto" });
};
for (const key of ["damping", "dephasing"])
  new ValueSlider(
    $(key),
    key === "damping" ? "Amplitude damping" : "Dephasing",
    (value) => lens.setNoise({ [key]: value }),
  );
$("coherent-noise").onchange = () =>
  lens.setNoise({ management: $("coherent-noise").checked });

new MapContext(layers, heightSeries, heightChange);
gameKeyboard(next, respond);
$("cities").hidden = true;
render();
if (state.status === "playing") $("welcome").showModal();

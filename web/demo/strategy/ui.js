import { active, available, canPlay } from "./rules.js";
import { upgradeChoices } from "./upgrades.js";
import { reserveChart, seasonBreakdown, impactReport } from "./debrief.js";
import { responsePreview, previewText } from "./preview.js";
import { IncidentList } from "./incident-list.js";
import { incidentProjection } from "./readout.js";
import { UpgradeLedger } from "./progression.js";
import { frontDetail } from "./front-detail.js";

const $ = (id) => document.getElementById(id);
const number = (value) => value.toFixed(1);
const covers = {
  210: "Coniferous cover",
  220: "Broadleaf cover",
  230: "Mixedwood cover",
};
export class OperationsUI {
  constructor(onSelect, onUpgrade) {
    this.onSelect = onSelect;
    this.onUpgrade = onUpgrade;
    this.incidents = new IncidentList($("incident-list"), onSelect, $("advance"));
    this.progression = new UpgradeLedger();
    $("upgrade").addEventListener("cancel", (event) => event.preventDefault());
    for (const button of document.querySelectorAll("[data-action], #advance")) {
      button.setAttribute("aria-describedby", "action-feedback");
      button.addEventListener("pointerenter", () =>
        this.preview(button.dataset.action),
      );
      button.addEventListener("focus", () =>
        this.preview(button.dataset.action),
      );
      button.addEventListener("pointerleave", () => this.clearPreview());
      button.addEventListener("blur", () => this.clearPreview());
    }
  }
  preview(kind) {
    if (!this.state) return;
    const result = responsePreview(this.state, kind);
    $("action-feedback").textContent = result
      ? previewText(result)
      : this.feedback;
  }
  clearPreview() {
    const focused = document.activeElement;
    if (focused.matches("[data-action], #advance"))
      this.preview(focused.dataset.action);
    else $("action-feedback").textContent = this.feedback;
  }
  render(state, feedback = "") {
    this.state = state;
    this.feedback = feedback;
    const fire = state.incidents.find((item) => item.id === state.selected);
    const terminal = state.status !== "playing";
    const front = terminal ? Math.max(0, state.turn - 1) : state.turn;
    const weather = state.weather[Math.min(front, 11)];
    $("front-number").textContent = `${Math.min(front + 1, 12)} / 12`;
    $("front-name").textContent = weather.name;
    $("front-detail").textContent = frontDetail(state, weather);
    $("weather-meters").innerHTML = [
      ["Dryness", weather.dry],
      ["Wind", weather.wind],
      ["Rain", weather.rain],
    ]
      .map(
        ([name, value]) =>
          `<div class="weather-meter"><span>${name}<b>${Math.round(value * 100)}%</b></span><i><b style="width:${value * 100}%"></b></i></div>`,
      )
      .join("");
    $("integrity").textContent = Math.round(state.integrity);
    $("integrity-bar").style.width = `${state.integrity}%`;
    $("integrity-bar").style.background =
      state.integrity < 60 ? "var(--accent)" : "var(--mint)";
    $("supplies").textContent = state.supplies;
    $("crews").textContent = `${available(state)}/${state.crewTotal}`;
    $("contained").textContent = state.contained;
    $("crew-status").textContent = fire?.crew
      ? terminal ? "Crew assigned" : `Crew returns in ${fire.crew} front${fire.crew === 1 ? "" : "s"}`
      : "";
    $("advance").disabled = !terminal && !canPlay(state);
    $("advance").querySelector("span").textContent =
      terminal ? "Season report" : state.turn === 11 ? "Close season" : "Advance front";
    $("incident-name").textContent = fire?.name || "All clear for now";
    if (fire) {
      const { pressure: next, loss } = incidentProjection(state, fire);
      $("incident-readout").innerHTML =
        `<div><strong>${number(fire.size)}</strong>pressure</div><div><strong>${next === null ? "—" : number(next)}</strong>${terminal ? "season ended" : "after front"}</div><div><strong id="incident-risk">${loss === null ? "—" : number(loss)}</strong>reserve loss</div>`;
      $("incident-readout").title =
        `${covers[fire.cover]}. Toy fuel ${number(fire.fuel)}, exposure ${number(fire.exposure)}. Reserve loss is this fire's projected contribution after the current front. These are fictional game units, not hectares.`;
      $("incident-readout").setAttribute("aria-description", $("incident-readout").title);
    } else {
      $("incident-readout").textContent = "Advance to the next weather front.";
      $("incident-readout").removeAttribute("title");
      $("incident-readout").removeAttribute("aria-description");
    }
    for (const button of document.querySelectorAll("[data-action]")) {
      const kind = button.dataset.action,
        cost = { crew: 2, water: 4 }[kind];
      let reason = "";
      if (!canPlay(state)) reason = "Choose an upgrade or begin a new season.";
      else if (!fire || fire.status !== "burning")
        reason = "Select an active fire.";
      else if (state.supplies < cost) reason = "Not enough supplies.";
      else if (kind === "crew" && fire.crew)
        reason = "A crew is already assigned.";
      else if (kind === "crew" && available(state) === 0)
        reason = "All crews are occupied. Advance a front to bring them back.";
      else if (kind === "water" && fire.dropTurn === state.turn)
        reason = "One drop per fire per front.";
      button.disabled = !!reason;
      button.title = reason;
      button.querySelector("small").textContent = terminal
        ? ""
        : kind === "crew"
          ? `Suppression over ${state.turn === 5 ? 3 : 2} fronts`
          : "Reduce pressure immediately";
    }
    $("action-feedback").textContent = feedback;
    this.incidents.render(active(state).sort((a, b) => b.size - a.size), state.selected, terminal);
    this.progression.render(state);
    if (state.upgradePending && !$("upgrade").open) this.showUpgrade(state);
    if (terminal && this.lastStatus !== state.status && !$("debrief").open)
      this.showDebrief(state);
    this.lastStatus = state.status;
    return fire;
  }
  showUpgrade(state) {
    $("upgrade-options").replaceChildren();
    for (const choice of upgradeChoices(state)) {
      const button = document.createElement("button");
      button.dataset.upgrade = choice.id;
      button.innerHTML = `<b>${choice.name}</b><span>${choice.branch}</span><small>${choice.description}</small>`;
      button.onclick = () => {
        this.onUpgrade(choice.id);
        $("upgrade").close();
      };
      $("upgrade-options").append(button);
    }
    $("upgrade").showModal();
  }
  showDebrief(state) {
    $("debrief-kicker").textContent =
      `Seed ${state.seed} / ${state.turn} fronts`;
    $("debrief-title").textContent =
      state.status === "won" ? "The season held." : "The line broke.";
    $("debrief-chart").innerHTML = reserveChart(state);
    const summary = seasonBreakdown(state);
    $("debrief-impact").innerHTML = impactReport(summary);
    $("debrief-impact").setAttribute("aria-label", `Largest contributors to ${summary.total.toFixed(1)} cumulative simulated pressure impact, before reserve is floored at zero. These are recorded impacts, not effects prevented by interventions.`);
    $("debrief-peak").textContent = summary.total && summary.peak
      ? `Hardest front ${summary.peak.front} · ${summary.peak.weather} · ${summary.peak.impact.toFixed(1)} impact`
      : "No pressure impact this season.";
    $("debrief-stats").innerHTML = [
      [Math.round(state.integrity), "reserve"],
      [state.contained, "contained"],
      [state.score, "score"],
    ]
      .map(
        ([value, label]) =>
          `<div><strong>${value}</strong><span>${label}</span></div>`,
      )
      .join("");
    $("debrief-stats").lastElementChild.title = "Score = 10 × final reserve + 18 × contained fires + 2 × remaining supplies, rounded.";
    $("debrief-thought").textContent =
      state.status === "won"
        ? `You combined ${state.deployments} crew dispatches and ${state.drops} water drops. Try the same weather with a different approach.`
        : "Pressure outran your response. Crews need time; water reduces pressure immediately. Replay this weather and try a different response.";
    $("debrief").showModal();
  }
}

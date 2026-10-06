import { upgrades } from "./upgrades.js";

const symbols = { network: "＋", training: "↑", logistics: "⇄", precision: "◉" };
const milestones = [4, 8];
const $ = id => document.getElementById(id);

// Read-only view of earned response upgrades, separate from instrument credits.
export class UpgradeLedger {
  constructor() {
    $("upgrade-track").setAttribute("aria-label", "Response upgrade milestones");
    this.slots = milestones.map(front => {
      const button = document.createElement("button");
      button.className = "upgrade-token empty";
      button.dataset.milestone = front;
      button.onclick = () => this.show(button);
      $("upgrade-track").append(button);
      return button;
    });
    document.body.insertAdjacentHTML("beforeend", `
      <dialog id="progression" aria-labelledby="progression-title">
        <button id="progression-close" class="close" aria-label="Close upgrade ledger">×</button>
        <span class="eyebrow">Response / logistics</span><h2 id="progression-title">Your season build.</h2>
        <div id="progression-milestones"></div><div id="progression-effects"></div>
        <div id="progression-branches"></div>
        <p class="progression-boundary">Choose one of three offered upgrades after fronts 4 and 8.
          Effects last this season. This ledger only reviews choices; quantum instrument credits are separate.</p>
      </dialog>`);
    $("progression-close").onclick = () => $("progression").close();
    $("progression").addEventListener("close", () => this.returnTarget?.focus());
    $("guide-progress").onclick = () => {
      $("guide").close();
      this.show($("guide-open"));
    };
  }
  render(state) {
    this.state = state;
    for (const [index, front] of milestones.entries()) {
      const item = upgrades.find(upgrade => upgrade.id === state.upgrades[index]);
      const status = item ? item.name : state.status !== "playing" ? "Not earned"
        : state.turn >= front ? "Choose an upgrade" : `After front ${front}`;
      this.slots[index].textContent = item ? symbols[item.id] : front;
      this.slots[index].classList.toggle("empty", !item);
      this.slots[index].title = item ? `${item.name}: ${item.description}` : status;
      this.slots[index].setAttribute("aria-label", `Front ${front}: ${status}. Open upgrade ledger.`);
    }
    $("progression-milestones").innerHTML = milestones.map((front, index) => {
      const item = upgrades.find(upgrade => upgrade.id === state.upgrades[index]);
      const status = item ? item.name : state.status !== "playing" ? "Not earned"
        : state.turn >= front ? "Choice ready" : `In ${front - state.turn} fronts`;
      return `<div class="progression-step ${item ? "earned" : ""}"><span>Front ${front}</span><b>${status}</b></div>`;
    }).join("");
    $("progression-effects").innerHTML = [
      [state.crewTotal, "total crews", "crews"], [state.crewPower.toFixed(2), "pressure / crew front", "power"],
      [state.resupply, "supplies / front", "supplies"], [Math.round((1 - state.dropFactor) * 100) + "%", "pressure removed / drop", "water"],
    ].map(([value, label, id]) => `<div><strong data-build-effect="${id}">${value}</strong><span>${label}</span></div>`).join("");
    $("progression-branches").innerHTML = ["Response", "Logistics"].map(branch =>
      `<section><h3>${branch}</h3>${upgrades.filter(item => item.branch === branch).map(item => {
        const selected = state.upgrades.includes(item.id);
        return `<div class="progression-node ${selected ? "earned" : ""}" data-build-upgrade="${item.id}">
          <span>${symbols[item.id]}</span><div><b>${item.name}</b><small>${item.description}</small></div>
          <em>${selected ? "Equipped" : "Not chosen"}</em></div>`;
      }).join("")}</section>`,
    ).join("");
  }
  show(returnTarget) {
    this.returnTarget = returnTarget;
    this.render(this.state);
    $("progression").showModal();
  }
}

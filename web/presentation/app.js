import { makeSlides } from "./slides.js";
import { geometryScene } from "./scenes.js";
import { BettyPresenter } from "./presenter.js";
import { drawSlidePanels } from "./panels.js";
const evidence = await fetch("evidence.json").then((response) => {
  if (!response.ok)
    throw new Error("Frozen evidence could not be loaded");
  return response.json();
});
const sweepResponse = await fetch("assets/shot-sweep.json");
if (!sweepResponse.ok) throw new Error("Saved shot-sweep evidence could not be loaded");
evidence.shot_sweep = await sweepResponse.json();
const slides = makeSlides(evidence);
const deck = document.querySelector("#deck");
deck.innerHTML = slides.map((s, i) => `<section class="slide ${i === 0 ? "cover" : ""}" id="${s.id}" data-index="${i}" aria-label="${s.title}" hidden><canvas class="slide-canvas" width="1280" height="720" aria-hidden="true"></canvas>${s.html}</section>`).join("");
document.querySelectorAll(".slide").forEach((slide) => {
  const canvas = slide.querySelector(".slide-canvas");
  if (canvas) {
    drawSlidePanels(canvas, slide.id);
  }
});
const sections = [...deck.children], panel = document.querySelector("#panel");
const content = document.querySelector("#panel-content");
const reduced = matchMedia("(prefers-reduced-motion: reduce)");
let index = 0, idle, angleScale = 4;
const bettyDock = document.querySelector("#betty-dock");
const betty = new BettyPresenter(bettyDock, notes);

function fit() {
  document.documentElement.style.setProperty("--scale", Math.min(innerWidth / 1280, innerHeight / 720));
  const activeCanvas = sections[index]?.querySelector(".slide-canvas");
  if (activeCanvas) {
    drawSlidePanels(activeCanvas, slides[index].id);
  }
}

function wake() {
  document.body.classList.add("awake");
  clearTimeout(idle);
  idle = setTimeout(() => document.body.classList.remove("awake"), 2500);
}

function show(next, update = true) {
  const previous = sections[index];
  index = Math.max(0, Math.min(slides.length - 1, next));
  sections.forEach((s, i) => {
    s.hidden = i !== index;
  });
  const current = sections[index];
  const activeCanvas = current?.querySelector(".slide-canvas");
  if (activeCanvas) {
    drawSlidePanels(activeCanvas, slides[index].id);
  }
  if (!reduced.matches && previous !== current) {
    const scale = matchMedia("(max-width:700px) and (orientation:portrait)").matches ? "" : "scale(var(--scale)) ";
    current.animate([{ opacity: 0, transform: `${scale}translateY(16px)` }, { opacity: 1, transform: `${scale}translateY(0)` }], { duration: 650, easing: "cubic-bezier(.22,1,.36,1)" });
  }
  document.querySelector("#position").textContent = slides[index].backup ? `A${index - 6}` : `${index + 1} / 7`;
  document.querySelector("#previous").disabled = index === 0;
  document.querySelector("#next").disabled = index === slides.length - 1;
  document.querySelector(".progress i").style.width = `${Math.min(index + 1, 7) / 7 * 100}%`;
  document.querySelector("#announcement").textContent = slides[index].title;
  betty.update(slides[index], index);
  if (update)
    history.replaceState(null, "", `#${slides[index].id}`);
  wake();
}

function notes() {
  content.innerHTML = `<div class="notes-header"><span class="betty-tag">🦫 BETTY · FIELD GUIDE NOTES</span><h2>${slides[index].title}</h2></div><div class="notes-body"><p>${slides[index].notes}</p></div><p class="caption" style="margin-top:22px">${slides[index].seconds ? `Planned ${slides[index].seconds} seconds` : "Question appendix"} · Arrow keys / Space: next · B: guide · N: notes · O: index · F: fullscreen</p>`;
  panel.showModal();
}

function overview() {
  content.innerHTML = `<h2>Slide index</h2><div class="index-list">${slides.map((s, i) => `<button data-jump="${i}" class="${s.backup ? "backup" : ""}">${s.backup ? "Appendix" : i + 1} &nbsp; ${s.title}</button>`).join("")}</div>`;
  panel.showModal();
}
document.querySelector("#next").onclick = () => show(index + 1);
document.querySelector("#previous").onclick = () => show(index - 1);
document.querySelector("#notes").onclick = notes;
document.querySelector("#overview").onclick = overview;
document.querySelector("#betty-toggle").onclick = () => betty.toggle();
document.querySelector("#fullscreen").onclick = () => document.fullscreenElement ? document.exitFullscreen() : document.documentElement.requestFullscreen();
document.querySelector(".close").onclick = () => panel.close();

panel.addEventListener("click", (event) => {
  if (event.target.dataset.jump !== undefined) {
    show(Number(event.target.dataset.jump));
    panel.close();
  }
});

deck.addEventListener("click", (event) => {
  const stage = event.target.dataset.mapStage;
  if (stage) {
    const scene = document.querySelector("#data");
    scene.dataset.stage = stage;
    scene.querySelectorAll("[data-map-stage]").forEach((b) => b.setAttribute("aria-pressed", String(b.dataset.mapStage === stage)));
  }
  const denominator = Number(event.target.dataset.scale);
  if (denominator) {
    const block = document.querySelector("#geometry .geometry-layout");
    const previousScale = angleScale;
    angleScale = denominator;
    block.innerHTML = geometryScene(evidence, denominator);
    if (!reduced.matches) {
      const arms = [...block.querySelectorAll(".state-arm")], begin = performance.now();
      function tween(now) {
        const t = Math.min(1, (now - begin) / 900), ease = 1 - Math.pow(1 - t, 3);
        if (angleScale !== denominator || !block.isConnected)
          return;
        arms.forEach((arm, i) => {
          const z = [-1, 0.3, 0.8, 1.4][i], x = 65 + i * 130, y = 77;
          const phase = 2 * Math.PI * ((1 - ease) / previousScale + ease / denominator) * Math.tanh(z / 2);
          const ex = x + 42 * Math.cos(phase), ey = y + 15 * Math.sin(phase);
          arm.querySelector("path").setAttribute("d", `M${x} ${y} L${ex} ${ey}`);
          arm.querySelector("circle").setAttribute("cx", ex);
          arm.querySelector("circle").setAttribute("cy", ey);
        });
        if (t < 1)
          requestAnimationFrame(tween);
      }
      requestAnimationFrame(tween);
    }
    block.querySelector(`[data-scale="${denominator}"]`).focus();
    if (!reduced.matches)
      block.querySelector(".heatmap svg").animate([{ opacity: 0.3 }, { opacity: 1 }], { duration: 600 });
  }
});

addEventListener("keydown", (event) => {
  if (panel.open || event.altKey || event.ctrlKey || event.metaKey)
    return;
  if (["BUTTON", "A", "INPUT"].includes(document.activeElement?.tagName) && [" ", "ArrowLeft", "ArrowRight"].includes(event.key))
    return;
  if (["ArrowRight", "PageDown", " "].includes(event.key)) {
    event.preventDefault();
    show(index + 1);
  }
  if (["ArrowLeft", "PageUp"].includes(event.key)) {
    event.preventDefault();
    show(index - 1);
  }
  if (event.key === "Home")
    show(0);
  if (event.key === "End")
    show(6);
  if (event.key.toLowerCase() === "b")
    betty.toggle();
  if (event.key.toLowerCase() === "n")
    notes();
  if (event.key.toLowerCase() === "o")
    overview();
  if (event.key.toLowerCase() === "f")
    document.querySelector("#fullscreen").click();
});

addEventListener("resize", fit);

addEventListener("pointermove", wake, { passive: true });

addEventListener("hashchange", () => {
  const i = slides.findIndex((s) => `#${s.id}` === location.hash);
  if (i >= 0)
    show(i, false);
});
fit();
show(Math.max(0, slides.findIndex((s) => `#${s.id}` === location.hash)), false);
window.presentation = { slides, evidence, show, get index() {
  return index;
} };

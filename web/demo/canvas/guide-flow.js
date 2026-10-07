import { tour } from "./tour.js";
import { lessons } from "./guide-lessons.js";
export function announceLesson(s, status) {
  const lesson = (s.guideIntro ? tour : lessons)[s.guideStep || 0];
  status.textContent = `Betty: ${lesson.title || lesson.name} ${lesson.text} ${lesson.tip || ""}`;
}
export function openBriefing(s, status) {
  s.help = true;
  s.guideIntro = true;
  s.guideStep = 0;
  s.guideValue = 0;
  announceLesson(s, status);
}
export function guideAction(s, type, value, status) {
  if (type !== "help" && !type.startsWith("guide-")) return false;
  if (type === "help") {
    s.help = !s.help;
    s.guideIntro = false;
    s.guideStep = 0;
    s.guideValue = 0;
  }
  if (type === "guide-step" || type === "guide-topic") {
    s.guideStep = Math.max(
      0,
      Math.min(7, type === "guide-topic" ? value : (s.guideStep || 0) + value),
    );
    s.guideValue = 0;
  }
  if (type === "guide-tour") openBriefing(s, status);
  if (type === "guide-demo") s.guideValue = s.guideValue ? 0 : 1;
  if (type === "guide-close") {
    if (s.guideIntro) {
      s.menu = true;
      location.hash = "main-menu";
    }
    s.help = false;
    s.guideIntro = false;
  }
  if (type === "guide-play") {
    s.onboarded = true;
    s.help = false;
    s.guideIntro = false;
    s.menu = false;
    location.hash = "workbench";
    status.textContent = "Choose your signals and run your first engine.";
  }
  if (s.help) announceLesson(s, status);
  return true;
}

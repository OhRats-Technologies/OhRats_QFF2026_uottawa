import { tour, tourText } from "./tour-lessons.js";
import { dialogue } from "./dialogue.js";
import { lessons } from "./guide-lessons.js";
export function announceLesson(s, status) {
  const lesson = (s.guideIntro ? tour : lessons)[s.guideStep || 0];
  const title = s.guideIntro && lesson.pageZones?.[s.guidePage || 0] === "kernel"
    ? "Kernel engine" : lesson.title || lesson.name;
  status.textContent = `Betty: ${title} ${s.guideIntro ? tourText(s) : lesson.text} ${lesson.tip || ""}`;
}
export function openBriefing(s, status) {
  s.help = true;
  s.guideIntro = true;
  s.guideStep = 0;
  s.guidePage = 0;
  dialogue.reset();
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
  if (type === "guide-next" && s.guideIntro) {
    if (dialogue.finish()) return true;
    type = "guide-step";
    value = 1;
  }
  if (type === "guide-step" || type === "guide-topic") {
    if (s.guideIntro && type === "guide-step") {
      let page = (s.guidePage || 0) + value;
      if (page >= tour[s.guideStep].pages.length) {
        if (s.guideStep === tour.length - 1) type = "guide-play";
        else { s.guideStep++; page = 0; }
      } else if (page < 0 && s.guideStep > 0) {
        s.guideStep--;
        page = tour[s.guideStep].pages.length - 1;
      }
      s.guidePage = Math.max(0, page);
    } else {
      s.guideStep = Math.max(0, Math.min(7,
        type === "guide-topic" ? value : (s.guideStep || 0) + value));
      s.guidePage = 0;
    }
    s.guideValue = 0;
    dialogue.reset();
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
    status.textContent = "Choose your signals. Complete builds test automatically.";
  }
  if (s.help) announceLesson(s, status);
  return true;
}

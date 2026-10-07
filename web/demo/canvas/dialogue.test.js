import { test, expect } from "bun:test";
import { Dialogue } from "./dialogue.js";
import { tour } from "./tour-lessons.js";
import { guideAction } from "./guide-flow.js";

test("every Betty bubble contains 10–25 words", () => {
  for (const topic of tour) for (const text of topic.pages) {
    const words = text.split(/\s+/).length;
    expect(words).toBeGreaterThanOrEqual(10);
    expect(words).toBeLessThanOrEqual(25);
  }
});
test("text types, click completes it, and reduced motion shows it immediately", () => {
  const d = new Dialogue(), text = "Betty is ready to build an engine with you.";
  expect(d.read("a", text, 1).text).toBe("");
  const mid = d.read("a", text, 1.8);
  expect(mid.text.length).toBeGreaterThan(0);
  expect(mid.typing).toBe(true);
  expect(d.finish()).toBe(true);
  expect(d.read("a", text, 1.81).text).toBe(text);
  expect(d.finish()).toBe(false);
  expect(d.read("b", text, 0).text).toBe(text);
});
test("dialogue pages move back and forward without skipping topics", () => {
  const s = { help: true, guideIntro: true, guideStep: 0, guidePage: 0 }, status = {};
  guideAction(s, "guide-step", 1, status);
  expect([s.guideStep, s.guidePage]).toEqual([0, 1]);
  guideAction(s, "guide-step", 1, status);
  expect([s.guideStep, s.guidePage]).toEqual([1, 0]);
  guideAction(s, "guide-step", -1, status);
  expect([s.guideStep, s.guidePage]).toEqual([0, 1]);
});

test("continue arrow uses bounded animated canvas strokes", async () => {
  const { dialogueArrow } = await import("./dialogue.js");
  const frames = [];
  for (const time of [0, 0.3, 0.9]) {
    const strokes = [], p = { line: (points) => strokes.push(points) };
    dialogueArrow(p, 100, 50, time);
    expect(strokes.length).toBe(2);
    expect(strokes.flat().every(([x, y]) => x >= 81 && x <= 105 && y >= 43 && y <= 57)).toBe(true);
    frames.push(strokes);
  }
  expect(frames[1]).not.toEqual(frames[2]);
});
test("Betty chirps respect mute, visibility and a bounded speaking rate", async () => {
  const { Audio } = await import("./audio.js");
  const previous = globalThis.document;
  globalThis.document = { hidden: false, addEventListener() {} };
  try {
    const a = new Audio(), tones = [];
    a.ctx = { state: "running", currentTime: 1 };
    a.tone = (...args) => tones.push(args);
    a.voice("hello", 1);
    expect(tones.length).toBe(0);
    a.enabled = true;
    a.voice("hello", 1);
    a.voice("hello", 2);
    expect(tones.length).toBe(1);
    a.ctx.currentTime += 0.1;
    a.voice("hello", 3);
    expect(tones.length).toBe(2);
    document.hidden = true;
    a.ctx.currentTime += 0.1;
    a.voice("hello", 4);
    expect(tones.length).toBe(2);
    expect(tones.every(([hz, , duration, volume]) => hz >= 250 && hz <= 525 && duration < 0.1 && volume < 0.03)).toBe(true);
  } finally { globalThis.document = previous; }
});

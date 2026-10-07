import { test, expect } from "bun:test";
import { settle } from "./glide.js";

const overlap = (a, b) => a.x < b.x + b.w && a.x + a.w > b.x &&
  a.y < b.y + b.h && a.y + a.h > b.y;

test("tour motion retains full label target and never sweeps text through it", () => {
  const old = { x: 20, y: 20, w: 320, h: 120 },
    target = { x: 400, y: 100, w: 100, h: 80 },
    box = { x: 520, y: 70, w: 420, h: 230 };
  settle("previous", { x: 10, y: 180, w: 100, h: 80 }, old, 0);
  for (const time of [1, 1.05, 1.1, 1.2, 1.3, 1.42]) {
    const shown = settle("next", target, box, time);
    expect(shown.target).toEqual(target);
    expect(shown.box.w).toBe(box.w);
    expect(shown.box.h).toBe(box.h);
    expect(overlap(shown.box, target)).toBe(false);
  }
});

test("resized dialogue stays on screen and leaves the encoder header exposed", () => {
  const target = { x: 100, y: 370, w: 120, h: 60 },
    header = { x: 20, y: 330, w: 800, h: 43 },
    box = { x: 100, y: 90, w: 420, h: 220 };
  settle("start", target, { x: 520, y: 450, w: 300, h: 100 }, 0);
  for (const time of [2, 2.05, 2.15, 2.3, 2.42]) {
    const shown = settle("header", target, box, time, { w: 844, h: 610 }, [header]);
    expect(shown.box.x + shown.box.w).toBeLessThanOrEqual(830);
    expect(shown.box.y + shown.box.h).toBeLessThanOrEqual(598);
    expect(overlap(shown.box, header)).toBe(false);
  }
});

test("reduced motion shows dialogue immediately", () => {
  const target = { x: 20, y: 300, w: 100, h: 60 },
    box = { x: 20, y: 20, w: 300, h: 200 };
  expect(settle("reduced", target, box, 0).fade).toBe(1);
});

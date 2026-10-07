import { test, expect } from "bun:test";
import { evaluation } from "./evaluation.js";
test("evaluating instrument animates inside its reserved rectangle", () => {
  const draw = (time) => {
    const cells = [], p = { text() {}, rect: (...args) => cells.push(args) };
    evaluation(p, 100, 20, 170, time);
    expect(cells.every(([x, y, w, h]) => x >= 100 && x + w <= 270.01 && y >= 20 && y + h <= 47)).toBe(true);
    return cells;
  };
  expect(draw(1)).not.toEqual(draw(1.2));
  expect(draw(0)).toEqual(draw(0));
});

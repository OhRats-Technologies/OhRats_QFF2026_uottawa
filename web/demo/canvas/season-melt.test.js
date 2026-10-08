import { test, expect } from "bun:test";
import { meltOffset } from "./season-melt.js";
test("columns hold, accelerate downward and completely clear at the deadline", () => {
  for (const height of [568, 900, 1800]) {
    for (const delay of [5, 90, 185]) {
      expect(meltOffset(0, delay, height)).toBe(0);
      expect(meltOffset(delay, delay, height)).toBe(0);
      expect(meltOffset(500, delay, height)).toBeGreaterThan(0);
      expect(meltOffset(700, delay, height)).toBeGreaterThan(meltOffset(500, delay, height));
      expect(meltOffset(1050, delay, height)).toBe(height);
      expect(meltOffset(2000, delay, height)).toBe(height);
    }
  }
});

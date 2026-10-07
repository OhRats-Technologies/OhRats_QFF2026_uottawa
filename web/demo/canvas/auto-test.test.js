import { test, expect } from "bun:test";
import { automaticTests, currentResult } from "./auto-test.js";
import { fresh, build } from "./session.js";
const pause = () => new Promise((resolve) => setTimeout(resolve, 35));
test("rapid edits coalesce, invalid builds wait, and identical results do not repeat", async () => {
  const s = fresh(); s.menu = false;
  let runs = 0;
  const auto = automaticTests(() => s, () => {
    runs++; s.result = { round: s.round, build: build(s) };
  }, 10);
  auto.schedule(); auto.schedule(); auto.schedule();
  expect(auto.pending).toBe(true);
  await pause(); expect(runs).toBe(1); expect(auto.pending).toBe(false);
  auto.schedule(); await pause(); expect(runs).toBe(1);
  s.features.pop(); auto.schedule(); expect(auto.pending).toBe(false);
  await pause(); expect(runs).toBe(1);
  s.features.push(7); auto.schedule(); await pause(); expect(runs).toBe(2);
  s.help = true; s.angle = 0.2; auto.schedule(); await pause(); expect(runs).toBe(2);
  auto.cancel();
});
test("an old season or edited build cannot unlock Next", () => {
  const s = fresh(); s.result = { round: 0, build: build(s) };
  expect(currentResult(s)).toBe(true);
  s.C = 3; expect(currentResult(s)).toBe(false);
  s.C = 1; s.round = 1; expect(currentResult(s)).toBe(false);
});

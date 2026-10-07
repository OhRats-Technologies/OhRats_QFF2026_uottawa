import { test, expect } from "bun:test";
import { fresh, build } from "./session.js";
import { contractLocked, choiceAction, choiceControl } from "./contract-lock.js";

test("a current winning contract locks, while stale, pending and next-season results do not", () => {
  const s = fresh();
  expect(contractLocked(s)).toBe(false);
  s.history = [{ round: 0, mae: 100, effort: 100 }, { round: 0, mae: 90, effort: 100 }];
  s.result = { round: 0, build: build(s) };
  expect(contractLocked(s)).toBe(true);
  expect(contractLocked(JSON.parse(JSON.stringify(s)))).toBe(true);
  s.evaluating = true; expect(contractLocked(s)).toBe(false);
  s.evaluating = false; s.C = 3; expect(contractLocked(s)).toBe(false);
  s.C = 1; s.round = 1; expect(contractLocked(s)).toBe(false);
});
test("build choices lock while navigation, inspection and audio remain available", () => {
  for (const id of ["signal-0", "width-4", "angle-up", "strength-down", "epsilon-up", "undo", "foundry"])
    expect(choiceControl(id)).toBe(true);
  for (const id of ["next", "help", "sound", "menu", "tab-results", "year-0", "rack-page", "guide-next"])
    expect(choiceControl(id)).toBe(false);
  for (const type of ["feature", "width", "angle", "strength", "epsilon", "restore", "apply", "sample"])
    expect(choiceAction(type)).toBe(true);
  for (const type of ["next", "new", "help", "sound", "year", "tab"])
    expect(choiceAction(type)).toBe(false);
});

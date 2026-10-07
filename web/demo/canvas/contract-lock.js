import { currentResult } from "./auto-test.js";
import { assessment } from "./session.js";

export const contractLocked = (s) => !s.running && !s.evaluating &&
  currentResult(s) && !!assessment(s).won;
export const choiceAction = (type) => [
  "feature", "width", "angle", "strength", "epsilon", "restore",
  "foundry", "sample", "more-shots", "candidate", "apply",
].includes(type);
export const choiceControl = (id) =>
  /^(signal|width|angle|strength|epsilon)-/.test(id) ||
  ["undo", "foundry", "apply", "more-shots"].includes(id) ||
  /^(method|candidate)-/.test(id);

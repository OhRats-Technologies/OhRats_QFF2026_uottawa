import { build } from "./session.js";
export const currentResult = (s) => !!s.result && s.result.round === s.round &&
  JSON.stringify(s.result.build) === JSON.stringify(build(s));
export function automaticTests(state, evaluate, delay = 420) {
  let timer, pending = false;
  const eligible = (s) => !s.menu && !s.help && !s.foundry && !s.running &&
    !s.finished && s.features.length === s.width && !currentResult(s);
  const cancel = () => { clearTimeout(timer); pending = false; };
  const schedule = () => {
    cancel();
    pending = eligible(state());
    if (!pending) return;
    timer = setTimeout(() => {
      const s = state();
      pending = false;
      if (eligible(s)) evaluate();
    }, delay);
  };
  return { schedule, cancel, get pending() { return pending; } };
}

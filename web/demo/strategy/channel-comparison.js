import { managedVector } from "./quantum.js";

// Squared state fidelity to a pure input; the output can be mixed.
export function pureFidelity(input, output) {
  return (1 + input.reduce((sum, value, index) => sum + value * output[index], 0)) / 2;
}
export function compareChannel(input, options) {
  const before = managedVector(input, { ...options, dd: false, twirl: false });
  const after = managedVector(input, options);
  return { input, before, after,
    beforeFidelity: pureFidelity(input, before), afterFidelity: pureFidelity(input, after) };
}
export function channelDiagram(comparison) {
  const { input, before, after, beforeFidelity, afterFidelity } = comparison;
  const arrow = (vector, kind) => {
    const x = 95 + 62 * vector[0], y = 76 - 62 * vector[1];
    return `<line class="channel-${kind}" x1="95" y1="76" x2="${x}" y2="${y}"/>`;
  };
  const describe = vector => vector.map(value => value.toFixed(3)).join(", ");
  return `<svg viewBox="0 0 190 162" role="img" aria-label="Equatorial x/y projection. Input vector ${describe(input)}. Without techniques ${describe(before)}, fidelity ${beforeFidelity.toFixed(4)}. With loadout ${describe(after)}, fidelity ${afterFidelity.toFixed(4)}. Fidelity includes the omitted z component.">
    <circle class="channel-grid" cx="95" cy="76" r="62"/>
    <path class="channel-grid" d="M25 76H165M95 6V146"/>
    <text x="171" y="79">x</text><text x="99" y="9">y</text>
    ${arrow(input, "input")}${arrow(before, "before")}${arrow(after, "after")}
    <text x="95" y="159" text-anchor="middle">Equatorial projection · z omitted</text>
  </svg>`;
}

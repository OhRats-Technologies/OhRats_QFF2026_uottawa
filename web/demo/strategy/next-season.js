// Spread neighbouring seasons across seed space; existing seeds/replays stay exact.
export function nextSeasonSeed(seed) {
  let value = (seed + 0x9e3779b9) >>> 0;
  value = Math.imul(value ^ (value >>> 16), 0x85ebca6b);
  value = Math.imul(value ^ (value >>> 13), 0xc2b2ae35);
  value = (value ^ (value >>> 16)) >>> 0;
  if (value && value !== seed) return value;
  return ((seed + 1) >>> 0) || 1;
}

import { sampleCandidates } from "./foundry.js";
export function foundryAction(s, data, audio, toast, type, value) {
  if (type === "sample" || type === "more-shots") {
    const method = type === "more-shots" ? s.sample?.method || "qaoa" : value;
    if (method === "mi" || method === "exact") {
      const features = data.rounds[s.round].selectors[method],
        mask = features.reduce((m, j) => m + (1 << j), 0);
      s.sample = { method, shots: 0,
        candidates: [{ features, energy: data.rounds[s.round].objective[mask] }] };
    } else s.sample = sampleCandidates(data.rounds[s.round].objective,
      type === "more-shots" ? 256 : 64, 31 + s.attempts, method);
    s.candidate = 0;
    audio.effect("run");
  }
  if (type === "candidate") s.candidate = value;
  if (type === "apply" && s.sample) {
    s.features = [...s.sample.candidates[s.candidate || 0].features];
    s.width = 4;
    s.foundry = false;
    toast("Subset patched. Open Results to compare.");
  }
}

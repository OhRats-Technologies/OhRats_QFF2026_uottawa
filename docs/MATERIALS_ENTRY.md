# SpinCourt: when would you believe a quantum magnet?

**Recommended track:** Materials Science. **Status:** implemented, locally validated, and measured on IBM. This is a proposed entry shape, not a submitted competition entry.

## The question

Can a small quantum simulation distinguish an entangled magnetic state from a separable state when the measurements are noisy and the shot budget is finite?

We simulate a four-spin Heisenberg ring with alternating bond strengths. Its fully separable energy threshold is −1 J. An energy estimate below that number looks persuasive, but a known separable control can fluctuate below it. The project makes the audience decide whether the evidence justifies a witness claim.

## What we built

1. **SpinWeave:** a four-qubit variational circuit, independently checked against exact ground energies at five dimerizations. The first restricted circuit failed and was replaced by alternating exchange layers.
2. **SpinCourt:** six fixed simulation challenges. The audience issues or withholds a model-based witness claim, then sees the reference state and uncertainty bound.
3. **SpinShield:** a one-sided Hoeffding sampling margin and a separate declared measurement-bias allowance. A classical finite-count convolution independently checks the reference cases. Conservative shot plans include a target detection probability and an independently known reference expectation.
4. **SpinTherm:** classical thermal controls and the independently checked two-dimer limit. These states were not prepared on IBM.
5. **Returned IBM counts:** three measurement bases on `ibm_quebec`, 1024 shots per basis. Public raw counts and their provenance are preserved.

## The actual device result

The ring returned energy **−1.865234 J**, with sampling standard error **0.026758 J**. The fixed one-sided 95% Hoeffding sampling upper is **−1.732746 J**, below the fully separable threshold **−1 J**.

This supports the energy witness under independent fixed-shot sampling, correct measurement bases, and a common prepared state. The sprint did not establish a bound on unknown device measurement bias or drift. The demo therefore lets the audience vary a **hypothetical** total bias allowance. The decision survives only while that allowance is below **0.732746 J**. This is sensitivity analysis, not measured calibration or an unconditional physical certificate.

The witness detects some entanglement; it does not prove genuine four-partite entanglement. Withholding the claim does not prove separability. Confidence is pointwise for a fixed decision, not a guarantee after repeated peeking or selecting the best run.

## Three-minute demonstration

**0:00–0:40 — The trap.** Open Materials in `demo/index.html`. Show the first SpinCourt trial: measured energy −1.036 J. Invite a verdict. Reveal that this was a known separable control and that the uncertainty-aware rule withholds detection.

**0:40–1:30 — The real experiment.** Show the returned IBM ring energy and fixed sampling upper. Explain the three measurement bases and the exact reference. The quantum circuit ran on a device; the small reference calculation runs classically.

**1:30–2:15 — Make the assumptions visible.** Move the hypothetical bias allowance from 0 to 0.80 J. The conditional verdict changes. Explain why more shots cannot by themselves establish a bound on unknown systematic errors.

**2:15–3:00 — A physical control and the contribution.** Show the independent-dimer thermal case: the two pairs can be entangled internally while their pair/pair cut is separable. Close with the rejected first ansatz, the validated replacement, and the public evidence trail.

## What is distinctive

Energy witnesses, Heisenberg simulations and Hoeffding bounds are established. We do not propose a new witness theorem or quantum algorithm. The contribution is a compact, reproducible experiment that joins a playable claim-checking challenge, physical controls, shot planning, returned hardware measurements, and explicit limits on what those measurements establish.

The four-spin model is classically tractable and does not predict a named material or demonstrate a quantum speedup. A strong presentation should make the quality of the experiment its central claim.

## Evidence and reproduction

- Offline demo: `demo/index.html`, Materials tab.
- Device counts: `artifacts/sprint-20261003/hardware-counts/scheduling-hardware.json`.
- Derived energies: `artifacts/sprint-20261003/evidence/summary.json`; select `REAL_IBM_HARDWARE`.
- Local controls: public `spinweave`, `spintherm`, `spinshield` and `spinaudit` snapshots.
- Check the source and evidence hashes and scientific tests: `uv run python -m tracklab.verify --tests`.
- Established witness theory: [Dowling, Doherty and Bartlett, Energy as an Entanglement Witness](https://arxiv.org/abs/quant-ph/0408086).
- Sampling bound: [Hoeffding, Probability Inequalities for Sums of Bounded Random Variables](https://doi.org/10.1080/01621459.1963.10500830).

The portfolio's editorial score is 4.30/5. It is a subjective submission-quality rating, not a probability of winning or an official judging rubric.

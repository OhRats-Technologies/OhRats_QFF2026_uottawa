# Quantum Worlds

Deadline: **2026-10-03, 22:00 America/Toronto** (2026-10-04 02:00 UTC).

Learn and audit action-conditioned latent quantum dynamics. The hypothesis is
that retaining the initial-state condition and respecting reversible physical
paths improves compositional prediction. Accuracy, validity and generalization
must be measured independently. A negative comparison is a result.

## Research cycle

1. State a mechanism and a falsifiable prediction before a run.
2. Screen cheap variants on designated validation data. Record failures too.
3. Freeze a choice, then generate independent confirmation data and seeds.
4. Challenge the explanation with a stronger baseline or a confound-removing
   ablation. Exploit improvements only after this check.
5. Maintain a report and provenance throughout; reserve the final 30 minutes
   for verification, figures, limitations and publication.

This is an iterative research workflow, not autonomous self-modification or
evidence of recursive scientific improvement. No hardware jobs are authorized
by this protocol. Do not chase nominal success by repeatedly selecting on the
same final holdout. New exploratory decisions require new confirmation data.

## Current experiment queue

| ID | Question | Gate for advancing |
|---|---|---|
| QW-01 | Does paired straight interpolation erase reversible transition information? | Exact collision witness and Qiskit-verified conventions |
| QW-02 | Does source conditioning repair endpoint-flow prediction? | Same endpoint supervision; solver convergence; multiple seeds |
| QW-03 | Does physical-path supervision preserve compositional prediction? | Explicitly disclose richer labels; compare with exact/learned linear dynamics |
| QW-04 | Does physical structure help with limited, noisy endpoint data? | Equal endpoint data; frozen tuning; fresh seeds; tune strong classical controls |
| QW-05 | Do conclusions survive a nonlinear latent representation? | Encoder/readout validity measured separately; no trivial collapsed solution |

The initial encoder is an invertible learned orthogonal basis of the complete
15 Pauli expectations. It prevents collapse by construction and allows exact
physical evaluation. It is not a learned low-dimensional visual representation,
an autoencoder reconstruction objective, or a reproduction of V-JEPA.

## Quality checks

- Qubit 0 is the left tensor factor, corresponding to Qiskit wire 1.
- Test gates against Qiskit and tangent labels against finite differences.
- Keep train, validation and final initial-state seeds distinct. All methods in
  a paired comparison receive identical data and measurement noise.
- Training angles lie in [-1.2, 1.2]; extrapolation angles have magnitude in
  [1.8, pi]. Multi-gate sequences are unseen because initial training comprises
  single transitions, not because a particular composition grammar is withheld.
- Evaluate raw physical validity before repair. Projected fidelity can hide
  model error. Report correction size, Pauli error and algebraic tests too.
- Treat guaranteed composition from a matrix exponential as architectural prior,
  not discovery. A skew-symmetric 15D generator preserves norm but need not
  preserve density-matrix positivity. A Hamiltonian commutator does.
- Keep simulator paths separate from straight latent paths and distinguish
  flow time, rotation angle and circuit length.
- Record actual time, seeds, parameters, sources and stage for every experiment.

## Closest prior work

[Flow Matching](https://arxiv.org/abs/2210.02747) introduces the vector-field
regression framework. [Flow-JEPA](https://arxiv.org/abs/2608.29029) already combines
JEPA and conditional flow prediction; its flow uses a Gaussian source and retains
the initial observation as a condition. Our unconditioned current-to-future chord
diagnostic does **not** establish a flaw in that method.

[Semigroup-JEPA](https://arxiv.org/abs/2609.10464) studies action-conditioned
physical generalization. [Quantum Flow Matching](https://arxiv.org/abs/2508.12413)
already studies quantum density-matrix generation with quantum circuits.
[Hamiltonian learning](https://www.nature.com/articles/s41467-023-44008-1) is an
established field. The potential contribution here is an audited quantum-state
transition benchmark and a controlled investigation of coupling, representation
and physical validity. Neither the broad combination nor Hamiltonian estimation
is established as novel by this sprint.

## Completed followups

This is a retrospective index of decisions recorded on the board and in the
append-only sprint ledger, not a claim that all later hypotheses were planned
before the sprint. Each run stores its actual prior protocol and source snapshot.

| Phase | Evidence | Outcome |
|---|---|---|
| Nonlinear JEPA confirmation | 60 paired runs, ten fresh seeds | Generator useful; two failed compositional encoders retained |
| Strong classical transfer | Same frozen encoders and observed endpoint labels | Much of the direct/flow deficit is in dynamics; classical competition remains |
| Control confirmation | All ten original checkpoints, 32 fresh shared tasks | Eight plan well; two forecasts can be exploited |
| Physical noise dictionary | 36 fits with equal data, 1,200 bootstrap rate fits | CPTP by construction; high fidelity need not settle a discrete EB index |
| Measurement design | 7,200 comparisons, 400 replicates/design/budget | Full-basis focused probing improves equal-shot index resolution |
| Readout stress | 3,600 policy comparisons, 200 replicates/scenario/budget | Blind model confidently wrong; independent calibration helps conditionally |
| Short-trajectory consistency | 16 initial, eight normalized diagnostic, twenty fresh runs | Loss-scale confound matters; two-step mixture still fails in two fresh seeds |
| Frozen trajectory control | 41 comparisons on 32 fresh shared tasks | Teacher-forced generator useful in all ten seeds; transferred linear is stronger |

Equivalence controls and shared seeds are not independent replications. Fresh
confirmation concerns fixed protocols on specified synthetic data, not general
architectural superiority. No additional hardware access was made.

The final deliverables are `REPORT.md`, `output/pdf/quantum-worlds-report.pdf`,
the sprint figures/audits/ledger, and all completed scientific artifacts. Source
and figure regeneration commands are in the report. A separate completion audit
checks completion counts, frozen hashes, dataset separation, matched shot
accounting, repository tests, rendered PDF and publication status.

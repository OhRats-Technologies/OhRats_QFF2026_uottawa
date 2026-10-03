# Implemented ideas and festival shortlist

The festival names QML, chemistry, materials and sustainability tracks. These ratings are **editorial submission potential**, not probabilities of winning or an official judging rubric. Score novelty honestly: the algorithms are established; a distinctive experiment, useful insight, clean controls and a memorable demo are the available contributions.

Ratings use track fit (25%), distinctiveness (25%), demo clarity/fun (20%), validated evidence (20%), and delivery feasibility (10%), each from 1 to 5. Treat small score differences as subjective. Hardware completion can strengthen evidence, but a queued job does not count as a measurement.

| Idea | Track | Fit | Distinctive | Demo | Evidence | Feasible | Weighted potential |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| SpinWeave: entanglement in a tiny magnet | Materials | 5 | 3 | 4.5 | 4.5 | 5 | 4.30 |
| EigenBudget: when adaptive shots stop helping | Chemistry | 5 | 3.5 | 3.5 | 4.5 | 5 | 4.23 |
| GridGuard: starting phases and valid schedules | Sustainability | 5 | 3.5 | 4 | 4 | 4.5 | 4.18 |
| FlyWalk: real connectivity, interference and lesions | Exploratory / outside the named tracks | 2 | 3.5 | 5 | 4.5 | 5 | 3.78 |
| KernelForge: a search that chooses fewer gates | QML | 5 | 2 | 3 | 4.5 | 5 | 3.75 |
| BondBench alone: H₂ energies and parity filtering | Chemistry | 5 | 1.5 | 3 | 4.5 | 5 | 3.63 |
| Initial BudgetBond allocator | Chemistry | 5 | 2.5 | 2 | 4 | 5 | 3.58; reject the improvement claim |

## Recommended submission shapes

**SpinWeave** is the clearest physical result: four-spin Heisenberg dimerization, independently checked energies, a rigorous separable bound, and noise that erases the witness. Its main limitation is novelty: energy witnesses and small spin simulations are established. Make the contribution a trustworthy interactive experiment, explain what the witness does and does not prove, and show the returned IBM evidence with its conditional sampling bound and uncharacterized systematic-error limitation. See [the focused materials entry and three-minute demo](MATERIALS_ENTRY.md).

**EigenBudget** has the strongest investigative narrative: an attractive allocator fails; a two-group eigenstate variance identity explains why; regularization fixes unseen-outcome failures; controlled imperfect states show when paid pilots become worthwhile. It is a measurement-resource benchmark, not a new VQE algorithm or a new theorem. Include all pilots and rejected shots and show uncertainty on improvements.

**GridGuard** is an accessible sustainability story: jobs move toward renewable availability; XY mixing preserves a scheduling rule; preparation phases change interference. The exact and greedy controls solve this tiny instance cheaply. The contribution is a controlled circuit-design comparison, not practical carbon savings or a speedup. Matched-optimizer follow-ups remove the confound in the original search. Two local phase corrections improve the original placement without changing its initial histogram, but large gains occur in only two of six heavy-job placements. The same generic compilation reports equal CX counts; backend optimization prunes the optimized circuits differently, so real-device costs are not equal.

**FlyWalk** remains the most playful demonstration and the origin of the repository. It uses a compact, pinned MaleCNS population graph; three qubits encode eight nodes. Keep it as the team's exploratory showpiece or supporting demo, rather than pretending it is a chemistry or QML application. It does not model fly thoughts, neuronal firing or biological quantum processing.

**KernelForge** is a useful architecture audit. Five split replications selected the unentangled preparation, and classical PCA/RBF classification won on average. Its result is honest and resource-aware, but a familiar Wine classification benchmark is unlikely to be the best headline submission by itself.

## Completed controls

- FlyWalk: independent analytic two-node limits, Qiskit/matrix-exponential agreement, same lesion time scale, 56 all-source interventions and 99 shuffled-weight controls.
- Noise: 432 sampling runs, separate gate and readout errors, exact noisy-density references and finite-shot error comparisons.
- BondBench: eight molecular geometries, two-qubit sector ansatz, independent PySCF FCI, two correlated measurement groups and symmetry filtering.
- EigenBudget: matched paid-shot budgets, independent production counts, original and regularized pilots, 400 repeats per state/budget, paired bootstrap sensitivity.
- SpinWeave: exact four-spin limits, magnetization conservation, rejected restricted ansatz, validated alternating exchanges, three measurement bases and a noise sweep.
- GridGuard: all 16 costs enumerated, six valid schedules, exact/greedy/uniform baselines, paired versus Dicke starts, matched optimizer budgets and seeds.
- KernelForge: train-only preprocessing, validation-only selection, frozen holdouts, matched classical controls, local finite-shot sampling and five split replications.

## Keep the scope small

Do not revive the retired Rockland/AABC work, build a full fly brain, classify biological sex from one male/female specimen, claim disease prediction, or combine every experiment into one submission. Eight-qubit fly partitioning and larger chemistry remain ideas, not completed deliverables. Select one primary project and use the lab portfolio to demonstrate how the team reached it.

The timed methodology and decisions are in `WORK_PLAN.md` and the append-only `EXPERIMENT_LOG.jsonl`. The frozen public evidence snapshot is in `artifacts/sprint-20261003/`; the portable demo is `demo/index.html`.

## Focused extensions and limitations

- **ActiveBudget:** LiH CAS(2,2), independently checked against CASCI, has four local measurement groups. Paid pilot allocation loses at 2048 shots and gives a conditional 12% RMSE reduction at 8192. The synthetic-noise audit removes any claim of consistent noise-robust savings. Keep this as evidence for the EigenBudget decision story.
- **SpinTherm / SpinShield:** extend the materials project with exact classical thermal controls and a conservative finite-shot/bias decision. A separable state can sample below the energy threshold; the uncertainty-aware rule withholds detection. Assumptions and pointwise confidence are visible. No new witness theorem or IBM thermal preparation is claimed.
- **FlyFlux:** a magnetic-graph-inspired direction encoding on the same real contact magnitudes. All starts and phase charges are tested. The direction effect is modest and model-dependent; phases are not neuronal measurements. Retain as a fun interference control rather than a claim about brains.

- Strength-preserving FlyWalk follow-up: retain the stronger control and the negative finding. Holding all population strengths and the intact time scale fixed reverses the earlier descriptive ordering. The 99 continuous graph alternatives are finite-chain exploratory controls, not independent biological specimens or a confirmatory p-value.

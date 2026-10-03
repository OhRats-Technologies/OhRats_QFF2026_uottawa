# Overnight experiment method

Implementation deadline: **2026-10-03 05:50 America/Toronto**. Report deadline: **06:00**. The owner requested approximately 30% fly examples and 70% other festival tracks. This is a development-time target, not a division of IBM shots or summed CPU time.

## Propose, test, retain

1. State a small question, an independent reference, and a failure condition.
2. Implement a bounded experiment with fixed seeds and explicit resource limits.
3. Validate the physics or mathematics before evaluating a proposed improvement.
4. Compare an established classical or simpler quantum baseline using matched resources.
5. Retain negative findings. Record follow-up changes as adaptive exploration, rather than disguising them as preregistered results.
6. Promote only reproducible results with clear interpretation and a usable demonstration.

This is inspired by the user's request for a dream-RSI style architecture loop. It is a bounded experimental workflow; the code does not recursively modify itself or invent evidence.

## Quality gates

- **Source:** attributed input data, pinned snapshot and hashes, or an explicit synthetic instance.
- **Correctness:** an analytic limit, exact enumeration, independent FCI reference, or another numerical implementation.
- **Reproducibility:** uv lockfile, deterministic seeds, complete settings and raw sample tables.
- **Comparison:** meaningful baselines and all resource overhead, including discarded pilot and postselected shots.
- **Interpretation:** distinguish a population from a neuron, a toy model from a material, and simulation from hardware.
- **Presentation:** inspect figures and exercise interactive controls.
- **Hardware:** confirmed event access, durable submission intent, bounded job count, actual returned counts. A queue receipt is not a result.

## Time and concurrency

`docs/EXPERIMENT_LOG.jsonl` is an append-only timestamped record. `timed_stage` records actual runtime of a stage and its passed/failed checks. Those durations are **compute/stage runtime**, not total human or agent development effort. Parallel runtimes must not be added together as wall-clock effort. Development allocation is recorded separately at work boundaries; the 30/70 split is approximate and will be reported candidly.

Independent local experiment processes can run concurrently with at most two simulation threads per process. Hardware collection is a single status check at a useful work boundary. While IBM jobs queue, continue local controls, replication, documentation and demo work. Stop broadening the portfolio when validation or polish would be sacrificed.

Hardware is capped at three jobs, at most six circuits per job, 1024 shots per submitted circuit in this sprint, and 300 seconds maximum execution allowance per job. All durable intents count against the cap. No claim of unlimited event allocation is made.

## Candidate decisions

- FlyWalk and its noise/lesion controls: retain as the playful real-data demo.
- BondBench: retain as independently checked chemistry groundwork.
- BudgetBond's initial pilot allocator: reject as a headline improvement; it lost to uniform allocation on the tested eigenstates.
- EigenBudget: retain the explanation and controlled imperfect-state follow-up. The eigenstate variance identity is elementary, not a new theorem.
- GridGuard: retain the state-preparation ablation; the cheap paired start was weak. The more costly Dicke start improves ideal optimization. Exact enumeration and greedy both solve this tiny case.
- KernelForge: retain as an architecture and baseline audit. Five split replications selected the unentangled feature map. The classical RBF baseline remained stronger on average.
- SpinWeave: reject the first restricted ansatz; retain alternating exchange layers, which pass the exact-energy checks and enable a physically meaningful entanglement-witness demonstration.

- ActiveBudget: retain the LiH CAS(2,2) extension. Four local groups break the two-group restriction, but paid pilots lose at 2048 shots and show a conditional gain at 8192. The active-space reference is independently checked against CASCI, not full-space FCI.
- ActiveNoise: retain the bias audit. The ideal gain is not consistent under the declared readout/gate errors; allocation cannot remove systematic error.
- SpinTherm: retain the exact classical thermal analysis and analytic independent-dimer threshold. Do not claim thermal-state preparation on IBM.
- FlyFlux: retain as an exploratory direction-encoding ablation. The phases are a declared graph model, not neural quantum phases; the modest directional effect is checked over all eight starts.

- Strength-preserving FlyWalk follow-up: retain the stronger control and the negative finding. Holding all population strengths and the intact time scale fixed reverses the earlier descriptive ordering. The 99 continuous graph alternatives are finite-chain exploratory controls, not independent biological specimens or a confirmatory p-value.

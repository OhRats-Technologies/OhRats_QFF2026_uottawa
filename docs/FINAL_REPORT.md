# Final report: spectral and certified mixing on a coarse-grained MaleCNS graph, and its quantum-channel extension

Informed by Kopel, *Pre-registered spectral and certified mixing analysis of the male Drosophila central nervous system connectome* (arXiv:2609.33054). This is a coarse-grained, eight-population experiment on the pinned MaleCNS snapshot (`datasets/fly/README.md`). It is **not** a replication of the full-CNS study, a biological claim, or a quantum-advantage claim. Each node is a cell-type population, not a neuron.

## 1. What was done

| Part | Method | Where |
| --- | --- | --- |
| Classical spectral analysis | Row-stochastic synapse-flow chain `P` (direction preserved in source CSVs, symmetrization only in the walk model), leading eigenvalues, spectral gap, stationary distribution, sweep-cut conductance | `flybrain/spectral.py` |
| Certified finite-step mixing | Dobrushin coefficient `tau(P^r)` with witness-row lower bound and hub-column upper bound | `flybrain/spectral.py` |
| Edge-pruning boundary trap | Threshold sweep, tracked `|lambda2|`, conductance, escape probability | `flybrain/channel_cli.py` |
| Signed influence map | Postsynaptic-normalized with median input floor; uncertainty lemmas 1–3 | `flybrain/spectral.py` |
| Quantum channel | CPTP map `E = gamma*Id + (1-gamma)*D_P`, true composition `E^r` via `SuperOp.power`, Choi state, PPT negativity | `flybrain/quantum_channel.py` |
| Exact EB certificate | Finite three-phase product twirl with rational arithmetic (by `fly-agent`) | `flybrain/channel_certificates.py`, `docs/CHANNEL_CERTIFICATES.md` |
| Hardware witness | Paired Z/X-basis circuits on `ibm_fez`, 128 shots per basis | `flybrain/hardware_channel.py`, `artifacts/ibm-20261003/conjugate-witness/` |

## 2. Results

### 2.1 Classical spectral results (measured on the real snapshot)

- Eight populations, 64 directed edges including self-loops; `|lambda2| = 0.8535`, spectral gap `0.1465`.
- Most metastable sweep cut is `T4a_R` (stationary mass 0.344, escape probability 0.0950).
- Certified Dobrushin coefficient: `tau(P^1) = 0.955`, `tau(P^7) = 0.360`, `tau(P^16) = 0.087`.

### 2.2 Edge-pruning boundary trap

Pruning weak edges lowers the escape probability of `T4a_R` and raises `|lambda2|`:

| Threshold | 0 | 20 | 50 | 200 | 500 | 1000 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| `|lambda2|` | 0.8535 | 0.8549 | 0.8559 | 0.8599 | 0.8707 | 0.8718 |
| Escape probability | 0.0950 | 0.0937 | 0.0928 | 0.0898 | 0.0755 | 0.0755 |

At threshold 5000 the giant strongly connected component shrinks to six nodes and the cut changes, so that point is a different graph and is not part of the trend. The trend direction agrees with the boundary-trap warning in the paper. It is one coarse graph, so this is qualitative consistency, not replication.

### 2.3 Quantum channel (ideal, simulated exactly)

For `gamma = 3/5`:

- Negativity `N(r)`: 1.941, 1.018, 0.471, 0.177, 0.039, 0.007 for `r = 1..6`, then 0 from `r = 7`.
- `N(r) > 0` for `r <= 6` rules out entanglement breaking there, so `n_EB >= 7`.
- An explicit 3^8-term product mixture reconstructs the step-7 Choi matrix (max entrywise error 2.1e-14), and exact rational certificates give the upper bound. Hence **`n_EB = 7` exactly** for this model.
- Exact EB step across `gamma = 0.2, 0.4, 0.6, 0.8`: fly graph 3, 5, 7, 16; uniform reset 2, 3, 5, 10; threshold-1000 pruned 3, 5, 8, 17.

### 2.4 Hardware witness (`ibm_fez`, measured)

Witness `S = <ZZ> + <XX>` on reference-system pairs; every separable state has `S <= 1`.

| Pair | `<ZZ>` | `<XX>` | `S` | Std. error | Excess over 1 |
| --- | ---: | ---: | ---: | ---: | ---: |
| (0, 3) | 0.7031 | 0.6562 | 1.359 | 0.092 | 3.9 sigma |
| (1, 4) | 0.7969 | 0.6094 | 1.406 | 0.088 | 4.6 sigma |
| (2, 5) | 0.7188 | 0.6094 | 1.328 | 0.093 | 3.5 sigma |

The local AerSimulator gave `S = 1.82–1.87`. The drop to about 1.33–1.41 on hardware is observed degradation; it was not predicted from a recorded calibration model. `fly-agent` independently recomputed all three `S` values and errors from the exported counts.

## 3. Corrections made along the way (kept visible)

1. **Channel powers.** The first implementation used `gamma^r I + (1-gamma^r) D_{P^r}` instead of true composition. A two-node `r = 2` counterexample exposed this. Fixed with `SuperOp.power`; the earlier `n_EB = 6` was wrong and is superseded by 7.
2. **PPT versus separability.** Zero negativity on an 8×8 Choi state is not a general separability proof. It was reported as a lower bound until the explicit product decomposition supplied the upper bound.
3. **Single-basis hardware readout.** The first IBM run (Z basis only, 128 shots, 72.7% matching registers against 96.1% ideal) could not certify entanglement. It was replaced by the Z/X witness.
4. **Dobrushin comparison.** My board acknowledgment quoted `0.710` as `tau(P^7)`. That value is `tau(M^7)` for the population chain `M = 0.6 I + 0.4 P` of the channel itself; the raw synapse-flow value is `tau(P^7) = 0.360`. The `classical_dobrushin` series in `results/spectral_channel/results.json` is for `P^r`, not `M^r`. Corrected by `fly-agent`; both indicate remaining classical memory at step 7 but they are different chains and must not be conflated.

## 4. Verification

- `uv run python -m unittest discover -s tests -v`: 57 tests pass (spectral bounds, CPTP checks, true-composition counterexample, conjugate witness, certificate reconstruction against Qiskit `SuperOp`).
- `uv run python -m flybrain run` and `uv run python -m flybrain channel --steps 10` run cleanly.
- Hardware artifacts exclude credentials, account identifiers and private job IDs; SHA-256 manifest in `artifacts/ibm-20261003/manifest.json`.

## 5. Conclusion

On this coarse-grained eight-population graph, the classical Kopel-style analysis behaves as the paper warns: weak-edge pruning produces a near-trap at `T4a_R` and pushes `|lambda2|` toward 1. In the ideal identity-retention channel built on the same graph, entanglement breaking occurs at exactly step 7, while classical population memory is still substantial (`tau(P^7) = 0.360`, `tau(M^7) = 0.710`). So loss of entanglement and completion of classical mixing are distinct events here. A single-run hardware witness on `ibm_fez` shows pairwise reference-system entanglement surviving one unitary walk step, with 3.5–4.6 sigma excess over the separable bound under trusted X/Z measurements.

## 6. Limits and open questions

- Eight cell-type populations, one snapshot, one lesion/source choice in the walk demo; no full-CNS or biological claim.
- The channel is a model chosen for analysis. The hardware experiment ran a unitary walk, not the multi-step measured-and-prepared channel, so it does not test the step-7 threshold.
- The witness bounds sampling error only (128 shots per basis), not systematic readout error, and certifies pairwise entanglement, not six-qubit entanglement.
- The pruning comparison and the model-dependence of `n_EB` are exploratory; there is no monotonicity theorem. `fly-agent` has an open isospectral-controls claim that tests whether spectrum alone determines `n_EB`.
- Not implemented: a noisy multi-step hardware realization of the channel.
- No quantum advantage, and no inference of biological quantum computation.

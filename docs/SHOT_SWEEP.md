# Do more shots rescue noisy feature selection?

[Documentation Index](README.md) · [Main Report](REPORT.md) · [Hardware Mitigation](IBM_PIPELINE_MITIGATION.md)

**Both devices complete: 12 real IBM jobs, 301,056 returned shots, 108 charged QPU seconds.** More measurements collected more valid candidates. They did not restore high feasible yield or guarantee a better subset. No wildfire predictor was retrained.

## What we measured

Reuse the exact device-native compiled circuits from the preceding frozen confirmation: 10, 16 or 20 candidate features, selecting exactly four. Parameters, features, initialization, measured mapping and gate sequence remain unchanged; copied QPY hashes match their parents. Each device has six independent jobs: 512, 1,024 and 2,048 shots, each raw and with combined dynamical decoupling (DD)/gate-and-measurement twirling. Every job contains 21 selector, basis-control and calibration PUBs at the same shot count. Fresh 512-shot jobs provide the reference. Fixed staggered level/arm order differs across devices; execution order is not randomized.

A **valid measurement** has exactly four selected features. The valid percentage is usable yield, not prediction accuracy. **Best objective gap** is the lowest observed training-QUBO cost minus its exact feasible minimum; zero means the optimum was sampled. Actual addon SQD verifies that minimum in the observed diagonal subspace; it creates no unsampled state. Readout reweighting also retains only observed feasible states. The tables report directly measured feasibility and observed minima, without silently replacing them by corrected results.

## The 20-feature result

| Device | Arm | 512 shots: valid | 1,024 shots: valid | 2,048 shots: valid | Best gaps at 512 / 1,024 / 2,048 |
|---|---|---:|---:|---:|---|
| Marrakesh | Raw | 74 (14.45%) | 129 (12.60%) | 259 (12.65%) | 0.2201 / 0.2090 / 0.0895 |
| Marrakesh | DD + twirling | 13 (2.54%) | 35 (3.42%) | 75 (3.66%) | 0.0582 / 0.2562 / 0.1791 |
| Quebec | Raw | 2 (0.39%) | 10 (0.98%) | 19 (0.93%) | 0.6851 / 0.1482 / 0.1912 |
| Quebec | DD + twirling | 4 (0.78%) | 6 (0.59%) | 12 (0.59%) | 0.3198 / 0.2968 / 0.3027 |

Marrakesh raw yield stays around 13–14%, and Quebec raw yield stays below 1%. Four times as many measurements therefore collect more usable samples without removing the invalid fraction. Marrakesh raw improves its best gap at 2,048; Quebec raw is best at 1,024. The Marrakesh combined arm is best at 512. Separate executions are not nested samples, so realized minima need not improve monotonically.

The combined arm has lower 16/20-feature valid yield than raw on Marrakesh at every level. This is evidence against treating DD/twirling as an automatic improvement. The two mechanisms were combined, not isolated; correlated execution effects and calibration drift remain unresolved. All six Marrakesh 10-feature circuits sample the optimum, while Quebec does so in three of six. Its 210-state feasible space is already cheap to enumerate classically.

![Measured valid fraction on both devices, common scale within each pool](figures/shot-sweep-both-yield.png)

## Comparison with classical sampling

One hundred uniform-feasible trials are saved at each **physical-shot budget** and **accepted-shot budget**. Every draw index is retained and independently replayed. The former asks what classical sampling gets from the full draw count; the latter asks about the quality of the surviving hardware candidates. Matching draw count does not match runtime, since classical sampling has no QPU or rejection cost.

At 20 features, full-budget uniform sampling averages gaps **0.0850 / 0.0625 / 0.0432**, lower than 11 of the 12 corresponding measured hardware minima. The exception is Marrakesh combined at 512 (0.0582). Accepted-budget comparisons are mixed: a hardware sample can beat the uniform mean at the same accepted count, but many physical measurements were discarded. One realized hardware minimum against a Monte Carlo mean does not establish an advantage.

![Observed best objective gap and classical full-budget controls](figures/shot-sweep-both-quality.png)

Simple basis-state controls retain **65.87–75.20%** valid outputs at 20 features on Marrakesh and **78.81–90.04%** on Quebec, far above their selectors. That points to substantial loss during the selector circuit beyond readout alone. These controls do not reproduce its gate sequence and cannot identify one noise mechanism. The 20-feature selector has 1,237 native CZ gates and depth 990 on both devices; its poor yield is not a clean test of measurement noise alone.

## Cost and turnaround

| Device | Jobs | Physical shots including controls/calibration | Charged QPU seconds | Created-to-finished range |
|---|---:|---:|---:|---|
| Marrakesh | 6 | 150,528 | 54 | 11.63–14.27 minutes |
| Quebec | 6 | 150,528 | 54 | 21.12–37.58 seconds |

Each arm costs **5 / 8 / 14 seconds** at 512 / 1,024 / 2,048. These are whole-job charges, covering all three pools, basis controls and calibration. Each account reserved 102 seconds; actual cost was 54. Queue turnaround is separate from QPU charge and does not establish device speed. The personal instance now reports **322/600 seconds consumed, 278 remaining**. Shared PINQ reports 3,148 remaining; its usage change includes activity beyond our 54-second sweep. Unused sweep reservations are released and no jobs remain pending.

## Limits and recommendation

Wilson 95% intervals assume independent Bernoulli shots; they exclude calibration drift and correlations across randomized executions. One job per condition cannot establish a causal shot effect, consistent mitigation benefit or intrinsic device ranking. The devices differ in calibration, account access and native timing. No final-year reads or new predictor fits occurred, so better objective sampling is not evidence of improved wildfire prediction or quantum advantage.

**Recommendation:** explain more shots as buying candidate coverage at increased cost, not repairing the circuit. For these larger pools, prioritize shallower circuits and measured mechanism-specific controls before increasing shot budgets further. This recommendation is not an additional authorized experiment.

## Full measured selector table

Charges repeat across pools sharing one arm/shot job; do not sum repeated rows. Accepted-budget uniform means are descriptive controls, not paired hardware replications. Raw counts, every basis control/calibration, SQD checks, readout weights, compilation details and both classical budgets are in the immutable evidence bundles.

| Device | Pool | Arm | Shots | Valid | Best gap | Uniform mean gap: accepted budget | Whole-job QPU seconds |
|---|---:|---|---:|---:|---:|---:|---:|
| Marrakesh | 10 | DD/twirl | 512 | 168 (32.81%) | 0.0000 | 0.0136 | 5 |
| Marrakesh | 10 | DD/twirl | 1,024 | 334 (32.62%) | 0.0000 | 0.0046 | 8 |
| Marrakesh | 10 | DD/twirl | 2,048 | 604 (29.49%) | 0.0000 | 0.0017 | 14 |
| Marrakesh | 10 | Raw | 512 | 136 (26.56%) | 0.0000 | 0.0154 | 5 |
| Marrakesh | 10 | Raw | 1,024 | 290 (28.32%) | 0.0000 | 0.0046 | 8 |
| Marrakesh | 10 | Raw | 2,048 | 573 (27.98%) | 0.0000 | 0.0017 | 14 |
| Marrakesh | 16 | DD/twirl | 512 | 57 (11.13%) | 0.1039 | 0.1072 | 5 |
| Marrakesh | 16 | DD/twirl | 1,024 | 100 (9.77%) | 0.0697 | 0.0818 | 8 |
| Marrakesh | 16 | DD/twirl | 2,048 | 196 (9.57%) | 0.0954 | 0.0531 | 14 |
| Marrakesh | 16 | Raw | 512 | 120 (23.44%) | 0.0233 | 0.0708 | 5 |
| Marrakesh | 16 | Raw | 1,024 | 228 (22.27%) | 0.0036 | 0.0452 | 8 |
| Marrakesh | 16 | Raw | 2,048 | 469 (22.90%) | 0.0300 | 0.0236 | 14 |
| Marrakesh | 20 | DD/twirl | 512 | 13 (2.54%) | 0.0582 | 0.2685 | 5 |
| Marrakesh | 20 | DD/twirl | 1,024 | 35 (3.42%) | 0.2562 | 0.2209 | 8 |
| Marrakesh | 20 | DD/twirl | 2,048 | 75 (3.66%) | 0.1791 | 0.1777 | 14 |
| Marrakesh | 20 | Raw | 512 | 74 (14.45%) | 0.2201 | 0.1791 | 5 |
| Marrakesh | 20 | Raw | 1,024 | 129 (12.60%) | 0.2090 | 0.1492 | 8 |
| Marrakesh | 20 | Raw | 2,048 | 259 (12.65%) | 0.0895 | 0.1111 | 14 |
| Quebec | 10 | DD/twirl | 512 | 108 (21.09%) | 0.0000 | 0.0203 | 5 |
| Quebec | 10 | DD/twirl | 1,024 | 223 (21.78%) | 0.0410 | 0.0098 | 8 |
| Quebec | 10 | DD/twirl | 2,048 | 486 (23.73%) | 0.0000 | 0.0027 | 14 |
| Quebec | 10 | Raw | 512 | 117 (22.85%) | 0.0410 | 0.0187 | 5 |
| Quebec | 10 | Raw | 1,024 | 194 (18.95%) | 0.0209 | 0.0098 | 8 |
| Quebec | 10 | Raw | 2,048 | 440 (21.48%) | 0.0000 | 0.0035 | 14 |
| Quebec | 16 | DD/twirl | 512 | 15 (2.93%) | 0.1095 | 0.1971 | 5 |
| Quebec | 16 | DD/twirl | 1,024 | 45 (4.39%) | 0.1646 | 0.1202 | 8 |
| Quebec | 16 | DD/twirl | 2,048 | 75 (3.66%) | 0.1039 | 0.0930 | 14 |
| Quebec | 16 | Raw | 512 | 25 (4.88%) | 0.1078 | 0.1568 | 5 |
| Quebec | 16 | Raw | 1,024 | 52 (5.08%) | 0.2275 | 0.1135 | 8 |
| Quebec | 16 | Raw | 2,048 | 98 (4.79%) | 0.0233 | 0.0756 | 14 |
| Quebec | 20 | DD/twirl | 512 | 4 (0.78%) | 0.3198 | 0.3672 | 5 |
| Quebec | 20 | DD/twirl | 1,024 | 6 (0.59%) | 0.2968 | 0.3257 | 8 |
| Quebec | 20 | DD/twirl | 2,048 | 12 (0.59%) | 0.3027 | 0.2711 | 14 |
| Quebec | 20 | Raw | 512 | 2 (0.39%) | 0.6851 | 0.4550 | 5 |
| Quebec | 20 | Raw | 1,024 | 10 (0.98%) | 0.1482 | 0.2895 | 8 |
| Quebec | 20 | Raw | 2,048 | 19 (0.93%) | 0.1912 | 0.2496 | 14 |

## Replay

```sh
uv run python scripts/collect_hardware_search.py shot-sweep-marrakesh
uv run python scripts/collect_hardware_search.py shot-sweep-quebec
```

Collectors reconstruct measured feasibility, objectives, SQD gaps, retained uniform draws and charge totals from [Marrakesh evidence](results/shot-sweep-marrakesh.json) and [Quebec evidence](results/shot-sweep-quebec.json). They use no credentials, source cache, fitting, sampling, new states or submissions. The [closeout receipt](data/shot_sweep_handoff.json) records verification and preserved final hashes.

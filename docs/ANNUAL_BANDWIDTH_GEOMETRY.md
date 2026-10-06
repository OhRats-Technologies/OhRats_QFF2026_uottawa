# Input bandwidth changes quantum kernel geometry

Post-final diagnostic following the QSVR guide. Frozen at `870abe2` before execution, after the 2019–2024 results were inspected. It reads **only 1988–2018 input columns**, not targets/test rows. One linear ZZ repetition; same 31 annual inputs and train-only input standardization. No predictor is fitted and no scale is selected.

| Inputs / qubits | Amplitude | Mean off-diagonal fidelity | Effective rank / 31 | Minimum eigenvalue | Condition |
|---|---|---:|---:|---:|---:|
| 4 | pi/32 | 0.767713 | 2.190 | 5.272e-07 | 4.583e+07 |
| 4 | pi/16 | 0.411802 | 5.311 | 7.725e-05 | 1.81e+05 |
| 4 | pi/8 | 0.137995 | 15.037 | 0.009819 | 609.1 |
| 4 | pi/4 | 0.076187 | 25.200 | 0.1278 | 27.07 |
| 4 | pi/2 | 0.058740 | 27.329 | 0.2835 | 10.26 |
| 10 | pi/32 | 0.538897 | 5.187 | 0.00657 | 2651 |
| 10 | pi/16 | 0.144300 | 19.028 | 0.1356 | 42.33 |
| 10 | pi/8 | 0.007667 | 30.661 | 0.7579 | 1.794 |
| 10 | pi/4 | 0.000805 | 30.998 | 0.9801 | 1.049 |
| 10 | pi/2 | 0.000859 | 30.997 | 0.9565 | 1.093 |

**The near-identity regime is adjustable; it is not an inevitable result of using ten qubits.** On the identical ten-input training rows, narrowing the angle amplitude from pi/4 to pi/32 changes effective rank from 30.998 to 5.187 and raises average similarity. Four-input rank changes from 25.200 to 2.190. This is expected from the guide’s bandwidth mechanism. The broadest similarities also approach a low-rank/constant regime; neither endpoint certifies prediction.

The pi/4 ten-qubit matrix reproduces the frozen main training Gram to numerical precision. [Collection/control audit](data/annual_bandwidth_audit.json) rechecks the ten matrices and all original 83 final predictions/24 matrix pairs. Main results and chosen models remain unchanged. Per-feature scales, target alignment, chronological predictive tuning and sampled PSD repair are still future work.

Execution: **48.89 s**, ten exact training matrices and **4,650 analytic fidelity pair circuits**, zero predictor fits/device jobs/shots. This is separately charged post-final diagnostic work, not another predictive replication or a fifth development model-search plan. [Frozen plan](../experiments/annual_bandwidth_geometry.json) · [all summary values](results/annual-bandwidth-geometry.json) · [145-test/69-CLI QA](data/annual_bandwidth_repository_checks.json).

## Reproduce in a new namespace

```sh
uv run --no-sync python scripts/annual_bandwidth_geometry.py run --output .cache/wildfire/annual-qsvr/new-geometry
uv run --no-sync python scripts/annual_bandwidth_geometry.py collect --output .cache/wildfire/annual-qsvr/new-geometry
```

These commands need the public 31-row table and locked quantum dependencies, no raw sources or credentials. Run prepares new analytic circuits; collect uses only that saved namespace. Existing intents are preserved.

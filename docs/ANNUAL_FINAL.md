# Frozen annual evaluation

Ontario annual mean agency-reported fire size, in hectares per size-observed incident. Training uses 1988–2018; the six 2019–2024 evaluation years overlap the earlier incident study and are explicitly reused. Same-year climate makes this retrospective annual estimation.

## Training freeze

The plan is [`annual_final.json`](../experiments/annual_final.json). All parameter choices and learned model states were saved before evaluation in [`annual-final-training.json`](results/annual-final-training.json), with the byte-pinned [receipt](data/annual_final_training_receipt.json). Training completed in **93.75 s**, with 80 final predictor fits, 288 classical inner fits and 216 quantum inner fits. Reusing identical kernels across C/epsilon and repeated feature subsets required 36 quantum matrices, below the cap of 50. QAOA used 109 optimizer calls, below 120. Execution was local analytic simulation; no hardware jobs.

Each kernel family had 36 chronological inner candidates per width. Selected configurations:

| Model | Four inputs | Ten inputs |
|---|---|---|
| Ridge alpha | 10 | 10 |
| Linear SVR C / epsilon | 0.1 / 0.5 | 0.1 / 0.2 |
| RBF C / epsilon / gamma multiplier | 10 / 0.5 / 16 | 10 / 0.05 / 4 |
| QSVR C / epsilon / repetitions / angle amplitude | 10 / 0.5 / 2 / pi/2 | 10 / 0.5 / 1 / pi/4 |

The three expanding inner folds use only training years. Feature order is canonical across selectors; no test-based subset or circuit choice is allowed. Train-mean, train-median and calendar-year controls remain in the comparison.

The original milestone placed evaluation at 4:25 PM. Training completed ahead of that estimate, so evaluation moves earlier without changing its recipe, budget or model choices. The remaining time goes to saved-evidence audit, reproduction, year-specific figures and reporting.

## Evaluation and collection

The exclusive evaluation is pending. It will compute fixed predictions from saved coefficients/support weights and scalers, without predictor fits. Per-year actual values and errors will accompany MAE/RMSE/bias. The fixed selector crossover includes every planned selector and predictor; a best row is not independent confirmation.

```sh
uv run --no-sync python scripts/run_annual_final.py train --output .cache/wildfire/annual-qsvr/final-v1
uv run --no-sync python scripts/run_annual_final.py evaluate --output .cache/wildfire/annual-qsvr/final-v1
uv run --no-sync python scripts/collect_annual_final.py --run .cache/wildfire/annual-qsvr/final-v1 --output .cache/wildfire/annual-qsvr/final-v1/audit.json
```

These are the original execution commands. Existing training/evaluation intents block replay into the same namespace. Collection verifies saved matrices and prediction equations; it performs no fits, shots or new quantum states.

## Literature steering

The [QSVR guide](<QSVR with Qiskit Literature and Performance Guide.md>) supports the frozen train-only scaling, joint C/epsilon tuning, shallow maps and matched RBF budget. Condition number, eigenspectrum and concentration will be reported from saved matrices. Per-feature scale tuning and trainable alignment are future work: they would expand this frozen search without independent validation. Sampled PSD repair and duplicate-skipping apply to a future shot-based study; this exact simulation validates raw PSD and has no sampled-kernel repair. Six reused years support descriptive model gaps, not significance or quantum-advantage claims.

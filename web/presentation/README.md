# Five-minute annual wildfire presentation

The measured annual development story is ready; **final 2019–2024 reused-year results remain pending**. [Report](../../docs/REPORT.md) · [study notes](../../docs/ANNUAL_QSVR.md).

Use the chapter format of the [earlier presentation](https://github.com/seofernando25/csi5341-vla-jepa/tree/a6427885b3a0bf12c218b455c44b7c468288f938/web/presentation), with minimal controls and presenter notes. Use bun if frontend dependencies are needed. A player is not implemented; this run prioritizes measured science and the outline.

| Beat | Seconds | Finding / visual |
|---|---:|---|
| Question | 30 | Ontario annual mean reported hectares per fire; 31 training years |
| Data | 50 | 39,616 source fires aggregated without classifier-coordinate/weather exclusions; station coverage and masked forest context |
| Classical reference | 55 | Chronological controls; RBF four-input MAE 77.02 vs training-mean 92.00 |
| Quantum comparison | 70 | Matched 36-candidate selection: QSVR four-qubit 86.64; ten-qubit fidelities near .001 |
| Selection / data lesson | 55 | QAOA does not beat uniform sampling; diagonal SQD equals sampled minimum; climate completeness changes errors |
| Final evaluation / conclusion | 40 | Insert frozen reused-year results when measured; small annual sample, retrospective sources, extreme-year errors and no hardware advantage |

Total: **300 seconds**. Keep claim strength tied to measured evidence. The quantum segment should show what was actually encoded and what the kernel did, not imply more qubits necessarily improve prediction.

Use these annual figures, with source/split/units visible:

- [Observed and predicted annual means](../../docs/figures/annual-development/annual-development.png): development predictions in 2007–2018 and source denominators.
- [Equal-budget comparison](../../docs/figures/annual-development/annual-matched.png): three chronological folds; dots are fold errors, not confidence intervals.
- [Kernel similarities](../../docs/figures/annual-development/annual-kernel-similarity.png): exact local state fidelities; ten-qubit similarity loss.

Mean size, annual total area and incident count are different quantities. These figures answer the macro task; the older incident confusion matrices stay in supporting evidence. Update the final beat after evaluation without selecting a model from test errors.

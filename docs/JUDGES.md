# Judge guide

[Presentation](https://fireline.ohrats.party/presentation/) · [Play Fireline](https://fireline.ohrats.party/) · [Repository overview](../README.md)

**Question:** Can quantum kernels improve retrospective annual Ontario wildfire-size estimates under a matched tuning budget?

**Finding:** Classical RBF leads matched development: 77.02 ha/fire MAE versus QSVR’s 86.64. On the six reused 2019–2024 evaluation years, no main climate model beats the training mean’s 276.81 ha/fire. Four-input QSVR beats matched RBF there, but misses the annual extremes.

## What the experiments contribute

- **Annual dataset and comparison.** One Ontario year per row: 31 training years, ten climate summaries and an audited mean-size target. The frozen evaluation reads saved model states and performs no fitting.
- **Encoding diagnosis.** Ten-qubit kernels make years almost unrelated. Smaller input angles restore similarity but can approach a nearly constant kernel. The result explains flat predictions rather than claiming quantum advantage.
- **Real-device diagnostics.** [Mitigation on Fez, Marrakesh and Quebec](IBM_PIPELINE_MITIGATION.md) separates kernel accuracy from prediction error. [Shot sweeps](SHOT_SWEEP.md) show that more measurements collect more valid subsets without repairing their low yield. [Selector experiments](SELECTOR_HARDWARE.md) compare sampled costs with downstream regression.
- **Playable teaching.** [Fireline](https://fireline.ohrats.party/) lets players choose features and tune angle, C and epsilon. Betty explains the controls and gives contextual hints. Its browser calculations are separate from research results.

## Five-minute route

Start with the [presentation](https://fireline.ohrats.party/presentation/): seven main slides cover the question, dataset, selection, comparison, annual errors, encoding and conclusion. Two appendices cover hardware. Press **N** for notes and sources; **F** for fullscreen.

For the evidence, read the [main report](REPORT.md), [frozen evaluation](ANNUAL_FINAL.md) and [reproduction instructions](REPRODUCIBILITY.md). [Presentation controls and local setup](../web/presentation/README.md) and [game controls](../web/demo/README.md) are available separately.

## What to keep in mind

The target is annual mean reported hectares per fire, not total hectares burned. Same-year climate makes this retrospective estimation. Only 31 years are available for training, and the six evaluation years were previously inspected. Later hardware diagnostics do not replace the original simulated final comparison.

The repository includes public code, tables, figures, saved prediction receipts and tests. The [recorded critique closeout](data/critique_response_handoff.json) reports its verification snapshot; current tests can be run using the README commands. The live browser deck is newer than the preserved PDF/PowerPoint downloads.

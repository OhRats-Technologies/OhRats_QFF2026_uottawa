# Documentation

[Play Fireline](https://fireline.ohrats.party/) · [Presentation](https://fireline.ohrats.party/presentation/)

The [repository README](../README.md) is the overview. Six guides cover the detailed work:

| Document | Read it for |
| --- | --- |
| [Report](REPORT.md) | Annual comparison, final parameters, yearly denominators and limitations |
| [Data and methods](DATA_SCHEMA.md) | Sources, aggregation, encoding, QAOA/SQD and forest contracts |
| [Reproduction](REPRODUCIBILITY.md) | Saved-evidence checks, commands and historical source reconstruction |
| [Hardware mitigation](IBM_PIPELINE_MITIGATION.md) | Three-device kernels, readout correction, DD and twirling |
| [Hardware selection](SELECTOR_HARDWARE.md) | Expanded feature pools, measured predictor kernels and cost accounting |
| [Shot sweep](SHOT_SWEEP.md) | 512/1,024/2,048-shot yield and subset quality |

[Game instructions](../web/demo/README.md), [presentation controls and narration](../web/presentation/README.md), [asset credits](../web/demo/canvas/ASSETS.md) and [hosting](../deploy/fireline/README.md) live beside their implementation.

Numerical tables, source manifests, raw-count summaries and verification receipts stay in `data/` and `results/`; figures stay in `figures/`. The [repetition microkernel results](results/repetition-microkernel.json) and [hardware ledger](data/hardware_accounting.json) retain their measured budgets.

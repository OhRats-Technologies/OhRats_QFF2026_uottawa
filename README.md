# Qiskit Fall Fest · Ontario wildfire study

**Annual mean reported fire size, one Ontario year per observation.** Train **1988–2018**; evaluate **2019–2024 as reused years**. The goal is active until **October 5, 5 PM Toronto**. Final evaluation is pending.

Matched development MAE: four-input RBF-SVR **77.02** vs four-qubit QSVR **86.64 ha/fire**. Quantum selection does not beat simple sampling controls. Climate quality and kernel concentration matter. [Report](docs/REPORT.md) · [Progress and evidence](docs/ANNUAL_QSVR.md).

```sh
uv sync --locked --group data --group analysis --group quantum
uv run --no-sync python scripts/pipeline.py annual matched --output .cache/wildfire/annual-qsvr/new-matched --execute
```

The public 31-year table and pinned quantum receipts support this quick replay without raw downloads. Preview by omitting `--execute`. Operations: `classical`, `quantum`, `matched`, `selectors`, `context`, `woodland`. Every run needs a new output directory. No development operation opens test targets or submits hardware.

For classical replay, add `--dataset docs/data/annual_training.csv`. Classical raw preparation and the context/woodland stages require ignored source files; see [reproduction](docs/REPRODUCIBILITY.md), [source coverage](docs/DATA_DOWNLOADS.md), [schema](docs/DATA_SCHEMA.md) and [pipeline guide](docs/PIPELINE.md).

```sh
uv run --no-sync python scripts/pipeline.py check
```

[Current development verification](docs/data/annual_repository_checks.json): **130 tests / 64 CLI help paths** at `9c40214`. Later changes receive new receipts; this is not whole-goal completion.

[Goal](GOAL.md) · [Quantum methods](docs/QUANTUM_METHODS.md) · [Talk outline](web/presentation/README.md) · [Board](AGENT_BOARD.md).

The earlier incident-classification results remain [separate evidence](docs/FINAL_EVALUATION.md). [Scope correction](docs/SCOPE_CORRECTION.md) records the earlier macro omission. Raw snapshots stay in `data/`, runs in `.cache/`, and credentials in ignored `.env`. [Placeholders](.env.example) · [Agent instructions](AGENTS.md).

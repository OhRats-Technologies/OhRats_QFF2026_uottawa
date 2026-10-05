# Qiskit Fall Fest · Open challenge

Ontario wildfire modelling using [Agency Reported Wildfires in Canada](https://cwfis.cfs.nrcan.gc.ca/en/catalogue/results/937eb7be-83fd-4b94-a122-9cc0385f3bf7). Target: **1985–2025**, with ECCC monthly weather and NRCan annual woodland context. See [the project goal](GOAL.md), [data schema](docs/DATA_SCHEMA.md) and [dataset notes](datasets/wildfires/README.md).

```sh
uv sync --locked
uv run python scripts/download_wildfires.py --output data/wildfires/ontario
```

Downloads are ignored by Git. The feed contains fire updates, not one independent fire per row or a complete daily observation grid.

Reusable resources:

- [Qiskit/SQD learning path](docs/sqd/LEARNING_PATH.md) and [solved masterclass](notebooks/Rishabh_tutorial_sqd_masterclass_solved.ipynb).
- `sqd_lab/`: local chemistry experiments and classical controls.
- `quantum_world/`: independent quantum dynamics and measurement code; [completed report](quantum_world/REPORT.md).

```sh
uv run python -m unittest discover -s tests -v
```

Keep credentials in ignored `.env`; placeholders are in [.env.example](.env.example).
[Agent instructions](AGENTS.md) · [Board protocol](AGENT_BOARD.md).

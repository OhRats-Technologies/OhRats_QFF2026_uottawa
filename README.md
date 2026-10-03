# FlyWalk & Quantum Track Lab

Qiskit experiments for Fall Fest 2026: fly connectivity, chemistry, materials, sustainability and quantum machine learning.

## Run locally

Python 3.12, managed with uv:

```sh
uv sync --locked
uv run python -m flybrain run
uv run python -m flybrain.noise
uv run python -m tracklab.verify --tests
```

FlyWalk compares classical diffusion and a three-qubit quantum walk on eight MaleCNS cell-type populations. Results and plots go to `results/`. Local runs need no IBM account.

## Fly explorer

Real 3D anatomy, weighted connections, continuous quantum/classical traces and saved hardware comparisons.

```sh
bun install --cwd explorer --frozen-lockfile
bun run --cwd explorer start
```

Open [localhost:8765](http://127.0.0.1:8765/). To rebuild:

```sh
uv run python -m flybrain.explorer
bun run --cwd explorer build
```

[Explorer controls and sources](docs/FLY_EXPLORER.md) · [Portfolio demo](demo/index.html)

## Experiments

| Track | Run with `uv run python -m …` |
| --- | --- |
| Fly graphs | `flybrain.atlas`, `flybrain.strengthnull`, `flybrain.flux` |
| Chemistry | `tracklab.chemistry`, `tracklab.budgetbond`, `tracklab.eigenbudget`, `tracklab.activebudget` |
| Materials | `tracklab.spinweave`, `tracklab.spintherm`, `tracklab.spinshield` |
| Sustainability | `tracklab.scheduling`, `tracklab.phaseguard` |
| QML | `tracklab.kernelforge` |

[Final report](docs/OVERNIGHT_REPORT.pdf) · [Materials submission](docs/MATERIALS_ENTRY.md) · [Ideas and findings](docs/FEST_IDEAS.md)

## Data and hardware

[MaleCNS provenance](datasets/fly/README.md). Fly model time is dimensionless; these experiments do not establish biological quantum computation or quantum advantage.

Three IBM jobs returned 14 circuits at 1,024 shots each. [Public counts](artifacts/sprint-20261003/hardware-counts/) are separate from simulations. Keep credentials in ignored `.env`; use [.env.example](.env.example) for configuration. The explorer submits no jobs.

[Agent instructions](AGENTS.md) · [Coordination protocol](AGENT_BOARD.md)

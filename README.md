# Connectome Mixing & Quantum Channels

Spectral mixing on MaleCNS population graphs and quantum-channel forgetting, informed by [Kopel’s connectome study](https://arxiv.org/abs/2609.33054). The eight-population model is a coarse-grained experiment, not a full-CNS replication.

## Run

```sh
uv sync --locked
uv run python -m flybrain.channel_cli
uv run python -m flybrain run
```

Classical analysis compares spectral contraction, mixing bounds and pruning. The quantum model compares channel composition and Choi entanglement. Negative partial transpose rules out entanglement breaking; zero negativity alone does not prove it.

## Explore

```sh
bun install --cwd explorer --frozen-lockfile
bun run --cwd explorer start
```

[Local explorer](http://127.0.0.1:8765/) · [Controls and sources](docs/FLY_EXPLORER.md) · [MaleCNS provenance](datasets/fly/README.md)

## Evidence

[IBM measurements](artifacts/ibm-20261003/README.md) include raw counts and circuits. The conjugate-basis witness tests pairwise reference–system entanglement under trusted measurements; it does not demonstrate biological quantum computation, quantum advantage or hardware multi-step noisy-channel mixing.

Local runs require no credentials. Keep tokens in ignored `.env`; use [.env.example](.env.example) for configuration. The explorer submits no jobs.

[Agent instructions](AGENTS.md) · [Coordination protocol](AGENT_BOARD.md)

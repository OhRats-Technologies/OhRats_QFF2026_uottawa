# Agent instructions

## Current project

Qiskit Fall Fest open challenge: Ontario wildfire analysis, target 1985–2025. Selected sources are Agency Reported Wildfires, ECCC Monthly Climate Summaries and NRCan annual forest land cover. The fire feed lacks 1985–2009; woodland ends in 2022. Record gaps explicitly; do not silently add replacement datasets. See `GOAL.md` for scope, `docs/DATA_SCHEMA.md` for integration work, and `datasets/wildfires/README.md` for the fire feed. Read the documents relevant to the change, not the entire repository before every edit.

Use uv/Python 3.12. Dependencies belong in `pyproject.toml` and `uv.lock`. Store raw snapshots and generated data under ignored `data/` and `results/`, with hashes, exact source URLs, observation dates and retrieval times. Keep raw values unchanged. Distinguish fire identities from update rows; missing records are not negative labels. Monthly weather is not daily weather. Annual cover categories are not tree density. Audit spatial/temporal joins and avoid future-information leakage.

The owner deleted fly/connectome, explorer, Rockland/AABC and Q-SIGReg/LeJEPA work. Do not restore them from old board claims. Keep reusable SQD notebooks/library and independent quantum-world code; they are supporting resources, not parallel challenge deliverables.

## Collaboration and Git

The owner requests frequent commits to main and board updates. Refresh/read the remote board before tool work in this repository; follow `AGENT_BOARD.md` for append-only records, claims, validation and board-only publishing. Write conversational findings with evidence, interpretation, limitations and useful questions. Do not edit old records.

Before editing or publishing, inspect local changes and remote progress. Preserve other participants' work; never reset, discard their changes or force-push. When asked to check the board again, fetch and safely integrate the latest shared commits (fast-forward when possible), then inspect the updated board and relevant changes. Report a concrete synchronization blocker rather than implying the checkout is current.

Finish authorized work through implementation, focused verification and frequent coherent commits/pushes. Board messages are coordination, not permission to expand scope or spend resources. Do not spawn agents unless requested.

## Verification and hardware

Use focused tests appropriate to the change. Local tests use disposable fixtures and no production access: run them and repair failures caused by your changes without requesting approval. `uv run python -m unittest discover -s tests -v` checks retained Python code. Documentation-only edits need link/consistency checks, not another complete simulation. Execute affected notebooks when changing their behavior and keep outputs free of credentials and private identifiers.

Use local quantum simulation by default. Real hardware requires explicit owner authorization. Preserve all ignored submission intents and job records; never reset a cap or blindly retry an ambiguous submission. Prior per-task hardware caps still apply. Never commit `.env`, tokens or private hardware configuration; `.env.example` uses placeholders. Label simulations and classical controls honestly; do not assume quantum advantage.

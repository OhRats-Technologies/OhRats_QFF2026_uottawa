# Agent board protocol

The authoritative coordination log is `AGENT_BOARD.jsonl`. This protocol supports any number of human or agent participants across machines and sessions.

## Storage and order

- The log is append-only. Never edit, delete, reorder, pretty-print, or rewrite existing records.
- Write one compact JSON object per line in UTF-8, with a trailing newline. No blank lines or comments. New records use schema version `v=1`.
- File order is authoritative causal order. `ts` is UTC creation metadata; never sort the log by timestamp.
- Use `CORR` to correct a prior record. Corrections preserve the original record and explain the replacement meaning.
- Keep messages concise. Never include secrets, large logs, private data, or absolute machine-specific paths. Reference repository-relative paths, task IDs, or commit hashes instead.

## Participants and scope

Use a stable, descriptive participant ID, such as `fern-agent`, `reviewer`, or `build-agent-2`. IDs must match `[A-Za-z0-9][A-Za-z0-9_-]{0,63}`; `*` is reserved for broadcast recipients. Different concurrently active agents must use different IDs. State your role in a `MSG` when joining if useful. No fixed roster is required.

Use `scope="repo"` for repository-wide matters. For focused work, use a consistent nonempty task or component scope, such as `task:bell-demo` or `component:setup`. Scope is a label, not a filesystem path or access boundary. Include the intended files and work in claims so overlap can be identified across different scope labels.

## Refresh and publish

Before coordination-sensitive work, fetch the shared branch and read its board:

```sh
git fetch origin main
git show origin/main:AGENT_BOARD.md
git show origin/main:AGENT_BOARD.jsonl
```

Substitute the configured remote and shared branch if they differ. Fetching does not modify a dirty worktree. If the board does not exist remotely yet, use the local protocol during bootstrap and report that state. Inspect local unsent records as well as the remote log.

Before appending, refresh remote state again. Preserve the remote log as an exact prefix, then append new records. Validate JSON, required fields, unique IDs, and backward references before committing.

The repository owner authorizes agents to commit and push coordination records to the shared branch as part of this protocol. After appending and validating records, create a board-only commit and push it promptly, independently of unfinished code. Do not wait for task completion or ask for confirmation for each routine board update. This authorization covers coordination records only; it does not authorize publishing code or other external actions. Explicit user restrictions take precedence.

Communicate at task start, when asking or answering questions, when plans or ownership change, when blocked, and when work completes. During sustained work, post a concise progress update when there is meaningful new information, and check the remote board at natural work boundaries so questions receive timely replies. Avoid repeated unchanged status messages. Batch closely related records into one board-only commit when useful, but do not leave actionable messages unpublished.

If local history includes unpushed code commits or the checkout is unsuitable, use a clean worktree based on the shared remote branch for the board commit. Do not include unrelated files.

If a push is rejected or the log conflicts, refresh again, preserve the remote log byte-for-byte, and append unsent local records after its tail. Check IDs to avoid duplicates. If several unsent records reference each other, retain their order. Do not force-push. A board commit communicates coordination; it does not approve code, experiments, or external actions.

## Record schema

```json
{"v":1,"id":"build-agent-20261003T041800Z-12ab34cd","ts":"2026-10-03T04:18:00Z","from":"build-agent","to":"*","type":"CLM","ref":null,"scope":"component:setup","msg":"Update uv setup in README.md and pyproject.toml."}
```

All fields are required:

| Field | Meaning |
| --- | --- |
| `v` | Integer `1`. |
| `id` | `<from>-<YYYYMMDDTHHMMSSZ>-<8 lowercase hex characters>`; globally unique. Timestamp must match `ts`. |
| `ts` | RFC3339 UTC creation time at second precision, ending in `Z`. |
| `from` | Participant ID. |
| `to` | Participant ID or `*` for broadcast. |
| `type` | One of `MSG`, `ASK`, `ACK`, `CLM`, `DONE`, `BLK`, `DEC`, `CORR`. |
| `ref` | ID of an earlier record in file order, or `null`. |
| `scope` | Nonempty scope label shared by related work. |
| `msg` | Nonempty single-line text. |

Record types:

| Type | Purpose |
| --- | --- |
| `MSG` | Status or context. |
| `ASK` | Question or coordination request. |
| `ACK` | Acknowledge a prior record; reference it. |
| `CLM` | Claim planned shared work, with files and intended changes. |
| `DONE` | Close a claim with results and verification; reference its `CLM`. |
| `BLK` | Close a claim as blocked or abandoned, stating what remains; reference its `CLM`. |
| `DEC` | Record a decision and its rationale within existing authority. |
| `CORR` | Correct a prior record; reference the corrected record. |

`ACK`, `DONE`, `BLK`, and `CORR` require a non-null `ref`. Only the original claimant should close its claim. To resume after `BLK`, append a new `CLM` referencing the blocked record. A claim is active until closed; do not infer expiry from its timestamp. For an apparently stale claim, ask the claimant or user before taking over.

## Existing logs

Do not copy unrelated historical records into a new repository. If adopting this protocol with an existing log, preserve that history and document any legacy schema separately. Never fabricate records on behalf of other participants.

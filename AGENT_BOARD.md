# Agent board protocol

The authoritative coordination log is `AGENT_BOARD.jsonl`. This protocol supports any number of human or agent participants across machines and sessions.

## Storage and order

- The log is append-only. Never edit, delete, reorder, pretty-print, or rewrite existing records.
- Write one compact JSON object per line in UTF-8, with a trailing newline. No blank lines or comments. New records use schema version `v=1`.
- File order is authoritative causal order. `ts` is UTC creation metadata; never sort the log by timestamp.
- Use `CORR` to correct a prior record. Corrections preserve the original record and explain the replacement meaning.
- Keep messages focused but explanatory; brevity must not remove interpretation or uncertainty. Never include secrets, large logs, private data, or absolute machine-specific paths. Reference repository-relative paths, task IDs, or commit hashes instead.

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

Finish validation successfully before starting the commit/push command. A failed validator must not fall through to publication through a later shell line.

The repository owner authorizes agents to commit and push coordination records to the shared branch as part of this protocol. After appending and validating records, create a board-only commit and push it promptly, independently of unfinished code. Do not wait for task completion or ask for confirmation for each routine board update. This authorization covers coordination records only; it does not authorize publishing code or other external actions. Explicit user restrictions take precedence.

Communicate at task start, when asking or answering questions, when plans or ownership change, when blocked, and when work completes. During sustained work, post a concise progress update when there is meaningful new information, and check the remote board at natural work boundaries so questions receive timely replies. Avoid repeated unchanged status messages. Batch closely related records into one board-only commit when useful, but do not leave actionable messages unpublished.

If local history includes unpushed code commits or the checkout is unsuitable, use a clean worktree based on the shared remote branch for the board commit. Do not include unrelated files.

If a push is rejected or the log conflicts, refresh again, preserve the remote log byte-for-byte, and append unsent local records after its tail. Check IDs to avoid duplicates. If several unsent records reference each other, retain their order. Do not force-push. A board commit communicates coordination; it does not approve code, experiments, or external actions.

## Collaborative discussion

Write to another collaborator who needs to understand and respond to your work. A board is a conversation as well as a coordination log. Result announcements must explain their meaning, not just list numbers, commits or passed checks.

For substantive results, add a short paragraph in the record or a linked follow-up `MSG` covering:

- What you tried and learned, and why it matters to the shared objective.
- Whether the result was expected or surprising relative to the baseline, paper or prior prediction; distinguish demonstration, replication and new evidence.
- What is measured, simulated, inferred or still uncertain, including assumptions that limit the conclusion.
- Your recommended next step or a specific question for another participant when their judgment would help.

Usually a few connected sentences suffice. Keep detailed derivations and logs in repository documents and link their relative paths. Do not add filler, invent surprise or ask performative questions merely to satisfy a template.

Address relevant participants with `to` and use `ref` to connect replies to the result or question. Acknowledge substantive feedback, explain agreement or disagreement, and report what you changed or why you retained an approach. Read incoming questions at natural work boundaries and answer them when possible; if you need more evidence, say what is missing. Do not imply an independent review has occurred when only a board summary was read.

A `DONE` closes the stated claim, not unrun owner requirements. Report completion against the owner’s objective and observation unit, not a narrowed agent-authored protocol. Identify missing required experiments explicitly; correcting a mistaken completion claim requires a `CORR` referencing it. A `DONE` need not end the scientific discussion. Follow up with interpretation or questions when useful. Corrections use `CORR` and explicitly qualify the earlier claim. Publishing discussion does not authorize additional experiments, spending or unrelated changes.

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

Two existing IDs predate strict format validation: `antigravity-20261003T201000Z-abc123` and `owner-steer-20261005T191027Z-d8d1bf81`. Preserve their records and references. Two further preserved peer IDs omit the compact timestamp separator: `antigravity-20261006202222Z-aaf0159d` and `antigravity-20261006202843Z-6d3fa703`. Preserve their bytes and references. These four format exceptions do not waive JSON/schema, uniqueness or backward-reference checks, and do not permit noncanonical IDs in new records.

# Data and processing pipeline

The earlier scope assessment below describes the 1 PM run. The owner authorized a new annual study through 5 PM; [current annual implementation and measured progress](ANNUAL_QSVR.md) supersede its unrun status as milestones finish.

**Annual front door:** `pipeline.py annual <classical|quantum|matched|selectors|context|woodland|collect> --output <new-directory>` previews the implemented macro stages; add `--execute` to run. The commands further below describe the preserved incident branch. [Scope correction](SCOPE_CORRECTION.md) · [implemented annual schema](DATA_SCHEMA.md).

For a fresh clone, `uv run python scripts/pipeline.py annual collect --output .cache/wildfire/annual-public --execute` verifies/extracts the checksum-pinned public bundle and collects 83 saved predictions without raw downloads, fitting or quantum execution. It refuses an existing output directory. [Final collection](ANNUAL_FINAL.md#portable-collection).

Use `scripts/pipeline.py` as the scientific front door. Specialist scripts remain available for individual studies and pinned historical reproduction.

**Forest map context:** `uv run --only-group data --frozen python scripts/context/pipeline.py plan --include-wms` previews a separate bounded acquisition pipeline. Replace `plan` with `prepare` to fetch seven coarse height epochs and five optional dated display layers into ignored replica paths. Its `asset-manifest.json` indexes numeric arrays and display images separately, with relative paths, grids and checked hashes. It runs no predictors and preserves published scientific receipts. [Prepared schema](DATA_SCHEMA.md#prepared-forest-context-contract) · [units, budgets and reproduction limits](FOREST_CONTEXT.md#limits-and-reproduction).

```sh
uv sync --locked --group data --group analysis --group quantum
uv run --no-sync python scripts/pipeline.py run
```

`run` previews the source-to-training-feature sequence. `run --execute` downloads missing selected inputs, verifies snapshot hashes, prepares lagged weather/NFDB labels and joins static 1984 woodland. Verified existing inputs skip acquisition. It passes actual dataset paths between stages; no fingerprint needs copying by hand. Without a plan, this prepares data only. Add a declared `--plan` and `--axis` to carry the prepared dataset into a bounded training-only screen and export its outcome summary. This optional screen requires a separate replica whose adaptive discovery is still open; the original final intent blocks it before any preparation. Neither path opens the final test or submits hardware.

## Commands

| Command | Purpose |
|---|---|
| `doctor --verify` | Check 915 required input/sidecar files and identify missing or changed snapshots. Nonzero exit means inputs are not ready. |
| `run` / `run --execute` | Preview / execute acquisition through training features; optional `--plan` and `--axis` also screen and summarize. |
| `prepare` | Run the same preparation from existing verified inputs. Source recipes must be committed. |
| `status` | Summarize saved reservations/outcomes and bounded follow-ups; this is not a live process check. |
| `screen --dataset … --plan … --axis …` | Preview a bounded selection/prediction/encoding screen; `--execute` runs it. Existing final intents still close adaptive reservations. |
| `collect --output …` | Recollect discovery, final, policy and goal evidence into a **new directory**. Requires original saved run records; fits no model. |
| `check` | Run fixture tests and every specialist CLI help path. |

Each subcommand has its own `--help`. The existing `prepare-weather` and `new-experiment` commands remain compatible. Status, reservations and orchestration now live in separate modules; the CLI is only dispatch.

## Fresh clone or existing snapshots

```sh
uv run --no-sync python scripts/pipeline.py doctor --verify
uv run --no-sync python scripts/pipeline.py run --execute
```

A full screening preview in a separate replica:

```sh
uv run --no-sync python scripts/pipeline.py run --plan experiments/historical_woodland_combinations.json --axis combinations
```

Add `--execute` there to run the declared budget and write a compact `summary-*.json` beside its outcome. It compares the plan's classical/quantum selector and predictor combinations without opening test years. The working repository has finished adaptive discovery: collect its saved evidence instead of resetting its final intent.

The selected preparation needs roughly 342 MiB of original input bytes. Acquiring the 1984 woodland crop requires a temporary national ZIP of about 1.5 GB; only that one year is needed for this fixed-cover study. The downloader bounds archive size, crops native classes and removes temporary national files. Weather acquisition uses three workers and reuses hashed month files.

Public URLs can serve revised data. Changed existing snapshots are preserved and stop execution; use the [input index](data/reproduction_inputs.json) and [pinned reproduction guide](REPRODUCIBILITY.md) to restore originals. Weather sidecar acquisition times may differ. A new woodland receipt may differ in retrieval metadata, but its crop/archive hashes and requested region must match; genuine provenance is retained and reported, never relabelled as the old acquisition. The final training table must match the published SHA-256.

A fresh clone does **not** contain ignored per-example run records. Rebuilding inputs cannot recollect old experiments. For existing saved records:

```sh
uv run --no-sync python scripts/pipeline.py collect --output .cache/wildfire/report-collections/my-review
```

The output directory must not exist. Existing scientific outcomes, submission intents and committed summaries are preserved. Independent scientific replication uses the historical recipe commits and a separate workspace/cache described in [reproduction](REPRODUCIBILITY.md); do not reset the original final intent.

## Data contracts and storage

| Stage | Storage | Contract |
|---|---|---|
| Acquire | Ignored `data/raw/` | Raw source bytes and sidecars stay unchanged. NFDB historical incidents and operational update rows are separate. |
| Prepare | `.cache/wildfire/processed/weather/<fingerprint>` | Preserve station IDs/zeroes; flag missing/invalid values and monthly availability. No fitted imputer or selector. |
| Join | `.cache/wildfire/features/historical-{weather,woodland}/<fingerprint>` | Training-only NFDB labels, lagged station context, native buffered categories and explicit exclusions. |
| Experiment | `.cache/wildfire/experiments/<plan-hash>` and exclusive study namespaces | Frozen budgets, actual outcomes, provenance and preserved failures. |
| Report | `docs/`, `web/presentation/` | Compact audited evidence and the five-minute findings plan. |

Recipe/raw/config hashes define cache versions. Historical preparation now depends directly on `weather_preparation.py`, rather than CLI/status code. New provenance namespaces can contain identical tables; that is **not a predictive replication**. Old scored datasets and manifests remain intact. Preparation records the committed recipe and checks the final table hash.

The implemented incident target is reported size ≥10 ha **conditional on eligible recorded incidents**, not ignition or a complete census. Approximate coordinates are not snapped; annual classes are not tree density; monthly observations are not daily weather. Retrospective map processing and unknown publication latency limit forecasting claims. [Schema](DATA_SCHEMA.md) · [source assumptions](SOURCE_ASSUMPTIONS.md) · [label/geography audit](LABEL_QUALITY.md).

The single 2019–2024 opening is complete. Saved-prediction collectors validate metrics, samples and recoverable historical recipes without refitting. [Final evidence](FINAL_EVALUATION.md) and [independent policy evolution](POLICY_EVOLUTION.md) remain separate. No new IBM jobs are authorized by these commands.

## Verification

Normal groups install local data, analysis and quantum dependencies. Notebook/hardware groups are opt-in. [Current isolated QA](data/workflow_repository_checks.json) pins **115 fixtures / all 55 help paths** at `8998e2a`, with a fresh 37-distribution environment and no production inputs copied. All **162 Python files** remain below 300 lines (maximum 250). The [integration receipt](data/workflow_integration_checks.json) verifies exact training-table reproduction, committed recipes and saved-evidence collection. It preserves all 1,310 prior data/cache files and 28,417 shared-environment files, adding eight derived files across preliminary and committed data-path checks. No new model fit, final opening or hardware call occurred.

The [usability 113/55 receipt](data/workflow_usability_repository_checks.json), [initial workflow 110/55 receipt](data/workflow_initial_repository_checks.json), [earlier policy 103/55 check](data/policy_repository_checks.json) and 93/54 dependency snapshot remain unchanged. Policy formatting preserves Python ASTs and recollects byte-identical results. Status/reservation logic also retains its original AST after moving to separate modules. The new primary commands have stage-specific help; specialists remain available for focused audits and exact historical recipes. The [document/source check](data/workflow_document_checks.json) verifies relative file links, source hashes and protected scientific hashes. The saved 81-row export checks all nine selector/predictor pairs with both group/selector schema support; earlier scientific summaries remain intact. Full screening handoff is fixture-tested. The [separate fixed-recipe replica](data/fixed_recipe_reproduction.json) reproduces all final metrics, samples and selected features using the original public snapshots; it exercises the documented historical commands rather than the new optional adaptive screen. Complete fresh network reacquisition was not run. Tests establish execution behavior, not source completeness or quantum advantage.

## Comprehensive followup replay

The [comprehensive report](RESEARCH_FINDINGS.md) gives six local-study and four hardware-bundle names. `uv run python scripts/collect_search.py STUDY` and `uv run python scripts/collect_hardware_search.py STUDY` are read-only arithmetic collectors. They require no credentials, source caches, fitting, new states, sampling or submissions. Producer recipes remain pinned in each evidence bundle; hardware namespaces and intents are exclusive and cannot be restarted.

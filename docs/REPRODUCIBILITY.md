# Reproduction

## Current annual study

The public annual training table allows quick classical, quantum and selector development without raw downloads. Use the locked environment and a new output for each command:

```sh
uv sync --locked --group data --group analysis --group quantum
uv run --no-sync python scripts/pipeline.py annual classical --dataset docs/data/annual_training.csv --output .cache/wildfire/annual-qsvr/new-classical-replay --execute
uv run --no-sync python scripts/pipeline.py annual matched --output .cache/wildfire/annual-qsvr/new-matched-replay --execute
uv run --no-sync python scripts/pipeline.py annual quantum --qubits 4 --output .cache/wildfire/annual-qsvr/new-quantum-replay --execute
```

Prepared CSV replay uses parsed floats; the original raw classical run consumed pre-serialization floats. Preserve this distinction when checking exact predictions. To reconstruct the annual table from sources, omit `--dataset`; the runner verifies/prepares weather automatically, then aggregates NFDB incidents. Context accepts an explicit prepared weather CSV through its specialist script. Woodland requires yearly crops and the pinned boundary, acquired with `scripts/download_ontario_boundary.py`. [Annual recipes, figures and evidence](ANNUAL_QSVR.md). The final reused-year opening remains pending.

## Preserved incident recipe

The recipes below reproduce the earlier incident-classification study. They are historical; they do not define the current annual experiment. Preserve old intents and receipts.

## Required inputs

- `data/raw/weather/`: original ON monthly CSV/JSON pairs for 1987–2024; sidecars contain each raw SHA-256.
- `data/raw/nfdb-audit/source.zip`: SHA-256 `9eb4773dfc60cfcfe7d76efa0f2470cdd341f4967fbec8084041f3fab87f8be3`.
- `data/raw/woodland/woodland-1984.tif` and `.json`: native crop SHA-256 `68dffad8b7db14bf4a38d2c154cb973df0dec3337a65884b89bce0087066352c`.

Annual maps and operational update records are unnecessary for this final recipe. Do not copy `.env`, private hardware results or any existing final-test intent into the new copy. Raw sources remain ignored in Git. Current-version download URLs can change; changed snapshots cannot reproduce the original experiment merely because their filenames match.

The [selected input index](data/reproduction_inputs.json) exposes every required weather CSV hash and public URL, plus the NFDB ZIP and 1984 crop/receipt. It covers **456 CSVs / 456 weather sidecars / three other files**, roughly **342.4 MiB** of original inputs. It hosts metadata, not raw bytes; the 10.90 GiB of acquired annual crops is unnecessary for this final replica. Source URLs can serve revised bytes, and a national ZIP URL is not a direct regional-TIFF download.

A [bounded public-source check](data/reproduction_source_check.json) on October 5 refetched weather 1987-01, 1988-01, 2018-12 and 2024-12 plus the NFDB ZIP. All five responses match the published SHA-256/size; the NFDB response is a valid ZIP. The 1984 national archive returned HTTP 200 and its expected 1,520,973,970-byte content length to a HEAD request, with no body downloaded. This checks four of 456 weather files and one current observation. It does not verify the forest archive hash, reproduce its crop, certify all source URLs or guarantee future availability. Original data/caches remain unchanged.

Weather receipt timestamps may differ after a fresh acquisition: preparation checks their status/CSV hash and fingerprints the CSV bytes, configuration and recipe. The cover namespace also includes `archive_sha256`, `crop_sha256` and `local_archive`. A newly acquired crop with different provenance can have identical values but a different namespace. Keep its real receipt; do not relabel it or overwrite a frozen intent. Exact namespace reproduction below uses the original source receipts.

## Build the exact training table

The original training table used preparation commit `4a38f46`. Later code organization/provenance changes can create new cache identifiers even when CSV values are identical. Pin the preparation version, then switch to the separately frozen final evaluator.

```sh
WILDFIRE_SOURCE=/path/to/existing/OhRats_QFF2026_uottawa
git clone https://github.com/OhRats-Technologies/OhRats_QFF2026_uottawa wildfire-replication
cd wildfire-replication
cp docs/data/reproduction_inputs.json ../wildfire-reproduction-inputs.json
git switch --detach 4a38f46
mkdir -p data/raw/weather data/raw/nfdb-audit data/raw/woodland
cp -R "$WILDFIRE_SOURCE/data/raw/weather/." data/raw/weather/
cp "$WILDFIRE_SOURCE/data/raw/nfdb-audit/source.zip" data/raw/nfdb-audit/
cp "$WILDFIRE_SOURCE/data/raw/woodland/woodland-1984.tif" data/raw/woodland/
cp "$WILDFIRE_SOURCE/data/raw/woodland/woodland-1984.json" data/raw/woodland/
uv sync --locked --group data --group analysis --group quantum
export OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1
```

The index is copied outside the checkout because the historical preparation commit predates it. Verify the selected copied inputs before building; weather receipt hashes are informational, while CSV hashes and the original crop/ZIP/receipt bytes are pinned:

```sh
uv run --no-sync python - <<'PY'
import hashlib, json
from pathlib import Path
index = json.loads(Path('../wildfire-reproduction-inputs.json').read_text())
inputs = [row for year in index['weather_years'] for row in year['inputs']]
for row in inputs + index['other_inputs']:
    digest = hashlib.sha256()
    with Path(row['file']).open('rb') as source:
        for block in iter(lambda: source.read(1024 * 1024), b''):
            digest.update(block)
    assert digest.hexdigest() == row['sha256'], row['file']
for row in inputs:
    receipt = json.loads(Path(row['sidecar']).read_text())
    assert receipt['status'] == 'downloaded' and receipt['sha256'] == row['sha256']
print('Verified 459 byte-pinned sources and 456 weather receipts.')
PY
uv run --no-sync python scripts/build_historical_features.py --lags 1 2 3
uv run --no-sync python scripts/add_woodland_features.py --dataset .cache/wildfire/features/historical-weather/5b9e54931d2a9d1b1f83 --fixed-year 1984
```

Expected training cache: `historical-woodland/f8a46f515b5b90b753a8`, 37,801 rows, CSV SHA-256 `b60618f65e1f8a71ddd9b8afe099efff49e4adf1d48acf2be6465b91207de8d8`. The typed weather output SHA-256 is `859c5153616f0b23b2af518d609590648ee56734582826bbf7545eb666dde8a4`. Both manifests retain raw/recipe hashes; check them before the final step.

## Execute the fixed evaluator in the new copy

```sh
git switch --detach 30b90f9
uv sync --locked --group data --group analysis --group quantum
uv run --no-sync python scripts/run_final_evaluation.py
uv run --no-sync python scripts/audit_final_evaluation.py
```

The evaluator checks committed recipes and exact training/source hashes, creates a new exclusive intent, and saves predictions. Expected held-out cohort: 3,820 fires; feature CSV SHA-256 `bd39f9bb82ddfa02aa3f630c922942c3cc09b878ead7136ca77f292fe982f5be`. It evaluates six full-training controls and 27 equally capped selector/predictor combinations. No hardware or LLM request occurs. Compare metrics and selected subsets with [committed evidence](results/final-evaluation.json); timestamps, elapsed times and outcome hashes will differ. The original same-host runner took 5.34 seconds excluding startup/acquisition, not a portable timing guarantee.

The [fixed-recipe reproduction](data/fixed_recipe_reproduction.json) executed these commands in a separate local clone, copying only the 915 original public input/receipt files. It rebuilt the exact training table and reproduced all metrics, sample hashes and selected features for six full-training models and 27 capped combinations, with zero numeric difference. The full copy/setup/preparation/evaluation/audit sequence took 53.11 seconds; its final runner took 5.44 seconds. Nine derived records remain in a separate ignored namespace; temporary raw copies, clone and environment were removed. This is reproducibility on the same snapshots and held-out years, not another independent predictive confirmation. The original intent/outcome remains unchanged. Full public-source network reacquisition was not run. The original preparation and evaluator files are recoverable in Git; these commands pin those recipes. Source availability, historical coordinate accuracy and operational validity remain separate audits.

## Coordinate audit without fitting

With the exact training table and source ZIP in place, use commit `654e2dd` or its descendants:

```sh
uv run --no-sync python scripts/audit_feature_quality.py --dataset .cache/wildfire/features/historical-woodland/f8a46f515b5b90b753a8 --coordinates-only
```

This reads only incident IDs, years and coordinates. It checks the source archive hash, numeric recurrence/grid alignment, original-fold geometry and local WGS84/NAD83 transformation sensitivity. It does not read final-year features, fit models or change the earlier weather/cover audit. The [receipt](data/coordinate_quality.json) and [source interpretation](SOURCE_ASSUMPTIONS.md) separate observed patterns from accuracy claims.

## Training-only follow-ups

The same hashed 37,801-row training table supplies the owner-requested follow-ups. Their opening commits and local namespaces are:

| Study | Opening recipe | Saved namespace |
|---|---|---|
| FidelityQuantumKernel / SQD | `5b7fdbf` | `library-followup-v3` |
| Shared landmarks | `227eeee` | `quantum-landmarks` |
| Fixed SVM convergence audit | `fc2a68c` | `kernel-convergence` |
| Kernel ridge | `74715bd` | `kernel-ridge` |
| Pure seasonal/geographic controls | `7f5edae` | `seasonal-baseline` |
| Labels-free analytic shot budget | `af75bec` | `shot-feasibility` |
| Initialization/mixer selector ablation | `ba09a49` | `constrained-selection` |
| Local fidelity/QGT geometry | `3f928ca` | `local-geometry` |
| Matched tangent/exact ridge control | `982d6b8` | `tangent-prediction` |
| Fixed landmark ridge measurement model | `b34d367` | `landmark-shot-ridge` |
| Exhaustive proxy alignment | `b36f7cc` | `proxy-alignment` |

All namespaces are under ignored `.cache/wildfire/`. In the existing workspace, use `collect_library_followup.py`, `collect_landmarks.py`, `collect_convergence.py`, `collect_ridge.py`, `collect_seasonal_baseline.py`, `collect_shot_feasibility.py`, `collect_constrained_selection.py`, `collect_local_geometry.py` or `collect_tangent_prediction.py` to audit their saved records. Public evidence alone does not include the original per-example predictions/coefficients or exact matrices required by collection. Do not delete intents to restart a study. The tangent check also requires its original hashed geometry and ridge parents; an independently generated parent needs a separately frozen lineage receipt.

`collect_shot_ridge.py` audits the later landmark measurement-model check from its original saved exact matrices and eighteen aggregate count arrays. It neither draws nor solves. Independent replication requires a separately frozen lineage receipt for newly generated parent outcomes; preserve original intents. [Its report](LANDMARK_SHOT_RIDGE.md) distinguishes modeled exposure from Qiskit sampler shots and actual device work.

`proxy_alignment.py collect` checks all 70 feasible subset predictions and the prior exact/L1 references without fitting. Its fixed parent outcome is required; a new parent needs a separate frozen lineage receipt. The [descriptive maximum](PROXY_ALIGNMENT.md) on reused validation years cannot become a new selected model. Its three fixtures/help path are included in the expanded 90/52 QA snapshot at `9fa3127`; the older 84/49 receipt remains separately pinned.

The post-final [probability report](PROBABILITY_REPORT.md), committed before collection at `82dbab3`, uses `audit_probability_report.py` and `plot_probability_report.py`. It reads the original hashed final outcome/evidence and performs no fitting. Newly generated final parents require a separate frozen reporting recipe; do not change old hashes or intents. Its three fixtures and both new help paths are included in the expanded isolated integration snapshot at `9fa3127`.

The training-only [cohort-geography extension](LABEL_QUALITY.md#geography-of-the-exclusions), frozen at `4559194`, reuses the source/weather/static-cover hashes and the immutable original label-audit receipt. Its documented ignored output paths preserve that parent. New table namespaces or parent receipts require a separate frozen reporting config; never relabel provenance to force the old one. It fits nothing and reproduces existing class-specific exclusions before aggregating coordinates. [Geography's isolated QA](data/cohort_repository_checks.json) verifies all 93 fixtures/54 help paths at that source pin; earlier 90/52 evidence is preserved.

The latest [dependency-scope QA](data/dependency_repository_checks.json) pins `b6ecc83`: 93 fixtures/all 54 help paths with only `data`, `analysis` and `quantum` groups, 37 installed distributions and unchanged retained package versions. Notebook and IBM tooling are now opt-in `notebook` / `hardware` groups; unused Aer/drawing extras are removed. This does not alter historical recipe locks or authorize hardware execution. The fresh copy contained no production inputs/credentials and was removed after checks; shared data/cache/environment metadata and protected final/source hashes are unchanged. Optional groups are not execution-tested by this receipt.

For an independent **ridge** replication, first build the exact training table above in a new copy; the final evaluator is unnecessary. Commit `9ede818` includes the unchanged opening recipes and the collector:

```sh
git switch --detach 9ede818
uv sync --locked --group data --group analysis --group quantum
uv run --no-sync python scripts/run_ridge_screen.py
uv run --no-sync python scripts/collect_ridge.py
```

Compare both seed groups and every declared gate with [ridge evidence](results/kernel-ridge.json), not only the best AP. This recipe uses no test years, pair circuits, shots or hardware. Collection reconstructs simulated states and checks coefficient equations without fitting. The original numerical checks passed; RBF still outperformed dense ZZ. The original SVM failures remain separate.

For the independent seasonal-control repair, use the same exact training-table copy, switch to `7f5edae`, sync its locked groups, then run `scripts/run_seasonal_baseline.py` followed by `scripts/collect_seasonal_baseline.py`. The twelve conditions reconstruct from saved coefficients and train-only statistics; the combined control must reproduce the original discovery AP within 1e-9. No quantum or test-year work occurs. [Evidence](results/seasonal-baseline.json) reports all groups, not a new final-model choice.

The convergence runner specifically requires the **original** ignored landmark outcome matching its committed evidence hash. A new landmark run changes timestamps and its outcome hash even when predictions agree, so it cannot silently replace that parent. Independent chain replication needs a separately frozen lineage receipt; the original diagnostic can instead be collected from its preserved parent. The library's two failed repair attempts are retained history, not additional replications.

[Expanded repository QA](data/expanded_repository_checks.json) pins **90 fixture tests and all 52 script help paths** to `9fa3127` in a fresh locked environment with no production inputs or credentials. All 1,736 production files and 28,417 shared-environment files retained their size/mtime; the task copy was removed. Temporary Git metadata was initialized before execution to support the reservation fixture. No source change or scientific run occurred. The earlier [84/49 at `a1893e2`](data/current_repository_checks.json) is preserved byte-for-byte, including its archive/Git-metadata setup repair. [74/40 at `8d6f72c`](data/constrained_repository_checks.json) and [61/30 at `3787725`](data/followup_repository_checks.json) remain separately pinned. These checks do not execute full follow-up replicas or certify historical predictor availability. Current preparation caches may have different identifiers; use the pinned recipes for exact table lineage.

## Independent policy-code evolution

The [policy study](POLICY_EVOLUTION.md) pins fresh development to `4cadf96` and reserved confirmation to `5906f4f`. Its collector checks saved trees, sampled labels, prediction metrics, recipe inheritance and shared execution without fitting. Both exclusive namespaces and the original flat replay remain intact. Separate replication requires the exact training cache and a new explicit selection freeze for its own development outcome; public summaries omit the ignored old replay history and per-example predictions. Do not reset original intents.

[Policy-source QA](data/policy_repository_checks.json) pins `9f5b268`, with 102 fixtures/all 55 help paths in a fresh normal-group environment. Its only later Python delta is the explicitly hashed proposal-model limitation string in the goal collector; no execution logic changes. Both disposable environments were removed after their terminal checks.

The final [policy release QA](data/policy_repository_checks.json) supersedes that check at `8d6b7e9`: 103 fixtures/all 55 help paths, current source bytes identical and the empty-outcome guard covered. The [102-fixture receipt](data/policy_initial_repository_checks.json) remains unchanged. Collection instructions now name original saved-run prerequisites and a separate output file.

## Current workflow front door

Use [the pipeline commands](PIPELINE.md) for acquisition through training features, optional bounded screening/summary and existing-result collection. `pipeline.py run` previews; `run --execute` acquires missing selected sources and passes the resulting dataset between preparation/join stages. With an explicit `--plan` and `--axis`, `run --execute` also fits the plan's training-only screen and saves a compact summary. This requires a separate replica with discovery open; the original final intent blocks it before preparation. `doctor --verify` distinguishes missing inputs, changed bytes and acquisition-receipt metadata. It preserves real metadata; identical table content can live in a new provenance namespace.

The committed `df99ef6` preparation reproduces training SHA-256 `b60618f65e1f8a71ddd9b8afe099efff49e4adf1d48acf2be6465b91207de8d8` under `historical-woodland/2fd3898f9d72da066223`; the original scored cache remains intact. A preliminary prepublication preparation is named separately in the [integration receipt](data/workflow_integration_checks.json), without relabelling its parent-commit metadata. Neither preparation is a model replication.

For saved evidence, `pipeline.py collect --output <new-directory>` runs the discovery/final/policy/goal collectors. The directory must be new, and original ignored run records are required. It does not refit or reopen the final test. [Current isolated QA](data/workflow_repository_checks.json) pins 115 fixtures/all 55 help paths at `8998e2a`, with unchanged normal dependency versions and all current code bytes matching. Earlier recipe commits and QA receipts remain valid for their own snapshots.

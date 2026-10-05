# Acquisition and coverage

**Acquisition is complete for the selected sources; annual modelling is not.** These files can support the restored macro objective, but no annual climate/fire modelling table or predictor was built. All 456 required weather files for 1987–2024 were rechecked against their hashes during the scope correction. [Status](SCOPE_CORRECTION.md).

Train **1988–2018 inclusive (31 calendar years)**; test **2019–2024**. The configuration is [ontario.json](../configs/wildfires/ontario.json). Fit preprocessing and select models using training data only; use chronological validation within training. The incident branch has already evaluated the final six years; disclose this exposure for any later overlapping macro test and freeze new choices on training years. Acquisition is separate from the measured local experiments in [FINDINGS.md](FINDINGS.md).

## Detailed fire records

```sh
uv run --no-sync python scripts/download_wildfires.py --output data/wildfires/ontario-new-snapshot
```

The WFS downloader preserves every operational update, with its fire ID, coordinates, cause, size, response, report date and validity interval. It downloads the full feed; the coverage audit restricts years to the configured split. Use a fresh snapshot directory; it refuses overwrite. The existing audited snapshot is `data/wildfires/ontario`.

**NFDB historical points are selected for incident labels; earlier operational update access remains unresolved.** The inspected Ontario snapshot contains status years from 2010 onward. Documented `/fire-list` queries for 1988 and 2009 return empty results, including mid-season, year-end, UTC and space-separated timestamps; a 2018 control succeeds. This is an endpoint/acquisition finding, not proof that historical fires or underlying agency records never existed. Retain the 1988 start date. Another agent verified [NFDB point records](https://cwfis.cfs.nrcan.gc.ca/downloads/nfdb/fire_pnt/current_version/NFDB_point_txt.zip) containing older coordinates/dates/cause/size, including Ontario 1988. The owner delegates source choice, and NFDB is now selected for the historical incident branch. It supplies agency-associated dates and reported sizes, with ambiguous identities/date disagreements and invalid date/location/size records excluded. It is distinct from the per-update feed. Do not label empty responses as no fires. Annual aggregation is required for the macro task; annual totals cannot reconstruct spatial incident records, and spatial records do not force an incident prediction task.

[API documentation](https://api.cwfif.nrcan.gc.ca/reported-fire-stats/docs) · [1988 detailed query](https://api.cwfif.nrcan.gc.ca/reported-fire-stats/fire-list?datetime=1988-12-31T23%3A59%3A59Z&agency_code=ON&paginate=true&size=1&include_prescribed=true) · [2018 control](https://api.cwfif.nrcan.gc.ca/reported-fire-stats/fire-list?datetime=2018-07-15T23%3A59%3A59Z&agency_code=ON&paginate=true&size=1)

The same API does provide historical Ontario aggregate totals, e.g. [1988: 3,241 fires, 394,597 ha](https://api.cwfif.nrcan.gc.ca/reported-fire-stats/ytd/by-agency?date=1988-12-31). Those were checked diagnostically and are not selected as replacement training inputs. This endpoint uses `date`; `/fire-list` uses `datetime`. Unknown query parameters can silently yield current data, so always check returned dates.

`/fire-list` returns the record valid at the requested time for each fire in that year. Daily calls can repeat the same entry. The WFS history provides update intervals, not a complete daily grid. Inspect reporting gaps and anomalous fire/status years before labelling; suspected 2013–2014 coverage issues remain open.

The historical branch can be reproduced with `uv run --no-sync python scripts/audit_nfdb.py`, then `scripts/build_historical_features.py --lags 1 2 3` after weather preparation. The audit retains the downloaded ZIP and source/hash evidence; derived features quarantine ambiguous identity groups.

## Monthly weather

```sh
uv run --no-sync python scripts/download_weather.py
```

All **444 Ontario monthly files for 1988–2024**, plus 12 months of 1987 lag context, are downloaded and cached with source URL, retrieval time, SHA-256 and station-row count. Re-running validates hashes and skips completed downloads. Failed and empty responses remain explicit. These are station-month files; station locations, missing observations and missing-day flags still need modelling QC. Monthly summaries cannot supply daily weather or weather known before that month ends. Raw `NA`, blanks and zeroes remain unchanged.

## Woodland

```sh
uv sync --locked --group data
# Default writes an acquisition plan only.
uv run --no-sync python scripts/download_woodland.py --bbox -95.2 41.6 -74.3 56.9
# Acquire native classes for one year, then retain only its regional crop.
uv run --no-sync python scripts/download_woodland.py --start-year 1988 --end-year 1988 --bbox -95.2 41.6 -74.3 56.9 --download
```

[The official catalogue](https://open.canada.ca/data/en/dataset/2785c103-9c2d-429b-9f3d-89f5cd9ea94d) lists annual national ZIPs for 1984–2022. The script processes one archive at a time, temporarily extracts its TIFF, crops on the original 30 m EPSG:3978 grid, preserves integer classes, saves a compressed regional GeoTIFF and removes temporary national files. It hashes source and crop, rejects RGB maps, unexpected class values and crops without classified pixels. The default archive transfer cap is 2.5 GiB; free-disk checks allow for the archive plus extracted TIFF.

Validated on the actual 1988 archive: 1432.4 MiB transferred, 297.4 MiB retained; one native uint8 band, EPSG:3978, 30 m grid. Hash-verified cache reuse and temporary-file cleanup passed. Acquisition is complete: **37 native regional crops**, 1984 and every year from 1987 through 2022, retaining **10.90 GiB**. The 1984 crop reuses the owner's original archive; no temporary national ZIP/TIFF remains in the repository data directory. [Per-year provenance and size totals](data/woodland_acquisition.json) and [coverage.csv](data/coverage.csv) distinguish the 35 matching-year requested maps from the 1987/1984 context maps. The frozen final model uses static 1984 context. Per-year sidecars, rather than a batch manifest, are authoritative for completed crops.

This saves retained disk, **not transfer volume**: a national ZIP is still downloaded for each requested year. The tested WMS TIFF is RGB and WCS is disabled; neither was adopted as raw categorical input. Use `--local-archive` for a previously downloaded ZIP with one matching year. The Ontario bounding rectangle includes neighbouring land and water; add a real study-area mask before aggregation.

**The 2022 cutoff is accepted.** The requested 2023–2024 test years have no matching-year map. A prior-year or fixed-2022 covariate must be labelled as such if later selected, never represented as a new annual map. Retrospectively classified woodland is not automatically known at prediction time; date all covariates and guard against disturbance leakage.

## Reproduce the year-level audit

```sh
uv run --no-sync python scripts/audit_data_coverage.py
uv sync --locked --group data --group analysis --group quantum
uv run --no-sync python -m unittest discover -s tests -v
```

[coverage.csv](data/coverage.csv) distinguishes local downloads from unresolved acquisition and product-year limits, links the sources, and lists fire updates, distinct IDs and report dates. NFDB incident rows are present in all 37 requested years; operational updates are present in 15 years. Blank operational cells mean unknown/missing snapshot coverage, independently of NFDB availability. They are not zero-fire labels. The clarified notes preserve every original coverage count. This audit does not certify that every incident/station observation is complete. Raw data and intermediate results remain ignored by Git.

For the frozen final replica, use the [selected input index](data/reproduction_inputs.json) and [pinned steps](REPRODUCIBILITY.md): 456 weather CSV/receipt pairs, NFDB ZIP and one 1984 crop/receipt. All listed source bytes were checked against the selected preparation parents. The public index contains hashes/URLs/receipt metadata only; mutable upstream URLs cannot guarantee the original snapshot. Additional annual maps and operational updates are not required for that recipe.

The [October 5 public-source spot-check](data/reproduction_source_check.json) independently refetched four fixed weather boundaries and the NFDB ZIP; all five match the original hashes. It downloaded about 24 MiB, preserving existing inputs. The 1984 national-map HEAD response matches the expected content length only; no national-map body or crop was recreated. This is a bounded availability observation, not a complete reacquisition or another predictive replication.

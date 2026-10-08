# Ontario fire sources

The current annual study aggregates NRCan National Fire Database (NFDB) records into one Ontario row per year: 1988–2018 training and 2019–2024 reused evaluation. The target is mean reported hectares per size-observed fire. See the [annual report](../../docs/REPORT.md), [source rules](../../docs/DATA_SCHEMA.md) and [reproduction instructions](../../docs/REPRODUCIBILITY.md).

The earlier individual-fire classifier is supporting historical work. Reported dates and sizes do not certify ignition dates or final burned area; missing records are not negative labels.

Agency Reported Wildfires is a separate operational feed with report-history updates. It is used for coverage diagnostics, not as the annual study’s historical incident source. The instructions below apply to that feed.

## Operational update feed

[Catalogue](https://cwfis.cfs.nrcan.gc.ca/en/catalogue/results/937eb7be-83fd-4b94-a122-9cc0385f3bf7) · [Statistics API documentation](https://api.cwfif.nrcan.gc.ca/reported-fire-stats/docs)

The raw source is the GeoServer WFS layer `public:cwfif_national_reportedfires`. The downloader filters `agency_code='ON'`, sorts by `id`, and retrieves every page (10,000 rows per request). Use a fresh output directory for each snapshot:

```sh
uv run --no-sync python scripts/download_wildfires.py --output data/wildfires/ontario-new-snapshot
```

Outputs: `reports.csv` and `metadata.json` with exact query URLs, timestamps, SHA-256 and annual coverage. Public incident/update identifiers are retained; no API key is needed. Files stay under ignored `data/`.

## Interpretation

- `national_fire_id` identifies a fire; `id` identifies a report-history row. Repeated fire IDs describe updates and must not become independent training examples split across train/test.
- `situation_report_date` is a report date; `record_start`/`record_end` describe history validity. A report may enter the feed later than its report date. Distinguish `fire_year` from `status_year`.
- Individual WFS update history starts in 2010 in our snapshot, with partial first-year ingestion; historical agency-level totals are available earlier through `/ytd/by-agency?date=YYYY-MM-DD`. Earlier **detailed-record acquisition remains unresolved**: empty `/fire-list` responses do not prove no fires or that older source data never existed. Annual totals are not the chosen replacement. The current year is incomplete. Fewer report dates do not by themselves establish missing daily observations.
- The earlier Ontario audit found suspicious 2013–2014 coverage differences versus NFDB. That comparison is a coverage warning, not an event-matched missing-fire count. NFDB supplies the separate historical incident branch; the two sources are not interchangeable.
- Response types describe full, modified or monitored management. Blank historical categories have no documented interpretation; retain them as unspecified.
- Missing feed records do not establish fire absence. Reporting frequency, agency practices and revisions can affect both labels and apparent changes in size.

WFS paging is not an atomic snapshot. The downloader rejects duplicate row IDs and changing schemas, but a concurrent update can still change coverage; metadata records the retrieval interval. For modelling, freeze a dated snapshot, audit coverage, and use time-aware splits and information-availability rules.

`/fire-list?datetime=...` returns each fire's entry valid at that requested time within the year, not every update on that date. Use the WFS history for update intervals; daily snapshots repeat still-valid entries. Neither grain is an independent daily ignition observation.

# Agency Reported Wildfires · Ontario

[Catalogue](https://cwfis.cfs.nrcan.gc.ca/en/catalogue/results/937eb7be-83fd-4b94-a122-9cc0385f3bf7) · [Statistics API documentation](https://api.cwfif.nrcan.gc.ca/reported-fire-stats/docs)

The raw source is the GeoServer WFS layer `public:cwfif_national_reportedfires`. The downloader filters `agency_code='ON'`, sorts by `id`, and retrieves every page (10,000 rows per request). Use a fresh output directory for each snapshot:

```sh
uv run python scripts/download_wildfires.py --output data/wildfires/ontario
```

Outputs: `reports.csv` and `metadata.json` with exact query URLs, timestamps, SHA-256 and annual coverage. Public incident/update identifiers are retained; no API key is needed. Files stay under ignored `data/`.

## Interpretation

- `national_fire_id` identifies a fire; `id` identifies a report-history row. Repeated fire IDs describe updates and must not become independent training examples split across train/test.
- `situation_report_date` is a report date; `record_start`/`record_end` describe history validity. A report may enter the feed later than its report date. Distinguish `fire_year` from `status_year`.
- History starts in 2010, with partial first-year ingestion; the current year is incomplete. Fewer report dates do not by themselves establish missing daily observations.
- The earlier Ontario audit found suspicious 2013–2014 coverage differences versus finalized CNFDB. That comparison is a coverage warning, not an event-matched missing-fire count. CNFDB is not an input to this project's current pipeline.
- Response types describe full, modified or monitored management. Blank historical categories have no documented interpretation; retain them as unspecified.
- Missing feed records do not establish fire absence. Reporting frequency, agency practices and revisions can affect both labels and apparent changes in size.

WFS paging is not an atomic snapshot. The downloader rejects duplicate row IDs and changing schemas, but a concurrent update can still change coverage; metadata records the retrieval interval. For modelling, freeze a dated snapshot, audit coverage, and use time-aware splits and information-availability rules.

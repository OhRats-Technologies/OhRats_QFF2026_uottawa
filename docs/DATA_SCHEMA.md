# Wildfire data schema and source mapping

Version 1 · 4 October 2026 · Ontario first. This is the integration design, not a claim that all tables or joins are implemented.

## Sources and observation units

| Source | One raw observation | Access and current status |
|---|---|---|
| [ECCC Monthly Climate Summaries](https://climate.weather.gc.ca/prods_servs/cdn_climate_summary_e.html) | Weather station × month | CSV/XML, by province and month. July 2025 Ontario CSV and legend inspected; bulk historical coverage not audited. |
| [NRCan annual forest land cover](https://open.canada.ca/data/en/dataset/2785c103-9c2d-429b-9f3d-89f5cd9ea94d) | 30 m raster cell × year | Annual GeoTIFFs, 1984–2022. Downloaded 1984 file inspected: one categorical band, EPSG:3978, nodata 255. |
| [Agency Reported Wildfires API](https://api.cwfif.nrcan.gc.ca/reported-fire-stats/docs) | Fire record valid at a requested time; summaries aggregate records | API field names differ from WFS. Full Ontario update history downloaded through WFS `public:cwfif_national_reportedfires`: 50,297 rows, 12,877 distinct fire IDs in the current snapshot. |

Keep raw files unchanged under ignored `data/`. Curated tables and training outputs also remain ignored. Commit schemas, import code, configurations and compact aggregate audits. Do not add CNFDB or other sources without an explicit scope change.

## Normalized tables

`PK` denotes primary key; `FK` denotes a reference to another table. Nullable values remain null rather than fabricated zeroes.

| Table | Key / grain | Fields |
|---|---|---|
| `source_snapshot` | PK `snapshot_id` (string) | `source_name`, `source_url`, `query_parameters` (JSON), `retrieval_started_utc`, `retrieval_finished_utc`, `sha256`, `relative_path`, `source_crs`, `schema_version`, `coverage_start`, `coverage_end`; publication/availability timestamp nullable and explicitly documented |
| `weather_station` | PK `(snapshot_id, climate_id)` | FK `snapshot_id`; string `climate_id`, `station_name`, `province`; float `longitude`, `latitude`; retain source CRS and coordinate provenance. Snapshot-keying preserves relocations/revisions. |
| `weather_month` | PK `(snapshot_id, climate_id, month)` | FK station; `month` (first day, date), nullable measurements and their missing-day counts below; `quality_flags` (string list) |
| `land_cover_asset` | PK `(snapshot_id, map_year)` | FK snapshot; integer `map_year`; raster path, EPSG:3978, affine transform, dimensions, 30 m resolution, band 1, class legend, nodata 255. Keep pixels in the raster, not billions of database rows. |
| `fire_update` | PK `(snapshot_id, update_id)` | FK snapshot; string `update_id`, `national_fire_id`, `agency_fire_id`, `agency_code`, `region_code`; dates, coordinates, status, cause, response and size below; raw codes plus normalized values and quality flags |
| `fire_identity` | PK `(agency_code, national_fire_id)` after collision audit | Identity only: source fire-year and agency identifiers. Locations can change between updates; do not silently pick final coordinates or final size as historical inputs. Conflicting identities are quarantined. |
| `feature_observation` | PK `observation_id` | Fire identity, `prediction_time`, fire-update/snapshot references; selected weather station/month/snapshot and distance; land-cover snapshot/year, buffer radius, class proportions, valid-area fraction; quality flags and split ID. Target, horizon and label provenance added only when the task is selected. |

## Weather CSV → normalized fields

The month comes from download parameters, not an explicit column in this CSV. Climate identifiers can contain letters; never convert them to integers.

| Raw CSV field | Normalized field | Unit / meaning |
|---|---|---|
| `Clim_ID`, `Stn_Name`, `Prov_or_Ter` | `climate_id`, `station_name`, `province` | Strings |
| `Long`, `Lat` | `longitude`, `latitude` | Degrees; confirm source datum before joining |
| `Tm`, `Tx`, `Tn` | `mean_temp_c`, `highest_max_temp_c`, `lowest_min_temp_c` | °C; `Tx`/`Tn` are monthly extremes |
| `DwTm`, `DwTx`, `DwTn` | `missing_mean_temp_days`, `missing_max_temp_days`, `missing_min_temp_days` | Days without valid observations |
| `P`, `DwP`, `Pd` | `total_precip_mm`, `missing_precip_days`, `precip_days_ge_1mm` | mm, days, days |
| `S`, `DwS`, `S_G` | `snowfall_cm`, `missing_snowfall_days`, `month_end_snow_cm` | cm, days, cm |
| `D`, `P%N`, `S%N` | `temp_anomaly_c`, `precip_percent_normal`, `snowfall_percent_normal` | Relative to 1981–2010 normals in the inspected legend |
| `BS`, `DwBS`, `BS%` | `sunshine_hours`, `missing_sunshine_days`, `sunshine_percent_normal` | Hours, days, percent |
| `HDD`, `CDD` | `heating_degree_days`, `cooling_degree_days` | Degree-days, base 18 °C |

[Inspected CSV](https://climate.weather.gc.ca/prods_servs/cdn_climate_summary_report_e.html?intYear=2025&intMonth=7&prov=ON&dataFormat=csv) · [Official field legend](https://climate.weather.gc.ca/prods_servs/cdn_climate_summary_report_e.html?intYear=2025&intMonth=7&prov=ON&dataFormat=txt)

Cleaning: preserve the original strings; normalize blank/`NA` to null, parse numerics, and keep missing-day counts alongside every measurement. Zero precipitation is not automatically missing. A value with many missing days is not equivalent to a complete monthly total. Check missing-day counts against month length; flag suspect values rather than silently replacing them. ECCC cautions that summaries receive basic checking and can be revised.

## Fire fields → normalized fields

| Raw WFS field | Statistics API field | Normalized field / rule |
|---|---|---|
| `id` | Not exposed in the inspected fire-list schema | `update_id` as string; unique within snapshot |
| `national_fire_id`, `agency_fire_id`, `agency_code`, `region_code` | Same names | Preserve strings; do not split identities by train/test row |
| `situation_report_date`, `status_date` | Same names | Preserve raw timestamps plus parsed time and known timezone; flag unknown timezone instead of assuming UTC |
| `record_start`, `record_end` | Same names | `valid_from`, `valid_to`; history validity, not ignition/extinguishment times or guaranteed API publication times |
| `fire_year`, `status_year` | Same names | Integers; retain separately |
| `latitude`, `longitude`, `geometry` | Latitude/longitude; geometry not in inspected fire-list schema | Coordinates plus declared CRS; cross-check geometry and attributes with explicit axis order |
| `fire_size` | `fire_size` | `reported_size_ha`, nullable nonnegative float; an update estimate, not necessarily final burned area |
| `stage_of_control_status` | `stage_of_control` | `control_status`; API enum: `out_of_control`, `being_held`, `under_control`, `extinguished`. Verify WFS code crosswalk before translating. |
| `response_type` | Same name | `response_type`; API enum: `full_response`, `modified_response`, `monitored_response`; preserve raw WFS values and unspecified blanks |
| `national_fire_cause` | Same name | API filter enum: `human`, `natural`, `undetermined`; verify WFS crosswalk |
| `fire_was_prescribed`, `fire_type_ics` | Same names | Preserve raw integer/code; validate meanings before deriving a boolean/filter |
| `percent_contained` | Not in inspected fire-list schema | Optional percentage; validate 0–100, retain null |
| `severity_nearest_dsr` | Same name | Preserve source value; it is not an independently joined monthly-weather feature |

Do not infer ignition from the first report. The API fire list and WFS history have different grains; aggregate API endpoints cannot substitute for individual updates. Preserve all distinct update IDs, audit conflicting/repeated rows, and do not sum repeated size estimates into total area burned. Unknown enum values are retained and flagged, never silently mapped to a valid class.

## Woodland raster → features

The inspected ZIP legend defines: `0` unclassified; `20` water; `31` snow/ice; `32` rock/rubble; `33` exposed/barren; `40` bryoids; `50` shrubs; `80` wetland; `81` treed wetland; `100` herbs; `210` coniferous; `220` broadleaf; `230` mixedwood. `255` is raster nodata. Codes are categories, not tree density or biomass. There is no dedicated urban class in this legend.

For a configured buffer around a location, derive `cover_fraction_<class>` = area mapped to that class / valid classified area. Include water in that denominator; exclude `0` and `255` and report their fraction separately. Fractions sum to one when classified area exists; otherwise return null. Record `map_year`, buffer radius, CRS, pixel inclusion/edge rule and valid-area fraction. Use equal-area or area-weighted calculations for provincial totals; 900 m² is projected pixel area, not an exact ground-area guarantee in Lambert Conformal Conic.

## Spatial and temporal joins

1. Select the latest fire update available at `prediction_time`, retaining its recorded coordinate and quality flags. Reconstructed availability from `record_start` is an assumption to audit, not an established publication timestamp.
2. Choose a weather station with adequate observations in the eligible month. Compute geodesic distance, save the station ID and distance, and set a maximum-distance/quality threshold in configuration before evaluation. Keep unmatched observations explicitly missing. Do not join by province alone or station name.
3. For forecasting, use only completed weather months published before prediction time. Same-month final summaries belong to retrospective description, not within-month prediction. This source does not provide daily wind, humidity or fire-weather conditions; do not invent those by repeating/interpolating monthly values.
4. Transform fire locations into EPSG:3978 for raster sampling. Use longitude/latitude order explicitly and check transformations against a second reference. Flag water/out-of-coverage locations; do not snap fires to land automatically. A 1984 CNFDB demonstration exposed this problem, but CNFDB remains outside the modelling inputs.
5. Select a pre-fire land-cover year under a documented lag/availability policy. Annual maps are retrospective, disturbance-informed and temporally smoothed; an earlier map year alone does not guarantee freedom from future information. State this limitation in any prediction claim.
6. Join features using their observation keys and snapshot IDs. Preserve unmatched records and reasons. Current overlap with annual cover ends in 2022; never silently carry the 2022 map into 2023–2026 or use the single 1984 file for modern fires.

## Quality gates before training

- Preserve raw snapshots, exact URLs, hashes, retrieval interval and schema version; freeze inputs used in a run.
- Audit annual/monthly fire coverage and per-fire update intervals, including suspected Ontario 2013–2014 gaps. Dates without updates are not guaranteed no-fire observations.
- Check identity uniqueness, coordinate ranges/CRS, missingness, timestamp ordering and field/crosswalk validity. Flag size decreases as possible revisions, not automatically corrupted data.
- Require explicit station-distance and weather-completeness policies, raster coverage thresholds and temporal-availability checks. Report excluded/unmatched counts by year and reason.
- Split chronologically and avoid the same fire leaking across train/test; add spatial holdouts where appropriate. Fit imputation/scaling on training data only.
- Select the prediction target/horizon and label rules separately. These three sources do not automatically establish true ignition dates or reliable negative examples.

Suggested layout: `data/raw/{weather,woodland,fires}/`, `data/curated/`, `configs/wildfires/`, and `results/wildfires/`. The existing fire downloader currently writes `data/wildfires/ontario/`; reference that snapshot until an explicit migration is implemented. No data was moved or cleaned by creating this document.

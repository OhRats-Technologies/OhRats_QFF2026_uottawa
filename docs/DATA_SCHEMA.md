# Wildfire data schema and source mapping

The earlier scope assessment below describes the 1 PM run. The owner authorized a new annual study through 5 PM; [current annual implementation and measured progress](ANNUAL_QSVR.md) supersede its unrun status as milestones finish.

Version 5 · 5 October 2026 · Ontario first. Annual climate/fire aggregation is implemented in `wildfire_lab/annual_data.py`, with [31-row training data](data/annual_training.csv) and [measured regressions](ANNUAL_QSVR.md). The existing pipeline implements station-month CSVs and a supporting NFDB incident-classification CSV with hash-linked manifests. The relational design below also describes future update/availability tables; those are not all materialized.

## Sources and observation units

| Source | One raw observation | Access and current status |
|---|---|---|
| [NRCan NFDB historical points](https://cwfis.cfs.nrcan.gc.ca/downloads/nfdb/fire_pnt/current_version/NFDB_point_txt.zip) | Agency-associated incident point with date and reported size | Selected historical label source, snapshot 20260811. Date/size/identity eligibility is audited before joining; not a daily status history or complete census. |
| [ECCC Monthly Climate Summaries](https://climate.weather.gc.ca/prods_servs/cdn_climate_summary_e.html) | Weather station × month | CSV/XML, by province and month. All 444 requested Ontario months (1988–2024) downloaded; station/measurement completeness still requires QC. |
| [NRCan annual forest land cover](https://open.canada.ca/data/en/dataset/2785c103-9c2d-429b-9f3d-89f5cd9ea94d) | 30 m raster cell × year | Annual GeoTIFFs, 1984–2022. Downloaded 1984 file inspected: one categorical band, EPSG:3978, nodata 255. |
| [Agency Reported Wildfires API](https://api.cwfif.nrcan.gc.ca/reported-fire-stats/docs) | Fire record valid at a requested time; summaries aggregate records | API field names differ from WFS. Full Ontario update history downloaded through WFS `public:cwfif_national_reportedfires`: 50,297 rows, 12,877 distinct fire IDs in the current snapshot. |

Training: **1988–2018 inclusive (31 calendar years)**. Testing: **2019–2024**. Woodland cutoff **2022** is accepted. Historical fire aggregates exist before 2010. Incident/per-date records support source auditing and annual aggregation; they do not require an incident-level prediction target. Audited NFDB points are selected for historical incident labels; operational update history remains unresolved before 2010. Missing incident records are not evidence of zero fires. See [coverage and acquisition](DATA_DOWNLOADS.md).

Keep raw files unchanged under ignored `data/`. Curated tables and training outputs also remain ignored. Commit schemas, import code, configurations and compact aggregate audits. The owner delegated historical source choice; NRCan NFDB points are now selected. Other source additions require an explicit scope decision.

## Annual modelling contract · climate/fire implemented

One modelling row is **Ontario × year**, giving 31 training and six reused test-year rows. Defined regions are a separate optional design, not additional independent years. The frozen primary outcome is annual mean reported size over size-observed incidents. Same-year climate gives retrospective annual estimation; prior-year context is an explicit sensitivity. The annual CSV retains counts, exclusions, total size, ten climate predictors and eligible station counts. Provincial woodland aggregation is the remaining optional preparation stage.

| Field group | Required meaning |
|---|---|
| Identity/provenance | Province, year, source snapshot hashes, aggregation recipe, split and coverage flags |
| Fire outcomes | Distinct recorded incident count, size-observed count, total observed reported hectares and mean over size-observed incidents; preserve unknowns and denominators |
| Climate predictors | Station/month temperature and precipitation summaries with declared station weighting, observation counts and missing-day coverage; no incident-frequency weighting |
| Woodland predictors | Declared area-weighted class fractions and map year; explicit policy for the 2022 cutoff and retrospective processing |
| Timing | Predictor availability/horizon; same-year full climate summaries imply retrospective analysis, not an advance annual forecast |

Build annual labels from audited source incidents under macro-specific rules. Coordinate, weather-distance and buffer filters needed by incident joins must not silently remove fire contributions from province totals. Missing size is not zero size; missing reporting is not zero activity. Preserve prescribed-fire/identity policies with explicit annual denominators. [Scope correction](SCOPE_CORRECTION.md) · [required experiment](EXPERIMENTS.md).

## Implemented supporting incident branch

The [NFDB reader](../wildfire_lab/nfdb.py) creates eligible incident dictionaries in memory. [Weather joining](../wildfire_lab/feature_joins.py) and [woodland joining](../scripts/add_woodland_features.py) write versioned `features.csv` / `manifest.json` pairs. There is no separate persisted incident database or per-row `prediction_time` / publication timestamp in this branch. Raw sizes, causes and prescribed codes remain recoverable from the source archive, not predictor columns.

| NFDB field | Typed incident field / eligibility |
|---|---|
| `SRC_AGENCY` | Select the string `ON`; agency is recorded in source/policy context, not repeated in the feature CSV. |
| `NFDBFIREID` | `incident_id`, string. Quarantine every ID repeated anywhere in the Ontario source snapshot, including outside the requested window. |
| `YEAR`, `MONTH`, `DAY`, `REP_DATE` | `year`, integer; `date`, valid ISO calendar-date string assembled from the first three fields. A nonblank `REP_DATE` must have the same first ten characters. This does not establish ignition date. |
| `LATITUDE`, `LONGITUDE` | Finite float degrees in latitude/longitude range; blank, invalid and `-999` values fail eligibility. Source attribute datum remains unspecified. |
| `SIZE_HA` | Finite nonnegative reported hectares. `target`, integer 0/1, is one at size ≥10 ha. Five eligible training sizes of zero are retained; their real-world meaning is unresolved. |
| `PRESCRIBED`, `FIRE_TYPE` | Exclude any nonblank prescribed code or `FIRE_TYPE=PB`. Blank flags remain unspecified; exclusion is not proof that every retained incident is nonprescribed. |

The saved training and test feature tables each contain **38 columns**; the [frozen final plan](../experiments/final_evaluation.json) pins their lineage and model inputs. Their logical types and meanings are:

| Stored fields | Type / meaning |
|---|---|
| `incident_id`, `date`, `year`, `latitude`, `longitude`, `target` | Incident identity, agency-associated date, year, reported coordinate and binary label as above. ID is unique within each retained snapshot; preserve it as a string when loading. |
| `month_sin`, `month_cos` | Floats: sine/cosine of `2π × month / 12`, derived from the agency-associated date. |
| `lag{1,2,3}_{mean_temp_c,total_precip_mm,snowfall_cm,heating_degree_days,cooling_degree_days}` | Fifteen nullable float measurements from antecedent calendar months. Empty CSV values mean missing, not zero. |
| `station_lag{1,2,3}`, `weather_distance_lag{1,2,3}` | Three string climate IDs and three float distances in km. Each lag chooses its own nearest station with coordinates; missing measurements do not disqualify that station. All lags must have a station within 150 km. |
| `cover_conifer`, `cover_broadleaf`, `cover_mixed`, `cover_water` | Four float fractions of classified pixels in the configured 1 km disk. Other classes remain in the denominator, so these four fractions need not sum to one. |
| `cover_valid_fraction` | Float fraction of disk pixels classified (excluding 0/255); retain only at least .5. This is coverage, not positional accuracy. |
| `cover_center_class`, `cover_center_water` | Integer mapped category and integer 0/1 water flag at the reported coordinate; water is not automatically excluded or snapped to land. |
| `cover_year`, `cover_age_years` | Integers: fixed 1984 map year and incident year minus map year. They do not establish map publication availability. |

Eight columns are final candidate predictors: latitude, longitude, month sine/cosine and the four cover fractions. The final models do **not** use weather measurements, station identifiers, coverage diagnostics, incident IDs or labels as inputs. Weather matching still selects the cohort; removing its predictors does not remove its eligibility effect. Train-only imputation/scaling belongs to each model recipe, not source preparation.

Snapshot-wide provenance lives in manifests: source URL/SHA-256, weather fingerprint, parent feature fingerprint, woodland crop/archive hashes and policy, recipe hashes/commits, table hash, exclusions and annual retained counts. Station/month linkage is reconstructed from each row's date, configured lags and climate IDs; publication times are unresolved. The selected training CSV has 37,801 rows; the separately frozen test CSV has 3,820. [Pinned paths and hashes](REPRODUCIBILITY.md) identify both tables. This mapping documents saved artifacts without changing them.

## Relational design and operational branch

`PK` denotes primary key; `FK` denotes a reference to another table. These are logical target relations, not a claim that every named table exists as a database. Snapshot provenance is currently manifest-level, weather stations are repeated in the station-month CSV, and operational records remain their separate raw snapshot. Nullable values remain null rather than fabricated zeroes.

| Table | Key / grain | Fields |
|---|---|---|
| `source_snapshot` | PK `snapshot_id` (string) | `source_name`, `source_url`, `query_parameters` (JSON), `retrieval_started_utc`, `retrieval_finished_utc`, `sha256`, `relative_path`, `source_crs`, `schema_version`, `coverage_start`, `coverage_end`; publication/availability timestamp nullable and explicitly documented |
| `weather_station` | PK `(snapshot_id, climate_id)` | FK `snapshot_id`; string `climate_id`, `station_name`, `province`; float `longitude`, `latitude`; retain source CRS and coordinate provenance. Snapshot-keying preserves relocations/revisions. |
| `weather_month` | PK `(snapshot_id, climate_id, month)` | FK station; `month` (first day, date), nullable measurements and their missing-day counts below; `quality_flags` (string list) |
| `land_cover_asset` | PK `(snapshot_id, map_year)` | FK snapshot; integer `map_year`; raster path, EPSG:3978, affine transform, dimensions, 30 m resolution, band 1, class legend, nodata 255. Keep pixels in the raster, not billions of database rows. |
| `fire_incident` | PK `(snapshot_id, agency_code, incident_id)` | Logical NFDB incident relation: source ID, raw date/size/cause/prescribed fields and eligibility reasons; the implemented accepted fields are mapped above. Separate from operational update IDs; no inferred cross-source identity equivalence. |
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

For a configured buffer around a location, derive `cover_fraction_<class>` = area mapped to that class / valid classified area. Include water in that denominator; exclude `0` and `255` and report their fraction separately. The complete class vector sums to one when classified area exists; otherwise return null. The current model stores only conifer/broadleaf/mixed/water fractions, so their sum can be below one; other classes remain in the raster. Record `map_year`, buffer radius, CRS, pixel inclusion/edge rule and valid-area fraction. Use equal-area or area-weighted calculations for provincial totals; 900 m² is projected pixel area, not an exact ground-area guarantee in Lambert Conformal Conic.

## Spatial and temporal join policy

The selected NFDB branch uses its incident date, antecedent station-month matching and explicitly static cover as mapped above. Rules about latest available operational updates and `prediction_time` describe a future forecasting branch, not implemented as-of evidence for the current retrospective classification.

1. Select the latest fire update available at `prediction_time`, retaining its recorded coordinate and quality flags. Reconstructed availability from `record_start` is an assumption to audit, not an established publication timestamp.
2. Choose a weather station with adequate observations in the eligible month. Compute geodesic distance, save the station ID and distance, and set a maximum-distance/quality threshold in configuration before evaluation. Keep unmatched observations explicitly missing. Do not join by province alone or station name.
3. For forecasting, use only completed weather months published before prediction time. Same-month final summaries belong to retrospective description, not within-month prediction. This source does not provide daily wind, humidity or fire-weather conditions; do not invent those by repeating/interpolating monthly values.
4. Transform fire locations into EPSG:3978 for raster sampling. Use longitude/latitude order explicitly and check transformations against a second reference. Flag water/out-of-coverage locations; do not snap fires to land automatically. A 1984 NFDB demonstration exposed this problem; historical points now enter modelling only after explicit date/size/identity audits.
5. Select a pre-fire land-cover year under a documented lag/availability policy. Annual maps are retrospective, disturbance-informed and temporally smoothed; an earlier map year alone does not guarantee freedom from future information. State this limitation in any prediction claim.
6. Join features using their observation keys and snapshot IDs. Preserve unmatched records and reasons. Current overlap with annual cover ends in 2022; never silently carry the 2022 map into 2023–2026 or present a fixed 1984 context as event-year vegetation. The current explicitly labelled static 1984 branch tests geographic cover context across all eligible years, with no annual-vegetation or deployment-availability claim.

## Quality gates before training

- Preserve raw snapshots, exact URLs, hashes, retrieval interval and schema version; freeze inputs used in a run.
- Audit annual/monthly fire coverage and per-fire update intervals, including suspected Ontario 2013–2014 gaps. Dates without updates are not guaranteed no-fire observations.
- Check identity uniqueness, coordinate ranges/CRS, missingness, timestamp ordering and field/crosswalk validity. Flag size decreases as possible revisions, not automatically corrupted data.
- Require explicit station-distance and weather-completeness policies, raster coverage thresholds and temporal-availability checks. Report excluded/unmatched counts by year and reason.
- Split chronologically and avoid the same fire leaking across train/test; add spatial holdouts where appropriate. Fit imputation/scaling on training data only.
- Select the prediction target/horizon and label rules separately. These three sources do not automatically establish true ignition dates or reliable negative examples.

Implemented layout: `data/raw/{weather,woodland,nfdb-audit}/`, `.cache/wildfire/{processed,features,experiments}/`, and `configs/wildfires/`. The existing fire downloader currently writes `data/wildfires/ontario/`; reference that snapshot until an explicit migration is implemented. Preserve private hardware records under ignored `results/` independently.

Current feature-join quality is quantified in [feature_quality.json](data/feature_quality.json): source measurement missingness, nonzero/unknown missing-day counts, station-distance quantiles and woodland center/coverage codes. These counts are incident-weighted, because many fires can share a station-month. The current nearest-station rule does not require complete measurements; train-only imputation handles missing inputs. Absence of preparation flags does not certify complete monthly observations. Quality-filtered experiments require a new frozen policy and same-row controls.

The [label-quality audit](LABEL_QUALITY.md) verifies the frozen training target against source sizes and traces class-dependent cohort retention. Weather matching removes proportionally more ≥10 ha incidents; the cohort is selected rather than a representative sample of all Ontario fires. Exact boundary values and numeric multiples are descriptive, not measured label error or an alternative target.

The [source-method audit](SOURCE_ASSUMPTIONS.md) confirms forward–backward processing of the forest maps. Static/prior-year map choice does not establish historical information availability; frame the measured cover gain as retrospective association.

# Source assumptions and forecasting boundary

These source limits apply to the intended annual study as well as the incident branch. They do not make the unrun macro objective complete or require deferring a simple retrospective annual baseline. [Scope correction](SCOPE_CORRECTION.md).

Checked 5 October 2026. This review qualifies the frozen results; it changes no inputs, predictions or model choices.

## Forest context

The [NRCan catalogue](https://open.canada.ca/data/en/dataset/2785c103-9c2d-429b-9f3d-89f5cd9ea94d) describes disturbance-informed temporal post-processing. The cited [2018 methods, section 2.5.1](https://www.tandfonline.com/doi/abs/10.1080/07038992.2018.1437719) use a forward–backward Hidden Markov Model: class probabilities depend on preceding and following states. A [2025 study using the 1984–2022 VLCE maps](https://academic.oup.com/forestry/article/98/5/786/8104860) also describes this processing.

**Inference:** selecting the previous-year map, or fixing the map to 1984, does not remove later-information dependence from its construction. The exact effect on our sampled pixels is unmeasured. Chronological label splits cannot make a retrospectively constructed covariate historically available. The cover gain therefore measures retrospective association; it does not validate deployable wildfire forecasting. The geography-only control remains useful, but agency dates, coordinates and reporting completeness also constrain its interpretation.

A future forecasting study needs versioned, as-of imagery/features or an explicitly causal reconstruction. That is outside this frozen evaluation. No test-driven replacement map or model is introduced.

## Historical fire definitions

The [NFDB point metadata](https://cwfis.cfs.nrcan.gc.ca/downloads/nfdb/fire_pnt/current_version/NFDB_point_shapefile_metadata.pdf), rendered from the retained PDF, gives these definitions:

| Pages | Definition | Consequence |
| --- | --- | --- |
| 1, 3 | Locations are approximate; completeness varies across agencies/years. Ontario's 1959–1975 subset is incomplete and contains only fires above 200 ha. | Our 1988–2024 window avoids that stated early cutoff; it is not certified complete. |
| 19 | `NFDBFIREID` combines agency, year and agency fire ID. | Collision quarantine remains necessary. |
| 20–22 | Dates are agency-associated; `SIZE_HA` is size reported by the agency. | No guaranteed ignition timestamp or final burned area. |
| 23 | `PRESCRIBED`: 0 not prescribed; 1–4 describe prescribed-burn categories. | Blank is unspecified. The frozen rule excludes any nonblank value or prescribed cause. |
| 24 | `RESPONSE` includes FUL, MOD and MON; agencies may use additional values. | Preserve raw codes; do not infer meaning from blanks. |

The inspected Ontario text snapshot uses blank/`PB`, rather than the numbered prescribed domain: training has 40,339 blanks and 60 `PB` rows; test has 3,847 blanks and 15 `PB` rows. **No explicit zero was removed.** This is a snapshot-specific observation, not a general crosswalk for all agencies. Collision/date exclusions overlap with these rows. The metadata PDF SHA-256 is `db6eb48a39fca59015eac75032fec1cda8ae28e1c5b23e65756e491821eacbb9`; raw files remain unchanged.

## Coordinate reference and precision

The retained NFDB PDF specifies NAD83 Canada Atlas Lambert, EPSG:3978, for stored geometry on page 4; page 21 defines latitude/longitude as agency-supplied attributes without an explicit datum. The archive XML agrees (SHA-256 `6b34e0c01eb660776263a5fd7f179bb300935a18304d0b12acd0658d0377d2a9`). Our inherited CSV join interprets those attributes as EPSG:4326. A [training-only sensitivity audit](data/coordinate_quality.json) also transforms them from NAD83/EPSG:4269 to EPSG:3978: all 37,801 projected differences are zero under Rasterio 1.5.2/GDAL 3.12.2. This checks the installed transformation operations, not universal datum equivalence or positional accuracy. Frozen coordinates, features and results remain unchanged.

Exact repetition and decimal-grid alignment are numeric diagnostics. They cannot establish the original location precision, justify removing distinct incidents or certify that mapped-water centers are mistaken. Ordinary validation fires are usually near training records; the [geometry audit](FINDINGS.md#coordinate-quality-and-geographic-novelty) keeps that interpolation question separate from source accuracy and model causality.

## Monthly weather

ECCC's [monthly summaries and legend](https://climate.weather.gc.ca/prods_servs/cdn_climate_summary_e.html) describe station-month observations. Our lags avoid using the completed incident month's summary, but historical publication latency is unresolved. Missing-day counts and station distances are retained; imputation does not certify measurement completeness. Current weather predictors were pruned, although weather matching still determines the eligible cohort.

Use the [final report](FINAL_EVALUATION.md) for measured scores and the [schema](DATA_SCHEMA.md) for join rules. Neither this audit nor metric recomputation establishes causal effects, source completeness or operational validity.

# Annual data review

**The published annual fire arithmetic is correct for the pinned NFDB snapshot and frozen exclusions.** An independent raw-CSV reader reproduced all seven audited fields across 37 years (1988–2024), including every displayed mean. It does not establish that every agency record is accurate or that this is a complete census. No model was refitted.

## What the orange value means

$$\text{mean hectares per fire}=\frac{\text{sum of recorded fire sizes in hectares}}{\text{number of fires with observed sizes}}.$$

Thus 503 in 2019 is **503 hectares burned per recorded fire on average**, not the total hectares burned across Ontario, and not the size of a typical individual fire. The mean is sensitive to rare giant fires.

| Year | Recorded fires used | Recorded total ha | Mean ha/fire | Median fire ha | Largest five share of total |
|---|---:|---:|---:|---:|---:|
| 2018 | 1,320 | 265,459.40 | 201.11 | 0.30 | 42.8% |
| 2019 | 536 | 269,633.90 | 503.05 | 0.20 | 83.6% |
| 2020 | 605 | 15,436.40 | 25.51 | 0.30 | 69.6% |
| 2021 | 1,194 | 784,447.00 | 656.99 | 0.30 | 60.8% |
| 2022 | 274 | 2,560.10 | 9.34 | 0.10 | 80.2% |
| 2023 | 738 | 441,471.50 | 598.20 | 0.30 | 51.5% |
| 2024 | 481 | 89,812.70 | 186.72 | 0.40 | 60.9% |

In 2021, 784,447.00 ÷ 1,194 = 656.99 ha/fire, while the median is 0.30 ha. In 2022, 2,560.10 ÷ 274 = 9.34 ha/fire. The contrast comes from recorded burned area and its heavy tail, not a hectares/acres conversion or a mean/total mix-up.

## Independent source check

The [CIFFC 2020 Canada Report, pages 5–6](https://ciffc.ca/sites/default/files/2021-02/Canada_Report_2020_Final.pdf) reports 2019 at 537 fires / 269,635 hectares and 2020 at 608 / 15,460 hectares. Its total-area contrast agrees closely with the frozen snapshot; counts and totals are not bit-identical. The [Ontario 2023–2024 annual report](https://www.ontario.ca/page/published-plans-and-annual-reports-2023-2024-ministry-natural-resources) reports 2022 at 275 fires / 2,560 hectares and 2021 at 1,198 / 784,465. That page was available through indexed official text; direct retrieval returned 403. These corroborate the large swings, not exact equivalence of record populations.

Our raw Ontario row counts are 538 / 609 / 1,200 / 276 for 2019–2022. The frozen policy quarantines every blank or globally repeated Ontario NFDBFIREID; it does not merge duplicates or choose a preferred record. It removes 2 / 4 / 6 / 2 rows in those years. No coordinate, daily-date or nearest-weather filter removes fires from the annual target. Explicit prescribed-burn codes are excluded. Unknown/negative size is not treated as zero; none occur in the six accepted evaluation-year populations. Identity exclusions explain part of the population difference, but do not establish why agency summaries and the later snapshot differ.

The [raw source archive](https://cwfis.cfs.nrcan.gc.ca/downloads/nfdb/fire_pnt/current_version/NFDB_point_txt.zip) is pinned by SHA-256; its member is NFDB_point_20260811.txt. Input fields are YEAR, SRC_AGENCY, SIZE_HA, NFDBFIREID and prescribed-fire indicators. Source reporting, revisions and quarantine losses remain limitations; frozen model labels were not changed.

## Did the models fit 2018?

| Four-input model | Held-out 2018 prediction | Final in-sample 2018 prediction |
|---|---:|---:|
| RBF-SVR | 104.85 | 106.60 |
| QSVR | 31.40 | 106.64 |

**Recorded 2018 mean: 201.11 ha/fire.** The last development fold trains through 2014 and holds out 2015–2018; therefore 2018 was not fitted in that development comparison. Final training includes all 31 years through 2018. The in-sample column reconstructs stored dual coefficients against stored training Gram matrices; it is not a new fit, quantum execution or validation result. Development and final recipes were selected separately, so these are not a paired same-model generalization test.

Training does not require exact interpolation. Final SVRs use epsilon = 0.5 on training-standardized log1p outcomes; that error tube permits sizeable deviations in hectares. The saved final models predict about 106.6 on 2018 even though it is in training. This supports an underfitting/target-loss concern; it does not identify the sole cause of later-year failure. A raw-versus-log target experiment remains unrun future work.

## Reproduce this audit

Download the pinned source through the [documented acquisition path](DATA_DOWNLOADS.md), then use a new output path:

```sh
uv run --no-sync python scripts/audit_annual_source.py --output .cache/wildfire/annual-source-review.json
```

The [audit script](../scripts/audit_annual_source.py) reads raw CSV independently of annual_data.py/nfdb.py. It checks counts/sums/means against both annual tables and verifies saved training matrix hashes before computing two in-sample predictions. [37-year receipt](data/annual_source_review.json). Fire-target arithmetic is audited here; station measurement quality and geographic completeness are not independently certified by this check. Old results and source bytes remain unchanged.

## Ontario map display correction

The original presentation painted woodland codes **0/255** the background colour and oversized the opening map. That obscured southern Ontario; it did not reflect the province boundary or demonstrate missing cities. The corrected shared assets draw the full official 2021 Ontario boundary independently of woodland classes, use grey for **no mapped woodland class**, and mark Toronto/GTA, Ottawa, Windsor and Thunder Bay. Grey does not mean no vegetation. The official provincial boundary includes water and is not a land-only shoreline.

All four WGS84 city controls transform into EPSG:3978 inside the official boundary and raster crop. Forward/inverse errors are below 1e-9 degrees. Toronto, Ottawa and Windsor sample source class 0; Thunder Bay samples class 33. This checks display alignment, not every fire's recorded position. [Map receipt](../web/presentation/assets/map.json) records coordinates, classes, boundary bounds and unchanged source hashes. No dataset, fitted model, annual target or scientific result changed.

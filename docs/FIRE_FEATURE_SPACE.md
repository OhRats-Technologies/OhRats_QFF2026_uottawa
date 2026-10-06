# Ontario wildfire feature-space audit

The complete search was screened on October 6, 2026: **46 pages, 455 unique records**, exactly matching the official search export. Three additional owner-linked products bring the detailed metadata inventory to 458. Every search-result summary was read; selected catalogue descriptions and resource documentation were examined in depth. This is a metadata/access audit, not a validation of every downloadable raster.

- [Page-by-page screening](data/FIRE_CATALOGUE_PAGES.md) lists every record and its decision.
- [Observed pagination receipt](data/fire_catalogue_pages.json) preserves ordered IDs, URLs and exact membership checks.
- [Sanitized structured inventory](data/fire_catalogue_inventory.json) records dates, formats, footprints, licences, resource URLs and metadata hashes.
- Query: [Open Canada `fire`, newest first](https://search.open.canada.ca/data/?sort=metadata_modified+desc&search_text=fire).

The export SHA-256 is `9316489cde395b7f1d23fae5163e5f4f0f114599af42a041e4ff334a3710339d`. Its 406 rows with extra unlabelled trailing CSV fields make those fields unreliable. Only its stable ID column is used for reconciliation. All 458 official CKAN `package_show` requests succeeded; exact raw responses and per-request receipts remain in ignored `.cache/catalogue/20261006/`. Published inventory excludes contact emails and wrapped Outlook tracking links. Titles support transparent triage, with manually reviewed overrides; category counts are screening counts, not counts of independent usable datasets.

## What the search actually contains

| Feature family | Search records | Meaning for this project |
| --- | ---: | --- |
| Fire labels / regimes | 56 | Points, perimeters, annual counts, burned area and fire-cycle summaries; different observation units must remain separate. |
| Forest structure | 24 | Height, crown closure, biomass, volume and species. Useful structural context; most older products are static snapshots. |
| Fuel / vegetation | 29 | Fuel categories, forest maps, potential-spread classes, crop/water/peatland context. Geographic and temporal compatibility varies. |
| Weather / smoke | 41 | Observations, danger ratings, remote imagery and air quality. Smoke can be an outcome, rather than a pre-fire predictor. |
| Recovery / disturbance / carbon | 107 | Post-event history and ecological effects. Same-event predictors would leak outcomes. |
| Management / response / boundaries | 28 | Response zones, bases, restrictions, weather sectors and infrastructure. Policy is not natural hazard. |
| Future climate scenarios | 22 | Modelled ensembles and RCP projections; not observed yearly climate. |
| Urban response | 34 | Hydrants, structural incidents and casualties; a different task from wildland fire. |
| Ecosystem / terrain / imagery context | 13 | Small studies or ancillary maps; footprint and role require case-by-case review. |
| Keyword collisions / non-feature documents | 101 | Fire assays, Fire Lake geology, Ring of Fire, traffic lights, news, investigations and administration. Excluded from predictor acquisition. |

Repeated titles and versions are not independent evidence. For example, legacy atlas severity/hotspot maps occur under different IDs, SCANFI v1/v2 overlap, and raw/validated air-quality records describe related series. Their IDs remain distinct in the receipt; a model must not count them as independent samples.

## The seven owner-linked sources

| Product | What is measured | Coverage / date | Decision |
| --- | --- | --- | --- |
| [Forest Elevation(Ht) Mean](https://open.canada.ca/data/en/dataset/7cbdfae1-f724-4679-8f0f-1c611f17186f) | Mean lidar first-return height above ground, **metres of canopy height**, not terrain elevation | Canada's forested ecosystems, 30 m; title and structured dates say 2015 | Ontario context candidate. Description also says 1985–2011, an unresolved metadata inconsistency. Do not manufacture an annual series. |
| [Lorey's Height](https://open.canada.ca/data/en/dataset/836082d5-d55f-46c3-9b9c-aaf1a306c247) | Tree height weighted by basal area, metres | National forested ecosystems, 30 m; 2015 title/date with the same 1985–2011 description inconsistency | Related to canopy height, not an independent tree-density measurement. Avoid both by default if they add redundancy. |
| [Post-disturbance recovery](https://open.canada.ca/data/en/dataset/a6b81e8b-d429-4629-9121-5a56786fcb83) | Years to reach **80% of pre-disturbance spectral value**, plus faster/slower recovery relative to ecozone baseline | Observation 1985–2017; disturbances 1986–2012; ~650 million ha of forested ecosystems | Landscape-recovery context. Spectral recovery is not full ecological restoration. Unrecovered pixels at 2017 are censored, not zero years. Do not feed the same disturbance's eventual recovery into its prediction. |
| [Canada Forest Water](https://open.canada.ca/data/en/dataset/0bce352f-6f3f-4a30-9763-c80805fcf272) | Water class extracted from VLCE annual land cover | National forested ecosystems, 2022, 30 m | Useful display mask, but overlaps the water class we already have. Not a new continuous moisture or water-depth feature. Keep its date visible. |
| [Vegetation vigor](https://open.canada.ca/data/en/dataset/347a2de5-1006-4c1f-ba09-b66947654d0a) | NBR / dNBR spectral composites from Harmonized Landsat–Sentinel data | **Quebec**, July 15–September 15 acquisition windows; 2014 onward; producer changes in 2025; EPSG:32198 | Exclude from Ontario joins. Cloud/smoke masking and same-season disturbance confound interpretation. One published download URL contains a backslash; preserve that access defect. |
| [Intensity / spread potential](https://open.canada.ca/data/en/dataset/1728e7f9-472a-474e-9e04-f96bf59479f9) | Six ordinal classes from fuel distribution and fire-behaviour knowledge | **Quebec**, 25 m; metadata starts June 12, 2025; southern dissemination south of 52° | Not Ontario data and **not ignition probability**. Can inspire a clearly fictional fuel/spread game rule; cannot be transplanted as an Ontario risk map. |
| [Preventive measures](https://open.canada.ca/data/en/dataset/adfa340a-1781-48b1-ab17-2e1ca1b915df) | Open-fire prohibitions, access prohibitions and forest-work restrictions | **Quebec** operational polygons; GeoJSON/WFS; metadata start `0001-01-01` is not historical coverage | Policy context, not a 2,000-year record. Exclude from Ontario labels. Restrictions may respond to danger, creating policy/outcome confounding. |

The two height products are imputed forest-structure estimates from lidar plots and Landsat, intended for strategic monitoring rather than operational management. A national bounding box alone does not establish valid values everywhere inside Ontario. Nodata, water and unclassified land must remain distinct.

## Stronger Ontario / national leads found across the pages

1. **[SCANFI v2](https://open.canada.ca/data/en/dataset/07653869-f303-46c2-a04e-9ab479b73cbf)** is the strongest structural lead: 30 m maps at five-year intervals, 1985–2025, with height, crown closure, biomass, stand age and species. Its [official README](https://ftp.maps.canada.ca/pub/nrcan_rncan/Forests_Foret/SCANFI/v2/_SCANFI_v2_read_me.txt) specifies metres, percent crown closure, tonnes/ha biomass and years of stand age. Version 2 species layers are crown-closure percentages directly; version 1 used proportions. The publisher recommends regional/national assessment, warns about pixel-level temporal inconsistency, and uses temporally smoothed imagery and disturbance records through 2025. Retrospective reconstruction is not proof the information was available in each historical year.
2. **[Current national FBP fuel types](https://open.canada.ca/data/en/dataset/851e6a27-a250-41e6-9cd0-d7ff96455dd6)** supply 2026 categorical fuels at 30/100 m, derived from SCANFI v2. Class 13 is unmatched vegetated fuel, not zero hazard; several slash/plantation fuel classes are absent. This is stronger game context than generic forest colour, but a 2026 map cannot repair historical predictors. The published WCS capability says “WMS image only”; do not assume a numerical coverage download is permitted merely because operations are advertised.
3. **Ontario [fire disturbance areas](https://open.canada.ca/data/en/dataset/83d09a07-542a-4d52-97b2-2e475c808806) and [points](https://open.canada.ca/data/en/dataset/e2e699b3-35bc-4efc-9c64-0f9fb749d342)** provide complementary geometry. The point product describes fires below 40 ha; size-dependent geometry must not become a hidden sample filter. [In-year perimeters](https://open.canada.ca/data/en/dataset/42979ae9-de32-4511-9e89-388b30134304) explicitly omit some fires, can be days old and are illustrative. Their daily refresh is not a complete daily trajectory for every incident.
4. **Ontario [fire-weather network](https://open.canada.ca/data/en/dataset/b7ec4dcd-4f54-4602-9231-33964e6a2d2d)** lists 123 stations, hourly observations and a current [Datamart feed](https://dd.weather.gc.ca/today/observations/swob-ml/partners/on-firewx/), with quality assessment marked “No.” The metadata does not establish a downloadable 1988–2024 hourly archive. It does not replace the monthly ECCC summaries used in the annual experiment.
5. **Ontario [response-plan areas](https://open.canada.ca/data/en/dataset/877eec7c-5298-4537-a357-4870c8691a36), [facilities](https://open.canada.ca/data/en/dataset/fd0e2449-dd85-46c1-94b7-ad84eb1c5554) and [suppression rates](https://open.canada.ca/data/en/dataset/43e8edd8-6306-4453-8774-835d071299f1)** inform credible resource tradeoffs. Game credits remain fictional, not these published dollar rates. Response recommendations and equipment availability are not estimates of intervention effectiveness.
6. **[National ignition density](https://open.canada.ca/data/en/dataset/3f0a6405-0a1a-420b-ae99-068a4aeb3b95)** summarizes 1980–2023 human/lightning ignitions. Useful historical description, but a pooled map including later test years leaks those years into an earlier prediction. Satellite hotspots also repeat one fire and miss some detections; they are not independent ignition labels.

## Integration schema and acquisition

Keep three roles separate: **observed source value**, **derived context**, and **simulated game state**. Each layer needs `dataset_id`, exact `resource_url`, retrieval time, SHA-256, observed period, native CRS/resolution, units/category legend, nodata semantics, display CRS/bounds, resampling, footprint and role. Missing values remain missing. Date `2022` on a water layer must not become `year=1988` through a join.

For bounded acquisition, request a projected Ontario map window and legend from an advertised WMS; preserve response bytes and request parameters. These are **styled display images**, not numerical height/biomass measurements. Numerical analysis needs a documented GeoTIFF/COG or an explicitly supported coverage subset with scale/nodata verified. Prefer ranged/tiled reads and cached Ontario windows; do not download a national archive for every layer merely to render a game.

Use the official Ontario polygon independently of raster classification. Full Ontario includes Toronto/GTA, Ottawa and Windsor; an unclassified woodland pixel is not absent geography. Keep water/background masks and source-coordinate uncertainty visible in the field guide.

## Could the features improve performance?

**No improvement has been measured from these new layers.** The annual study has 31 training years and remains frozen. A fixed Ontario-wide 2015 height average is the same number for every year: after centring it has zero variance and supplies no annual predictive information. Adding ten static attributes does not create ten useful yearly features. Sampling context around the fires whose eventual sizes define the target can also condition on the outcome and change the intended task.

A worthwhile next design is **dated regional aggregation with ecological memory**, retaining annual targets and the agreed observation unit. Candidate inputs are previous-available forest composition/closure, prior disturbance fraction and lagged seasonal weather. An ablation should compare weather only; weather plus one structural block; weather plus lagged disturbance; and both. Match chronological folds and feature/label budgets against ridge and RBF before one small QSVR. Training-only evaluation must precede any new reserved test period; the already inspected 2019–2024 years cannot certify a newly selected architecture. SCANFI temporal smoothing and the availability of historical snapshots require a separate leakage audit.

This is a feasible hypothesis, **not an architectural breakthrough**. New context can improve a game's explanatory depth without improving the published predictor. Current work acquires and audits context and assesses eligibility; it does not retune evaluated annual models, alter final predictions or submit hardware.

## Access status and remaining checks

All package metadata were retrieved. NTEMS and national FBP WMS capabilities and the SCANFI README were retrieved successfully. The Quebec potential PDF guide returned an access error; its catalogue description supports the limited interpretation above. Ontario display windows, legends and any numerical subset checks are being collected separately, with receipts. Raw resource availability, nodata decoding and empirical model benefit are not inferred from a successful metadata request.

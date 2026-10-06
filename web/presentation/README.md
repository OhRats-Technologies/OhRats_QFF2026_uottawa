# Presentation

**Seven main slides · five-minute plan · two question appendices.** Official live duration is organizer-announced. The story is annual Ontario estimation, unsuccessful reused-year prediction, and a measured encoding-scale diagnosis. Dataset construction and classical/QAOA/SQD selection are in the main talk. Diagonal SQD adds no optimization benefit.

## Open or submit

- [PDF slides](slides/ontario-wildfire.pdf): offline, fixed layout, all nine slides.
- [Editable PowerPoint](slides/ontario-wildfire.pptx): native charts/tables and source-linked speaker notes; motion is in the browser version.
- Browser presentation: from the repository root, run `bun run web/presentation/serve.ts`, then open **http://127.0.0.1:8790/web/presentation/**. No install, CDN, credentials or hardware connection.

Use arrows or Space to navigate, **N** for speaker notes, **O** for the index, **F** for fullscreen. Home/End select the first/last main slide; appendices follow the main slides. The bandwidth view switches among five measured settings; it does not simulate or select a better model. The opening uses actual 2021 Ontario cover pixels and raw recorded fire locations. The dataset view switches between Algonquin-area pixels, recorded locations and an actual annual row with four climate measurements. Angle controls smoothly rotate illustrative phase states while the heatmap switches among saved measured matrices. These diagrams are explanatory; dots are not predicted hotspots, and the circles are not full entangled states. The browser honors reduced motion and adapts to portrait screens. Print saves all slides, not just the current slide.

| Main slide | Planned seconds |
|---|---:|
| Annual wildfire question | 30 |
| Dataset construction and reused evaluation | 55 |
| Classical and QAOA/SQD feature selection | 45 |
| Matched chronological development | 45 |
| Missed later-year extremes | 55 |
| Scale and kernel geometry | 40 |
| Findings and limits | 30 |

Total **300 seconds**. Appendix: a visual circuit explanation and compute receipts.

The separate [QSVR arcade and walkthrough](../demo/README.md) run on the same server: **http://127.0.0.1:8790/web/demo/** for Signal Run, **http://127.0.0.1:8790/web/demo/lab.html** for the evidence views. It is optional demonstration material, not an extra main slide or new experiment.

## Evidence and authoring

[README](../../README.md) · [Report](../../docs/REPORT.md) · [Final results](../../docs/ANNUAL_FINAL.md) · [Bandwidth diagnostic](../../docs/ANNUAL_BANDWIDTH_GEOMETRY.md).

`evidence.json` is a published snapshot of six frozen result records, an independent raw-source audit, a public annual example row and ten saved training matrices. `evidence.py --check` compares it with the original local matrices without fitting or new states; rebuilding this snapshot requires the ignored geometry cache. Browser/PPTX charts are editable source representations, not flattened report screenshots. Heatmaps and PowerPoint chart values round to six decimals; quoted metrics use original records.

[Map provenance](assets/map.json) pins the cropped raster, boundary and raw fire archive. `map_assets.py` reproduces descriptive assets from ignored inputs; nearest-neighbour display preserves class categories, not native 30 m display resolution. All 1,200 raw 2021 location markers are contextual and include identity-quarantined records; the annual target separately uses 1,194 accepted records. Woodland classes are not tree density or final climate predictors. The full official boundary and Toronto/GTA, Ottawa and Windsor remain visible independently of coverage. Grey means no mapped woodland class (0/255), not no vegetation. City control-point checks are in the map receipt and [display audit](../../docs/DATA_REVIEW.md#ontario-map-display-correction).

Public viewing needs bun; ordinary public evidence replay uses uv as documented in the root README. `check.mjs` and `export-slides.mjs` are authoring tools using the Codex-bundled Playwright/Presentations runtimes, not dependencies for viewing or evaluating the submitted artifacts. The browser build has no frontend packages to install. PDF captures the browser layout; PowerPoint uses static native layouts, a rank chart in place of the interactive heatmap and does not claim identical animations or a PowerPoint application test.

The [submission audit](../../docs/SUBMISSION_AUDIT.md) records artifact, content and browser checks separately from historical scientific tests. Submission itself remains a team action.

Motion uses staged reveals and direct controls; reduced motion presents the same final values. Design reference: [Apple motion guidance](https://developer.apple.com/design/human-interface-guidelines/motion).

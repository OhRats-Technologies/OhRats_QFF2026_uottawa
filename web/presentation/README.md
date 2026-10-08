# Presentation

**Seven main slides · five-minute plan · two question appendices.** Official live duration is organizer-announced. The story is annual Ontario estimation, unsuccessful reused-year prediction, and a measured encoding-scale diagnosis. Dataset construction and classical/QAOA/SQD selection are in the main talk. Diagonal SQD adds no optimization benefit.

## Open or submit

- [PDF slides](slides/ontario-wildfire.pdf): offline, fixed layout, all nine slides.
- [Editable PowerPoint](slides/ontario-wildfire.pptx): native charts/tables and source-linked speaker notes; motion is in the browser version.
- Browser presentation: from the repository root, run `bun run web/presentation/serve.ts`, then open **http://127.0.0.1:8790/web/presentation/**. Bun serves the committed assets; optional remote display fonts have system fallbacks.

An optional `--port=8791` selects another local port; `--port=0` chooses an available one. The server stays bound to localhost.

Use arrows or Space to navigate, **B** to toggle Field Guide Betty, **N** for speaker notes, **O** for the index, **F** for fullscreen. Home/End select the first/last main slide; appendices follow the main slides. The slideshow shares the Fireline quantum engineering workbench aesthetic, with Beatrice ("Betty" the code-drawn firefighter beaver) presenting live commentary across all slides. The bandwidth view switches among five measured settings; it does not simulate or select a better model. The opening uses actual 2021 Ontario cover pixels and raw recorded fire locations. The dataset view switches between Algonquin-area pixels, recorded locations and an actual annual row with four climate measurements. Angle controls smoothly rotate illustrative phase states while the heatmap switches among saved measured matrices. These diagrams are explanatory; dots are not predicted hotspots, and the circles are not full entangled states. The browser honors reduced motion and adapts to portrait screens. Print saves all slides, not just the current slide.

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

[Five-minute spoken outline](talk.md) follows these seven timings, with two short visual interactions. Use the richer speaker notes for questions rather than reading them during the talk. Rehearsal determines the actual delivery time.

The interactive [canvas Fireline game](../demo/README.md) runs on the same server at **http://127.0.0.1:8790/web/demo/**. The presentation shares its CRT engineering palette, live pixel-art guide Beatrice, and component styling.

## Evidence and authoring

[README](../../README.md) · [Report](../../docs/REPORT.md) · [Final results](../../docs/ANNUAL_FINAL.md) · [Bandwidth diagnostic](../../docs/ANNUAL_BANDWIDTH_GEOMETRY.md).

`evidence.json` is a published snapshot of six frozen result records, an independent raw-source audit, a public annual example row and ten saved training matrices. `evidence.py --check` compares it with the original local matrices without fitting or new states; rebuilding this snapshot requires the ignored geometry cache. Browser/PPTX charts are editable source representations, not flattened report screenshots. Heatmaps and PowerPoint chart values round to six decimals; quoted metrics use original records.

The later [forest context study](../../docs/FOREST_CONTEXT.md) is separate from this frozen annual comparison and its input-only scale diagnostic. It fits fixed training-only recipes and includes a same-width zero control; it changes none of the six displayed final-year predictions. The speaker notes identify annual rows without assuming temporal independence and explain that the feature map has no learned variational parameters.

[Map provenance](assets/map.json) pins the cropped raster, boundary and raw fire archive. `map_assets.py` reproduces descriptive assets from ignored inputs; nearest-neighbour display preserves class categories, not native 30 m display resolution. All 1,200 raw 2021 location markers are contextual and include identity-quarantined records; the annual target separately uses 1,194 accepted records. Woodland classes are not tree density or final climate predictors. The full official boundary and Toronto/GTA, Ottawa and Windsor remain visible independently of coverage. Grey means no mapped woodland class (0/255), not no vegetation. City control-point checks are in the map receipt and [display audit](../../docs/DATA_REVIEW.md#ontario-map-display-correction).

Public viewing needs bun; ordinary public evidence replay uses uv as documented in the root README. `check.mjs` and `export-slides.mjs` are authoring tools using the Codex-bundled Playwright/Presentations runtimes, not dependencies for viewing or evaluating the submitted artifacts. The browser build has no frontend packages to install. PDF captures the browser layout; PowerPoint uses static native layouts, a rank chart in place of the interactive heatmap and does not claim identical animations or a PowerPoint application test.

`check.mjs` writes its test PDF under ignored `.cache/judge-submission/browser` and verifies that published PDF/PPTX hashes stay unchanged. The native export layouts in `export-slides.mjs` also require content reconciliation before rebuilding a later submission snapshot.

The [submission audit](../../docs/SUBMISSION_AUDIT.md) records artifact, content and browser checks separately from historical scientific tests. Submission itself remains a team action.

Motion uses staged reveals and direct controls; reduced motion presents the same final values. Design reference: [Apple motion guidance](https://developer.apple.com/design/human-interface-guidelines/motion).

An [earlier clean tracked-tree viewing check](../../docs/data/current_view_portability.json) opens all nine slides, the five-view walkthrough, game controls/inspectors, eight context choices and seven height epochs with external requests blocked. The [older receipt](../../docs/data/static_view_portability.json) retains its original seven-choice snapshot. The exported tree contains no ignored caches, credentials or installed project packages; served PDF/PPTX bytes match the committed files. This verifies viewing on this Mac with installed Bun, not public GitHub access, remote cloning or fresh scientific training. The optional authoring checker is `portable-check.mjs`; it uses the isolated browser tooling and leaves a new ignored receipt/tree for each source commit.

The browser conclusion now connects the original annual comparison to three measured diagnostic lessons: encoding, objective/prediction mismatch and downstream mitigation. The resources appendix shows actual20-feature shot-sweep counts at512/1024/2048 on Marrakesh/Quebec, with Wilson intervals and108 charged QPU seconds across12 jobs. [The scientific response](../../docs/CRITIQUE_RESPONSE.md) supplies stability, exact-classical timing and repair dependence. Seven main slides still total300 seconds. Exported PDF/PPTX preserve the earlier original-study snapshot; their conclusion and resources pages do not incorporate these later findings. Use the browser version for the updated talk, and update the native export layouts before rebuilding an offline deck.

[Latest critique-response viewing receipt](../../docs/data/critique_response_handoff.json) verifies the updated nine-slide browser talk, twelve measured yield points and source-free game/walkthrough viewing, with external requests blocked. It preserves the earlier exported deck bytes. Rebuild the yield asset with `uv run python scripts/presentation_shots.py`.

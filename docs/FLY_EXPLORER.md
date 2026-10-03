# Fly explorer

A full-screen local instrument: measured anatomy, weighted connectivity, continuous evolution traces, and paired saved comparisons. The default canvas has no header, footer, status badge, scientific counters, decorative titles or persistent technical readout. Bun builds and serves the frontend; uv prepares the frozen data.

## Open and rebuild

`explorer/index.html` is a self-contained portable HTML, approximately 10 MB, with embedded compressed data and bundled scripts. No assets, fonts, CDN scripts, IBM requests or live experiment calls are required by the application. External attribution links are deliberate user navigation.

```sh
uv sync --locked
uv run python -m flybrain.explorer
bun install --cwd explorer --frozen-lockfile
bun run --cwd explorer build
bun run --cwd explorer test
bun run --cwd explorer start
```

The local site is `http://127.0.0.1:8765/`. Set `FLY_PORT` to choose another local port. The server binds only to loopback and serves the built HTML. The browser review tool permits only HTTP/HTTPS: direct file-URL opening was blocked, so that route remains unverified. Static checks confirm that the portable HTML embeds its dependencies and data; the application was reviewed through its local server.

## Explore

- **Atlas:** drag to orbit, scroll to magnify; hover the left color dock to reveal population names. Select a branch, population, body ID or region, then focus. Search with the magnifier or `/`. Context branches, surfaces and a Z section have discreet icon controls. There are no planar camera buttons; reset restores the useful front view while free orbit remains available.
- **Connections:** static structural graph; tube thickness follows symmetrized contact strength. Select a population to highlight its links and follow the strongest neighboring populations. This layout is schematic, independent of anatomical location.
- **Interference:** eight time traces, colored for the ideal quantum walk and pale for classical diffusion. Each row shares one maximum across those two models, so small populations are legible without claiming equal probabilities across rows. Select a trace for the actual percentages. Phase mode shows complex amplitude around the time axis, relative to the source return amplitude; row scaling is retained. Drag to reveal depth. Bright colored traces have elapsed; dim traces lie ahead. The pale classical reference is shown across the full time window.
- **Compare:** mirrored bars, measured frequencies on the left and ideal probabilities on the right, using one global probability scale. Initial state, Short walk, Long walk and Pm2a disconnected replace opaque circuit codes. Hover explains their model settings. These are four saved IBM comparisons, not live submissions or biological activity.

The custom scrubber captures pointer dragging, supports touch, and implements Arrow keys (0.05), Shift+Arrow (0.5), Home and End. Play advances continuously at 0.7 model units per wall-clock second and stops at 8. The eigensystem evaluates probabilities and complex amplitudes at the exact current time; playback no longer advances through 81 discrete snapshots. Curve geometry is sampled at 401 points, with an exact moving endpoint and cursor. Camera framing uses a one-second ease; reduced-motion preferences disable camera tweening and CSS animation. Playback and orbit start only on request. Space controls playback; 1–4 switch views. Escape closes discovery or restores a hidden interface.

## Provenance and boundaries

The geometry snapshot includes 216 real neuron skeletons and 18 simplified ROI surfaces. See `datasets/fly/morphology/README.md` and its source manifest for deterministic selection, coordinate conversions, source hashes, sampling and display simplification. Contralateral anatomy is independently measured, not mirrored.

The graph retains the pinned eight-population source, symmetrized Laplacian, dimensionless time and intact degree scale after disconnections. Continuous evolution is computed from the same eigensystem as the verified Python reference. Quantum traces are probabilities, not neuronal firing. Phase traces are mathematical state amplitudes, not measured phases or evidence of quantum processing in the fly.

`artifacts/sprint-20261003/hardware-counts/hardware.json` supplies the four returned comparisons exactly. Credentials and service/job identities are excluded. The explorer submits no jobs. Dataset attribution and caveats are available through the `?` dialog; software MIT notices are embedded in the HTML and preserved in `explorer/THIRD_PARTY_LICENSES.txt`.

The earlier portfolio, report, 51-file evidence snapshot and 39-source hash manifest are retained. The explorer has its own build manifest, so it does not rewrite the provenance of the earlier report.

## Review loop

This uses a bounded proposal–build–inspect–correct workflow inspired by the user's iterative-design request; it is not an autonomous architecture-search benchmark. Each pass has a concrete gate.

| Pass | Gate and correction |
| --- | --- |
| 1. Sources | Public MaleCNS SWC/mesh parsing, frame units, parent validity, source hashes; rejected invented or mirrored anatomy. |
| 2. Layout | Replaced the initial report-style columns with a full-screen scene; removed header, footer, branding and status badge after owner feedback. |
| 3. Anatomy | Added measured left-side representatives, corrected camera framing and preserved uncropped source topology while declaring the display crop. |
| 4. Interaction | Tested selection, focus, discovery, sections, mode switching, modal behavior and bookmarks; fixed an overly broad navigation selector and initialization overwriting the requested URL fragment. |
| 5. Responsive | Reviewed phone and desktop layouts; removed a crowded persistent inspector and corrected camera fitting. |
| 6. Visual meaning | Owner review rejected duplicated graph screens, hollow titles, technical counts and opaque case names. Replaced them with structural tubes, time traces and paired comparisons; moved technical details into an optional dialog. |
| 7. Motion | Replaced the browser range control with a custom pointer/keyboard scrubber and exact continuous evolution. Verified dragging to a non-grid time, play/pause advancement and phase mode. |
| 8. Fidelity | 38 Python tests plus three Bun model tests pass. The continuous JS solver agrees with all 81 × 8 × 9 stored reference combinations, arbitrary between-sample times and an analytic two-node interference case. |
| 9. Portability | Frozen Bun install and dependency audit, embedded-asset/hash checks, original evidence verifier, and CPU geometry fallback. HTTP/HTTPS review is verified; direct file-URL review remains blocked by tool policy. |

The renderer draws only when the scene changes, orbit runs or playback runs. The CPU fallback projects the same measured geometry and honors clipping and trace draw ranges; it sparsely rasterizes region wire triangles. It is a functional fallback, not identical shaded output or a measured cross-device performance claim. Final screenshots document the reviewed build rather than a mockup.

# MaleCNS anatomy snapshot

Measured geometry from [MaleCNS v1.0](https://male-cns.janelia.org/download/), licensed [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/). Attribution: FlyEM / HHMI Janelia, Cambridge, MRC LMB, Google Research. Geometry is separate from the eight-population graph in `../male_cns_v1/`.

`geometry.json` contains 216 coarse neuron skeletons and 18 neuropil meshes in one MaleCNS EM coordinate frame, in micrometres. SWC voxel coordinates are multiplied by 0.008; legacy mesh nanometres by 0.001. No inter-specimen alignment or mirrored anatomy is used. Source URLs, byte sizes, SHA-256 hashes and the output hash are in `manifest.json`.

Sampling is deterministic: ten soma-X-spread representatives for each of the eight modeled right populations; ten independently measured left representatives per type as anatomy context; up to three body-ID-spread neurons on each side for sixteen context types. Missing types are omitted. `group` is non-null only for the 80 right-side model representatives. The remaining neurons are anatomy context, not additional model nodes.

All published skeleton nodes and parent edges are retained in the snapshot, rounded to 0.001 μm for storage. ROI meshes use 2.5 μm vertex clustering, averaging vertices in each occupied grid cell, removing collapsed and duplicate triangles. This grid parameter is not a measured geometric-error bound. These are display surfaces, not a new segmentation or a complete brain mesh.

The explorer crops skeleton edges to the selected ROI bounding box expanded by 35 μm. This removes descending extensions from the default brain view; the uncropped source geometry remains in the snapshot. Context, region surfaces and Z clipping can be controlled separately. The CPU rendering fallback shows sparse ROI wire triangles and omits subpixel skeleton strokes during rasterization; it retains the same camera and source coordinates.

Reacquire the bounded snapshot with:

```sh
uv run --with pyarrow==22.0.0 python -m flybrain.morphology
```

Raw downloads are cached under ignored `results/morphology-source/`. This uses public data endpoints; no account or event token is needed. See the parent data README for pinned graph provenance. One specimen and selected skeletons do not support behavioral, sex-comparison, or biological quantum-processing claims.

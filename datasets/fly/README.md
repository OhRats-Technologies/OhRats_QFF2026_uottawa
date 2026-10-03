# MaleCNS visual-system cell-type snapshot

A small derived dataset from the male fruit-fly CNS v1.0. The reconstruction and annotations are from FlyEM / HHMI Janelia, the University of Cambridge, MRC LMB, and Google Research. Connectivity tables are served by the Reiser Lab Cell Type Explorer.

## Attribution and source

- [MaleCNS project](https://male-cns.janelia.org/)
- [Official downloads and license](https://male-cns.janelia.org/download/)
- [Cell Type Explorer](https://reiserlab.github.io/celltype-explorer-drosophila-male-cns/)
- [Explorer table definitions](https://reiserlab.github.io/celltype-explorer-drosophila-male-cns/help.html#connectivity)
- Source repository commit: `789cc6c105798ce2fd70ba85dab394f90899616b`.
- Dataset license: [Creative Commons Attribution 4.0](https://creativecommons.org/licenses/by/4.0/).

Changes made: select eight cell-type groups, extract exact total directed contacts from their downstream tables, and export the induced graph as CSV. The experiment subsequently symmetrizes weights and excludes self-loops; the CSV retains source direction and self-loops. No author or institution endorses this experiment.

## Selection and units

Start with `Mi1_R`. Select its seven highest-weight downstream partners, excluding itself and sorting ties by partner ID. Extract the downstream tables for all eight groups and retain contacts between selected groups.

The HTML displays rounded mean connections per neuron, but includes exact population totals in the `∑ connections:` table-cell title. The importer uses those exact integer totals. Weights are anatomical contact counts, not firing rates, signed functional effects, or per-neuron strengths. Population size affects the totals.

`nodes.csv` establishes node-to-basis-state order. Each node is a cell-type/hemisphere group. `edges.csv` contains `source,target,synapses`. An absent edge means no row was present in the published table, not proof that a connection is biologically impossible. Results describe a closed selected graph, not a circuit embedded in the whole brain.

`manifest.json` records the pinned source commit, selection rule, each source URL and SHA-256, retrieval time, license, and CSV hashes. Loading validates CSV hashes.

## Rebuild without overwriting

```sh
uv run python -m flybrain fetch --data data/fly-rebuilt
uv run python -m flybrain run --data data/fly-rebuilt --output results/rebuilt
```

The importer refuses a nonempty destination. Expect eight HTML pages (a few megabytes), not a full image volume or connection table. Rebuilding should reproduce the included CSV hashes; retrieval timestamps differ.

The explorer is an annotation snapshot. Counts can differ from live neuPrint queries or headline totals due to revisions and counting conventions. Do not mix versions silently.

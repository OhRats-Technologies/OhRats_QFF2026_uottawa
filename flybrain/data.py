"""Extract a pinned, attributed cell-type graph from the Janelia explorer."""

import csv
from datetime import datetime, timezone
import hashlib
from html.parser import HTMLParser
import io
import json
from pathlib import Path
import re
from urllib.request import urlopen

import numpy as np

REPO = Path(__file__).resolve().parents[1]
DEFAULT_DATA = REPO / "datasets/fly/male_cns_v1"
SOURCE_COMMIT = "789cc6c105798ce2fd70ba85dab394f90899616b"
SOURCE_ROOT = (
    "https://raw.githubusercontent.com/reiserlab/"
    f"celltype-explorer-drosophila-male-cns/{SOURCE_COMMIT}/types/"
)
SEED_TYPE = "Mi1_R"


class ConnectionParser(HTMLParser):
    """Read exact integer totals, not rounded per-neuron display values.

    The upstream HTML omits optional tr/td closing tags. Flush rows on the
    next tr as well as on explicit closing tags, and scope to downstream only.
    """

    def __init__(self):
        super().__init__()
        self.active = False
        self.found = False
        self.row = None
        self.rows = []

    def finish_row(self):
        if self.row and "target" in self.row:
            if "synapses" not in self.row:
                raise ValueError("Connection row is missing an exact synapse count")
            self.rows.append(self.row)
        self.row = None

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == "table" and attrs.get("id") == "downstream-table":
            self.active = self.found = True
        if not self.active:
            return
        if tag == "tr":
            self.finish_row()
            self.row = {}
        if self.row is None:
            return
        if tag == "a":
            match = re.fullmatch(r"([A-Za-z0-9_-]+)\.html#s-c", attrs.get("href", ""))
            if match:
                self.row["target"] = match[1]
        if tag == "td" and attrs.get("title", "").startswith("∑ connections:"):
            self.row["synapses"] = int(attrs["title"].split(":", 1)[1].replace(",", ""))

    def handle_endtag(self, tag):
        if self.active and tag in {"tr", "table"}:
            self.finish_row()
            if tag == "table":
                self.active = False


def parse_connections(html):
    parser = ConnectionParser()
    parser.feed(html)
    parser.close()
    if not parser.found or not parser.rows:
        raise ValueError(
            "Expected populated downstream table; upstream format may have changed"
        )
    targets = [row["target"] for row in parser.rows]
    if len(set(targets)) != len(targets) or any(
        r["synapses"] <= 0 for r in parser.rows
    ):
        raise ValueError("Duplicate partners or invalid counts in upstream table")
    return parser.rows


def digest(data):
    return hashlib.sha256(data).hexdigest()


def csv_bytes(fields, rows):
    stream = io.StringIO(newline="")
    writer = csv.DictWriter(stream, fieldnames=fields, lineterminator="\n")
    writer.writeheader()
    writer.writerows(rows)
    return stream.getvalue().encode("utf-8")


def fetch_snapshot(destination=DEFAULT_DATA):
    """Fetch eight source pages. No credentials or full brain download needed."""
    destination = Path(destination)
    if destination.exists() and any(destination.iterdir()):
        raise ValueError(
            "Destination is nonempty; choose a new --data directory to preserve provenance"
        )
    sources, tables = [], {}

    def fetch(node):
        url = SOURCE_ROOT + node + ".html"
        with urlopen(url, timeout=30) as response:
            raw = response.read(8 * 1024 * 1024 + 1)
        if len(raw) > 8 * 1024 * 1024:
            raise ValueError("Source page exceeds 8 MiB limit")
        tables[node] = parse_connections(raw.decode("utf-8"))
        sources.append(
            {"node": node, "url": url, "sha256": digest(raw), "bytes": len(raw)}
        )

    fetch(SEED_TYPE)
    partners = sorted(
        (r for r in tables[SEED_TYPE] if r["target"] != SEED_TYPE),
        key=lambda r: (-r["synapses"], r["target"]),
    )[:7]
    if len(partners) != 7:
        raise ValueError("Not enough downstream partners for eight nodes")
    nodes = [SEED_TYPE] + [r["target"] for r in partners]
    for node in nodes[1:]:
        fetch(node)
    edges = [
        {"source": source, **row}
        for source in nodes
        for row in tables[source]
        if row["target"] in nodes
    ]
    files = {
        "nodes.csv": csv_bytes(["id"], [{"id": node} for node in nodes]),
        "edges.csv": csv_bytes(["source", "target", "synapses"], edges),
    }
    manifest = {
        "schema_version": 1,
        "dataset": "male-cns:v1.0",
        "source_commit": SOURCE_COMMIT,
        "retrieved_at": datetime.now(timezone.utc).isoformat(),
        "license": "CC-BY-4.0",
        "license_url": "https://creativecommons.org/licenses/by/4.0/",
        "attribution": "FlyEM / HHMI Janelia, Cambridge, MRC LMB, Google Research; Reiser Lab Cell Type Explorer",
        "source_home": "https://male-cns.janelia.org/",
        "seed": SEED_TYPE,
        "node_unit": "cell type and hemisphere, not individual neuron",
        "selection": "Mi1_R plus its seven strongest downstream cell-type partners by total contacts; ties by ID",
        "edge_unit": "total directed anatomical synaptic contacts between the selected cell-type groups",
        "limitations": "Selected induced subgraph of published tables; outside connections omitted; one specimen",
        "sources": sources,
        "files": {name: digest(raw) for name, raw in files.items()},
    }
    destination.mkdir(parents=True, exist_ok=True)
    for name, raw in files.items():
        (destination / name).write_bytes(raw)
    (destination / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    return manifest


def load_graph(directory=DEFAULT_DATA):
    directory = Path(directory)
    manifest = json.loads((directory / "manifest.json").read_text())
    if manifest.get("schema_version") != 1:
        raise ValueError("Unsupported data manifest schema")
    for name in ("nodes.csv", "edges.csv"):
        if digest((directory / name).read_bytes()) != manifest["files"][name]:
            raise ValueError(f"Snapshot checksum mismatch: {name}")
    with (directory / "nodes.csv").open(newline="") as stream:
        nodes = [row["id"] for row in csv.DictReader(stream)]
    n = len(nodes)
    if len(set(nodes)) != n or n < 2 or n > 32 or n & (n - 1):
        raise ValueError("Expected 2, 4, 8, 16, or 32 distinct nodes")
    index = {node: i for i, node in enumerate(nodes)}
    adjacency = np.zeros((n, n))
    seen = set()
    with (directory / "edges.csv").open(newline="") as stream:
        for row in csv.DictReader(stream):
            pair = row["source"], row["target"]
            weight = int(row["synapses"])
            if pair in seen or weight <= 0 or any(node not in index for node in pair):
                raise ValueError("Duplicate or invalid edge")
            seen.add(pair)
            adjacency[index[pair[0]], index[pair[1]]] = weight
    return nodes, adjacency, manifest

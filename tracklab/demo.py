"""Build a portable, offline demonstration from validated numerical results."""

import base64, json, hashlib
from datetime import datetime, timezone
import numpy as np
from flybrain.data import REPO, load_graph
from flybrain.walks import laplacian, undirected
from flybrain.atlas import all_source_trajectories
from flybrain.progress import timed_stage


def main():
    output = REPO / "demo"
    output.mkdir(exist_ok=True)
    nodes, adjacency, provenance = load_graph()
    weights = undirected(adjacency)
    times = np.linspace(0, 8, 81)
    scale = weights.sum(axis=1).max()
    trajectories = {}
    with timed_stage("presentation", "offline_demo_generation") as evidence:
        for lesion in range(-1, len(nodes)):
            w = weights.copy()
            if lesion >= 0:
                w[lesion, :] = w[:, lesion] = 0
            c, q = all_source_trajectories(laplacian(w, scale), times)
            trajectories[str(lesion)] = {
                "classical": np.round(c, 8).tolist(),
                "quantum": np.round(q, 8).tolist(),
            }
        data = {
            "nodes": nodes,
            "weights": weights.tolist(),
            "times": times.tolist(),
            "trajectories": trajectories,
            "provenance": provenance,
            "generated_utc": datetime.now(timezone.utc).isoformat(),
        }
        for name, folder in [
            ("chemistry", "chemistry"),
            ("budget", "eigenbudget"),
            ("grid", "scheduling"),
            ("spin", "spinweave"),
            ("qml", "kernelforge"),
            ("atlas", "atlas"),
            ("noise", "noise"),
        ]:
            data[name] = json.loads(
                (REPO / "results" / folder / "metrics.json").read_text()
            )
        data["statistics"] = json.loads(
            (REPO / "results/statistics/summary.json").read_text()
        )
        data["evidence"] = json.loads(
            (REPO / "results/evidence/summary.json").read_text()
        )
        data["phaseSweep"] = json.loads(
            (REPO / "results/phaseguard/phase_sweep.json").read_text()
        )
        data["placements"] = json.loads(
            (REPO / "results/phaseguard/placements.json").read_text()
        )
        data["thermal"] = json.loads(
            (REPO / "results/spintherm/metrics.json").read_text()
        )
        data["activeBudget"] = json.loads(
            (REPO / "results/activebudget/metrics.json").read_text()
        )
        data["activeNoise"] = json.loads(
            (REPO / "results/activenoise/metrics.json").read_text()
        )
        data["shield"] = json.loads(
            (REPO / "results/spinshield/metrics.json").read_text()
        )
        data["spinAudit"] = json.loads(
            (REPO / "results/spinaudit/metrics.json").read_text()
        )
        data["flux"] = json.loads((REPO / "results/flyflux/metrics.json").read_text())
        data["strengthNull"] = json.loads(
            (REPO / "results/strengthnull/metrics.json").read_text()
        )
        data["fluxTrajectories"] = json.loads(
            (REPO / "results/flyflux/demo_trajectories.json").read_text()
        )
        pictures = {}
        for folder, file in [
            ("noise", "noise.png"),
            ("atlas", "atlas.png"),
            ("chemistry", "bondbench.png"),
            ("eigenbudget", "eigenbudget.png"),
            ("scheduling", "gridguard.png"),
            ("spinweave", "spinweave.png"),
            ("kernelforge", "kernelforge.png"),
            ("phaseguard", "phaseguard.png"),
            ("spintherm", "spintherm.png"),
            ("activebudget", "activebudget.png"),
            ("activenoise", "activenoise.png"),
            ("spinshield", "spinshield.png"),
            ("flyflux", "flyflux.png"),
            ("strengthnull", "strengthnull.png"),
            ("forecastaudit", "forecastaudit.png"),
        ]:
            pictures[folder] = (
                "data:image/png;base64,"
                + base64.b64encode(
                    (REPO / "results" / folder / file).read_bytes()
                ).decode()
            )
        data["pictures"] = pictures
        template = (REPO / "demo/template.html").read_text()
        html = template.replace(
            "__EXPERIMENT_DATA__",
            json.dumps(data, separators=(",", ":")).replace("</", "<\\/"),
        )
        (output / "index.html").write_text(html)
        (output / "manifest.json").write_text(
            json.dumps(
                {
                    "generated_utc": data["generated_utc"],
                    "sha256": hashlib.sha256(html.encode()).hexdigest(),
                    "evidence": "Offline snapshot; refresh with python -m tracklab.demo",
                },
                indent=2,
            )
            + "\n"
        )
        evidence.update(lesion_states=len(trajectories), times=len(times), offline=True)
    print("Built demo/index.html; no server or credentials required.")


if __name__ == "__main__":
    main()

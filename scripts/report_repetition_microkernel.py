"""Publish validated microkernel counts without private service identifiers."""
import json
from pathlib import Path
import sys
import numpy as np
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from wildfire_lab.mitigation_hardware import sha


def report(output):
    plan = json.loads((ROOT/"experiments/repetition_microkernel.json").read_text())
    blocks = []
    for device in plan["devices"]:
        directory = output/device["backend"]
        prepared = json.loads((directory/"prepared.json").read_text())
        for block in range(plan["blocks"]):
            prefix = f"block-{block}"
            path = directory/f"{prefix}-collected.json"
            if not path.exists():
                raise ValueError("Hardware acquisition is not complete")
            result = json.loads(path.read_text())
            metrics = json.loads((directory/f"{prefix}-metrics.json").read_text())
            summaries = []
            for fault in plan["faults"]:
                for idle in plan["idle_us"]:
                    for arm in plan["arms"]:
                        rows = [r for r in result["rows"] if r["fault"] == fault
                                and r["idle_us"] == idle and r["arm"] == arm]
                        summaries.append(dict(fault=fault, idle_us=idle, arm=arm,
                            rmse=float(np.sqrt(np.mean([r["squared_error"] for r in rows])))))
            blocks.append(dict(backend=device["backend"], block=block,
                shots=sum(r["shots"] for r in result["rows"]),
                quantum_seconds=metrics.get("usage", {}).get("quantum_seconds"),
                summaries=summaries, rows=result["rows"], counts=result["counts"],
                syndrome_counts=result["syndrome_counts"], resources=prepared["resources"],
                collected_sha256=sha(path)))
    public = dict(study=plan["study"], plan_sha256=sha(ROOT/"experiments/repetition_microkernel.json"),
                  status="complete", blocks=blocks, shots=sum(b["shots"] for b in blocks))
    target = ROOT/"docs/results/repetition-microkernel.json"
    target.write_text(json.dumps(public, indent=2)+"\n")
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    fig, axes = plt.subplots(1, 2, figsize=(10, 4), sharey=True)
    colors = ["#6b8995", "#eb9b43", "#167d82"]
    for ax, device in zip(axes, plan["devices"]):
        for i, arm in enumerate(plan["arms"]):
            for j, idle in enumerate(plan["idle_us"]):
                values = [s["rmse"] for b in blocks if b["backend"] == device["backend"]
                          for s in b["summaries"] if s["fault"] == "none"
                          and s["idle_us"] == idle and s["arm"] == arm]
                x = j+(i-1)*.23
                ax.bar(x, np.mean(values), width=.21, color=colors[i],
                       label=arm if j == 0 else None)
                ax.scatter([x]*len(values), values, s=17, color="#172c34", zorder=3)
        ax.set(title=device["backend"], xticks=[0, 1], xticklabels=["0 μs", "20 μs"],
               xlabel="Storage delay · no injected faults")
        ax.spines[["top", "right"]].set_visible(False)
    axes[0].set_ylabel("Overlap RMSE across three phase inputs")
    axes[1].legend(frameon=False)
    fig.tight_layout()
    fig.savefig(ROOT/"docs/figures/repetition-microkernel.png", dpi=180)
    plt.close(fig)
    return dict(status="published", blocks=len(blocks), shots=public["shots"])


if __name__ == "__main__":
    print(json.dumps(report(ROOT/"results/repetition-microkernel-v1")))

"""Compact aggregate exports from immutable measured outcomes."""

import hashlib
import json
from collections import defaultdict
from statistics import mean


def summarize(path):
    record = json.loads(path.read_text())
    if record["status"] != "complete":
        raise ValueError("Only completed outcomes can enter a measured summary")
    groups = defaultdict(list)
    for row in record["rows"]:
        if row["status"] != "complete":
            continue
        selector = row.get("selector")
        name = selector if selector not in {None, "fixed_control"} else row["predictor"]
        if record["axis"] == "combinations":
            selector = selector or row.get("group")
            name = f"{selector} / {row['predictor']}" if selector else row["predictor"]
        elif row.get("group"):
            name += " / " + row["group"]
        spatial = row.get("spatial") or {}
        if spatial.get("control"):
            name += " / " + spatial["control"]
        groups[name].append(row)
    models = []
    for name, rows in groups.items():
        conditions = defaultdict(list)
        for row in rows:
            key = str(row["fold"])
            if row.get("spatial"):
                key += " / side " + str(row["spatial"]["train_side"])
            conditions[key].append(row["metric"]["average_precision"])
        condition_means = {k: mean(v) for k, v in conditions.items()}
        models.append(
            dict(
                name=name,
                mean_average_precision=mean(condition_means.values()),
                condition_average_precision=condition_means,
                mean_prevalence=mean(row["metric"]["prevalence"] for row in rows),
                measured_runs=len(rows),
            )
        )
    return dict(
        study=record["plan"]["id"],
        attempt=record["id"],
        axis=record["axis"],
        outcome_sha256=hashlib.sha256(path.read_bytes()).hexdigest(),
        seconds=record["seconds"],
        quality_checks=record["quality_checks"],
        models=models,
    )


def write_summary(paths, output):
    studies = [summarize(p) for p in paths]
    lines = ['{"status":"measured_screen","final_test_sealed":true,"studies":[']
    for i, study in enumerate(studies):
        models = study.pop("models")
        lines.append(json.dumps(study, separators=(",", ":"))[:-1] + ',"models":[')
        lines.extend(
            json.dumps(m, separators=(",", ":")) + ("," if j < len(models) - 1 else "")
            for j, m in enumerate(models)
        )
        lines.append("]}" + ("," if i < len(studies) - 1 else ""))
    lines.append("]}")
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text("\n".join(lines) + "\n")

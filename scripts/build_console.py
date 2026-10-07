"""Export authentic saved modeller-game recipes; no fitting or circuit execution."""

import csv
import hashlib
import json
from pathlib import Path
import zipfile
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
LABELS = [
    "Annual Temp",
    "Summer Temp",
    "Annual Rain",
    "Summer Rain",
    "Crown Closure",
    "Forest Biomass",
    "Forest Age",
    "Spruce / Pine Mix",
    "Last Year Burned",
    "Biomass Change",
    "Spring Rain",
    "Snowfall",
    "Highest Temp",
    "Lowest Temp",
    "Heating Days",
    "Cooling Days",
    "Broadleaf Crown",
    "Black Spruce Crown",
    "Jack Pine Crown",
    "Last Year Fires",
]


def source(name, hashes):
    path = ROOT / f"docs/data/{name}-evidence.zip"
    hashes[str(path.relative_to(ROOT))] = hashlib.sha256(path.read_bytes()).hexdigest()
    with zipfile.ZipFile(path) as archive:
        return json.loads(archive.read("evidence.json"))


def pack(
    identifier,
    label,
    features,
    specification,
    gram,
    cross,
    state,
    scaling,
    target,
    predicted,
    actual,
    rival,
    resource,
):
    dual = np.asarray(state["dual_coef"])
    support = state["support"]
    raw = np.asarray(cross)[:, support] @ dual + state["intercept"]
    restored = np.maximum(0, np.expm1(raw * scaling["y_scale"] + scaling["y_mean"]))
    np.testing.assert_allclose(restored, predicted, rtol=1e-10, atol=1e-8)
    train_prediction = np.asarray(gram)[:, support] @ dual + state["intercept"]
    values = np.linalg.eigvalsh(gram)
    weights = np.maximum(values, 0) / sum(np.maximum(values, 0))
    rank = float(np.exp(-sum(p * np.log(p) for p in weights if p > 0)))
    return dict(
        id=identifier,
        label=label,
        features=features,
        specification=specification,
        gram=gram,
        cross=cross,
        state=state,
        target_scaling={k: scaling[k] for k in ["y_mean", "y_scale"]},
        train_target_scaled=target,
        train_prediction_scaled=train_prediction.tolist(),
        predicted=predicted,
        actual=actual,
        rbf=rival,
        health=dict(
            rank=rank,
            similarity=float(np.asarray(gram)[~np.eye(len(gram), dtype=bool)].mean()),
            pair_circuits=resource.get(
                "pair_circuits",
                len(gram) * (len(gram) - 1) // 2 + len(cross) * len(gram),
            ),
        ),
    )


def build():
    hashes = {}
    selectors = source("selector-multistart", hashes)
    searches = [
        source(name, hashes) for name in ["expanded-tuning", "expanded-tuning-distinct"]
    ]
    feature_names = json.loads(
        (ROOT / "experiments/selector_multistart.json").read_text()
    )["features"]
    table = list(
        csv.DictReader((ROOT / "docs/data/forest_selector_scaling_training.csv").open())
    )
    rounds = []
    for c in selectors["cohorts"]:
        if len(c["features"]) != 20:
            continue
        fold = c["fold"]
        end = fold[1]
        train_targets = [
            float(r["mean_reported_size_ha"]) for r in table if int(r["year"]) <= end
        ]
        models = []
        for method in ["mi", "exact", "optimized1", "uniform"]:
            m = c["models"][method]
            q = next(r for r in m["rows"] if r["model"] == "qsvr")
            rbf = next(r for r in m["rows"] if r["model"] == "rbf")
            spec = dict(
                C=1.0,
                epsilon=0.2,
                circuit=dict(
                    amplitude="pi32", reps=1, topology="linear", order="canonical"
                ),
            )
            models.append(
                pack(
                    method,
                    {
                        "mi": "Mutual information",
                        "exact": "Exact QUBO",
                        "optimized1": "QAOA + SQD",
                        "uniform": "Uniform sampling",
                    }[method],
                    q["features"],
                    spec,
                    m["quantum_gram"],
                    m["quantum_cross"],
                    q["parameters"],
                    m["preprocessing"],
                    m["scaled_targets"],
                    q["predicted_ha"],
                    q["actual_ha"],
                    rbf["predicted_ha"],
                    m["resource"],
                )
            )
        for search_index, search in enumerate(searches):
            for cohort in search["cohorts"]:
                if cohort["fold"] != fold or cohort["panel"] not in ["weather4", "mi4"]:
                    continue
                for kind in ["fixed_qsvr", "qsvr"]:
                    if kind == "fixed_qsvr" and search_index:
                        continue
                    r = cohort["results"][kind]
                    rbf = cohort["results"]["rbf"]
                    label = (
                        "Fixed"
                        if kind == "fixed_qsvr"
                        else "Tuned"
                        if not search_index
                        else "Wider C"
                    )
                    models.append(
                        pack(
                            f"{cohort['panel']}-{search_index}-{kind}",
                            label,
                            r["columns"],
                            r["specification"],
                            r["train_matrix"],
                            r["cross_matrix"],
                            r["parameters"],
                            r["preprocessing"],
                            r["scaled_targets"],
                            r["predicted_ha"],
                            r["actual_ha"],
                            rbf["predicted_ha"],
                            r["resource"],
                        )
                    )
        # Display every feasible objective as a diagnostic, never invent predictions for unmeasured patches.
        costs = {
            str(state): value
            for state, value in zip(c["sector_states"], c["sector_objectives"])
        }
        rounds.append(
            dict(
                fold=fold,
                train_years=list(range(1988, end + 1)),
                years=list(range(fold[2], fold[3] + 1)),
                models=models,
                baseline=float(np.mean(train_targets)),
                objective=costs,
                optimum=c["exact_objective"],
            )
        )
    assert len(rounds) == 3
    geometry = json.loads((ROOT / "web/presentation/evidence.json").read_text())[
        "geometry"
    ]
    for filename in [
        "docs/data/forest_selector_scaling_training.csv",
        "experiments/selector_multistart.json",
        "web/presentation/evidence.json",
    ]:
        hashes[filename] = hashlib.sha256((ROOT / filename).read_bytes()).hexdigest()
    return dict(
        features=[
            dict(
                id=f,
                label=LABELS[i],
                group="WEATHER"
                if i in [0, 1, 2, 3, 10, 11, 12, 13, 14, 15]
                else "FIRE MEMORY"
                if i in [8, 19]
                else "FOREST",
            )
            for i, f in enumerate(feature_names)
        ],
        rounds=rounds,
        geometry=geometry,
        source_sha256=hashes,
        target="Ontario annual mean reported hectares per size-observed fire",
        limitation="Previously inspected development years and retrospective inputs. Saved recipes, not live training; no new hardware or predictive confirmation.",
    )


if __name__ == "__main__":
    path = ROOT / "web/demo/console/evidence.json"
    path.parent.mkdir(exist_ok=True)
    path.write_text(json.dumps(build(), separators=(",", ":")) + "\n")
    print(
        "Exported three chronological rounds and authentic saved models; no refitting."
    )

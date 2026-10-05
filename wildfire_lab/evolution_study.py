"""Exclusive, hash-pinned policy rollout lifecycle; final years are prohibited."""

import hashlib
import json
import subprocess
import time
from datetime import datetime, timezone
import numpy as np
import pandas as pd
from wildfire_lab.evaluation import sample_indices, split
from wildfire_lab.evolution_evaluator import evaluate
from wildfire_lab.evolution_rollout import run_world

RECIPES = [
    "wildfire_lab/evolution_policy.py",
    "wildfire_lab/evolution_evaluator.py",
    "wildfire_lab/evolution_rollout.py",
    "wildfire_lab/evolution_history.py",
    "wildfire_lab/evolution_study.py",
    "wildfire_lab/evolution_checks.py",
    "scripts/run_policy_evolution.py",
    "wildfire_lab/encoding_screen.py",
    "wildfire_lab/kernel.py",
    "wildfire_lab/evaluation.py",
    "pyproject.toml",
    "uv.lock",
    "experiments/policy_evolution.json",
]


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def verify_confirmation(parent, selected, hashes):
    fixed = [
        "wildfire_lab/evolution_evaluator.py",
        "wildfire_lab/evolution_rollout.py",
        "wildfire_lab/encoding_screen.py",
        "wildfire_lab/kernel.py",
        "wildfire_lab/evaluation.py",
        "experiments/policy_evolution.json",
        "pyproject.toml",
        "uv.lock",
    ]
    if any(hashes[file] != parent["intent"]["recipe_sha256"][file] for file in fixed):
        raise ValueError("Confirmation evaluator differs from development")
    if selected["policy_sha256"] != hashes["wildfire_lab/evolution_policy.py"]:
        raise ValueError("Selected policy code changed")


def run(root, plan_path, stage, policy="evolved_v1"):
    start = time.perf_counter()
    if stage not in ("development", "confirmation"):
        raise ValueError("Unknown online phase")
    plan = json.loads(plan_path.read_text())
    if (
        plan["status"] != "frozen_training_only_policy_evolution"
        or plan["fold"][-1] > 2018
    ):
        raise ValueError("A committed training-only protocol is required")
    commit = subprocess.check_output(
        ["git", "rev-parse", "HEAD"], cwd=root, text=True
    ).strip()
    recipes = (
        RECIPES
        + ["docs/results/policy-evolution-offline.json"]
        + (
            ["experiments/policy_evolution_selection.json"]
            if stage == "confirmation"
            else []
        )
    )
    for file in recipes:
        if (root / file).read_bytes() != subprocess.check_output(
            ["git", "show", f"{commit}:{file}"], cwd=root
        ):
            raise ValueError("Uncommitted opening recipe: " + file)
    hashes = {file: sha(root / file) for file in recipes}
    if stage == "confirmation":
        selected = json.loads(
            (root / "experiments/policy_evolution_selection.json").read_text()
        )
        parent = root / ".cache/wildfire/policy-evolution-development/outcome.json"
        if sha(parent) != selected["development_outcome_sha256"]:
            raise ValueError("Development parent changed")
        verify_confirmation(json.loads(parent.read_text()), selected, hashes)
        policy = selected["selected_policy"]
    path = root / plan["dataset"] / "features.csv"
    if sha(path) != plan["dataset_sha256"]:
        raise ValueError("Training snapshot changed")
    frame = pd.read_csv(path)
    if frame.year.max() > 2018 or frame.incident_id.duplicated().any():
        raise ValueError("Final years or repeated identities in policy input")
    train, valid = split(frame, plan["fold"], (1988, 2018))
    offline = root / "docs/results/policy-evolution-offline.json"
    if (
        stage == "development"
        and json.loads(offline.read_text())["selected_policy"] != policy
    ):
        raise ValueError("Online policy differs from offline selection")
    destination = root / ".cache/wildfire" / ("policy-evolution-" + stage)
    destination.mkdir(parents=True, exist_ok=True)
    intent = dict(
        stage=stage,
        policy=policy,
        plan=plan,
        git_commit=commit,
        recipe_sha256=hashes,
        offline_evidence_sha256=sha(offline),
        created_utc=datetime.now(timezone.utc).isoformat(),
    )
    with (destination / "intent.json").open("x") as f:
        f.write(json.dumps(intent, indent=2) + "\n")
    worlds = []
    try:
        for seed in plan[stage + "_seeds"]:
            ti = sample_indices(len(train), plan["train_cap"], seed)
            vi = sample_indices(len(valid), plan["validation_cap"], seed)
            t, v = train.iloc[ti], valid.iloc[vi]
            if set(t.target.unique()) != {0, 1} or set(v.target.unique()) != {0, 1}:
                raise ValueError("Fresh sample lacks both classes")

            def evaluator(candidate):
                if time.perf_counter() - start > plan["max_phase_seconds"]:
                    raise TimeoutError("Frozen rollout time budget exhausted")
                return evaluate(t, v, candidate, plan)

            def checkpoint(tree):
                (destination / "partial.json").write_text(
                    json.dumps(dict(seed=seed, worlds=worlds, current=tree))
                )

            policies = (
                [policy, "classical_gate"]
                if policy != "classical_gate"
                else ["classical_gate"]
            )
            world = run_world(
                evaluator,
                policies,
                plan["query_budget"],
                plan["query_penalty"],
                checkpoint,
            )
            world.update(
                seed=seed,
                train_rows=len(t),
                validation_rows=len(v),
                train_indices_sha256=hashlib.sha256(ti.tobytes()).hexdigest(),
                validation_indices_sha256=hashlib.sha256(vi.tobytes()).hexdigest(),
                labels=v.target.astype(int).tolist(),
                train_positive=int(t.target.sum()),
                validation_positive=int(v.target.sum()),
            )
            worlds.append(world)
        if (
            sum(w["predictor_fits"] for w in worlds)
            > plan["max_predictor_fits_per_phase"]
            or sum(w["simulated_state_preparations"] for w in worlds)
            > plan["max_simulated_state_preparations_per_phase"]
        ):
            raise ValueError("Frozen physical execution cap exceeded")
        if any(sha(root / file) != digest for file, digest in hashes.items()):
            raise ValueError("Opening recipe changed during execution")
        outcome = dict(
            status="complete",
            intent=intent,
            seeds=worlds,
            seconds=time.perf_counter() - start,
        )
    except Exception as error:
        outcome = dict(
            status="failed",
            intent=intent,
            seeds=worlds,
            seconds=time.perf_counter() - start,
            error_type=type(error).__name__,
        )
        (destination / "outcome.json").write_text(
            json.dumps(outcome, separators=(",", ":")) + "\n"
        )
        raise
    (destination / "outcome.json").write_text(
        json.dumps(outcome, separators=(",", ":")) + "\n"
    )
    return outcome

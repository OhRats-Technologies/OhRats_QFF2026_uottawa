"""Validate saved prospective trees and predictions without refitting or states."""

import hashlib
import json
import math
import subprocess
import numpy as np
import pandas as pd
from wildfire_lab.evaluation import scores, split, sample_indices
from wildfire_lab.evolution_policy import next_action, score
from wildfire_lab.evolution_study import verify_confirmation


def verify_shared(world):
    unique = {}
    for tree in world["trees"]:
        for node in tree["nodes"]:
            name = node["candidate"]
            payload = {
                k: v
                for k, v in node.items()
                if k not in ("id", "parent", "shared_execution")
            }
            if node["shared_execution"] != (name in unique) or (
                name in unique and payload != unique[name]
            ):
                raise ValueError("Shared evaluator copies or execution flags differ")
            unique[name] = payload
    if list(unique) != world["executed_candidates"]:
        raise ValueError("Executed candidate order differs from revealed requests")
    return unique


def verify_world(world, plan):
    target = np.asarray(world["labels"])
    if len(target) != world["validation_rows"] or set(target) != {0, 1}:
        raise ValueError("Saved labels do not match the frozen sample")
    public = []
    for tree in world["trees"]:
        revealed = []
        for node in tree["nodes"]:
            if revealed:
                action = next_action(
                    revealed,
                    tree["policy"],
                    plan["query_budget"],
                    plan["query_penalty"],
                )
                if action != {k: node[k] for k in ("parent", "candidate")}:
                    raise ValueError("Saved decision differs from revealed-only policy")
            elif (
                node["id"] != "root"
                or node["parent"] is not None
                or node["candidate"] != "standard_logistic"
            ):
                raise ValueError("Invalid prospective root")
            prediction = np.asarray(node["predictions"], dtype=float)
            if (
                hashlib.sha256(prediction.tobytes()).hexdigest()
                != node["prediction_sha256"]
            ):
                raise ValueError("Saved prediction bytes changed")
            metric = scores(target, prediction, False)
            if not math.isclose(
                metric["average_precision"], node["ap"], abs_tol=1e-12
            ) or any(
                not math.isclose(metric[k], node["metric"][k], abs_tol=1e-12)
                for k in metric
            ):
                raise ValueError("Saved AP differs from predictions")
            revealed.append(node)
        if (
            next_action(
                revealed, tree["policy"], plan["query_budget"], plan["query_penalty"]
            )
            is not None
        ):
            raise ValueError("Tree stops before its frozen policy")
        if (
            tree["requests"] != len(revealed) - 1
            or not math.isclose(
                tree["reward"], score(revealed, plan["query_penalty"]), abs_tol=1e-12
            )
            or tree["best_ap"] != max(n["ap"] for n in revealed)
        ):
            raise ValueError("Saved query count or reward changed")
        public.append(
            dict(
                policy=tree["policy"],
                requests=tree["requests"],
                best_ap=tree["best_ap"],
                reward=tree["reward"],
                nodes=[
                    {
                        k: v
                        for k, v in n.items()
                        if k not in ("predictions", "prediction_sha256")
                    }
                    for n in revealed
                ],
            )
        )
    return dict(
        seed=world["seed"],
        train_rows=world["train_rows"],
        validation_rows=world["validation_rows"],
        train_positive=world["train_positive"],
        validation_positive=world["validation_positive"],
        train_indices_sha256=world["train_indices_sha256"],
        validation_indices_sha256=world["validation_indices_sha256"],
        trees=public,
        predictor_fits=world["predictor_fits"],
        simulated_state_preparations=world["simulated_state_preparations"],
        measured_candidate_seconds=world["measured_candidate_seconds"],
    )


def collect(root, plan):
    table = root / plan["dataset"] / "features.csv"
    if hashlib.sha256(table.read_bytes()).hexdigest() != plan["dataset_sha256"]:
        raise ValueError("Policy input bytes changed")
    train, valid = split(pd.read_csv(table), plan["fold"], (1988, 2018))
    stages = []
    for stage in ("development", "confirmation"):
        path = root / ".cache/wildfire" / ("policy-evolution-" + stage) / "outcome.json"
        if not path.exists():
            continue
        raw = path.read_bytes()
        saved = json.loads(raw)
        intent = saved["intent"]
        if (
            json.loads(path.with_name("intent.json").read_text()) != intent
            or intent["plan"] != plan
        ):
            raise ValueError("Changed exclusive policy intent")
        if (
            saved["status"] == "complete"
            and [w["seed"] for w in saved["seeds"]] != plan[stage + "_seeds"]
        ):
            raise ValueError("Complete phase has changed reserved seeds")
        for file, digest in intent["recipe_sha256"].items():
            historical = subprocess.check_output(
                ["git", "show", f"{intent['git_commit']}:{file}"], cwd=root
            )
            if hashlib.sha256(historical).hexdigest() != digest:
                raise ValueError("Opening policy recipe not recoverable")
        if stage == "confirmation":
            selected = json.loads(
                subprocess.check_output(
                    [
                        "git",
                        "show",
                        intent["git_commit"]
                        + ":experiments/policy_evolution_selection.json",
                    ],
                    cwd=root,
                )
            )
            parent = root / ".cache/wildfire/policy-evolution-development/outcome.json"
            if (
                hashlib.sha256(parent.read_bytes()).hexdigest()
                != selected["development_outcome_sha256"]
                or selected["selected_policy"] != intent["policy"]
            ):
                raise ValueError("Confirmation selection parent changed")
            verify_confirmation(
                json.loads(parent.read_text()), selected, intent["recipe_sha256"]
            )
        if (
            hashlib.sha256(
                (root / "docs/results/policy-evolution-offline.json").read_bytes()
            ).hexdigest()
            != intent["offline_evidence_sha256"]
        ):
            raise ValueError("Frozen offline selection changed")
        for world in saved["seeds"]:
            ti = sample_indices(len(train), plan["train_cap"], world["seed"])
            vi = sample_indices(len(valid), plan["validation_cap"], world["seed"])
            if (
                hashlib.sha256(ti.tobytes()).hexdigest()
                != world["train_indices_sha256"]
                or hashlib.sha256(vi.tobytes()).hexdigest()
                != world["validation_indices_sha256"]
            ):
                raise ValueError("Fresh sampled rows changed")
            if (
                valid.iloc[vi].target.astype(int).tolist() != world["labels"]
                or len(ti) != world["train_rows"]
                or len(vi) != world["validation_rows"]
            ):
                raise ValueError("Fresh labels or caps changed")
            unique = verify_shared(world)
            if (
                len(unique) != world["predictor_fits"]
                or sum(n["simulated_state_preparations"] for n in unique.values())
                != world["simulated_state_preparations"]
            ):
                raise ValueError("Shared evaluator cost is double counted")
        worlds = [verify_world(w, plan) for w in saved["seeds"]]
        if (
            sum(w["predictor_fits"] for w in worlds)
            > plan["max_predictor_fits_per_phase"]
            or sum(w["simulated_state_preparations"] for w in worlds)
            > plan["max_simulated_state_preparations_per_phase"]
        ):
            raise ValueError("Saved execution exceeds phase caps")
        policies = sorted({t["policy"] for w in worlds for t in w["trees"]})
        means = {
            p: {
                k: float(
                    np.mean(
                        [t[k] for w in worlds for t in w["trees"] if t["policy"] == p]
                    )
                )
                for k in ("requests", "best_ap", "reward")
            }
            for p in policies
        }
        stages.append(
            dict(
                stage=stage,
                status=saved["status"],
                outcome_sha256=hashlib.sha256(raw).hexdigest(),
                opening_commit=intent["git_commit"],
                recipe_sha256=intent["recipe_sha256"],
                runner_seconds=saved["seconds"],
                means=means,
                seeds=worlds,
                predictor_fits=sum(w["predictor_fits"] for w in worlds),
                simulated_state_preparations=sum(
                    w["simulated_state_preparations"] for w in worlds
                ),
            )
        )
    if not stages:
        raise FileNotFoundError(
            "No saved policy rollout outcomes; collection cannot create evidence"
        )
    return dict(
        status="audited_policy_evolution",
        plan=plan,
        stages=stages,
        audit_predictor_fits=0,
        audit_state_preparations=0,
        pair_circuits=0,
        shots=0,
        hardware_jobs_submitted=0,
        final_test_access=False,
        limitations="Independent Codex policy-code revision and fresh configuration rollouts. Fixed generator, not full LLM program discovery. Shared evaluator results avoid duplicate fits while query costs charge each policy. Fresh row seeds reuse the same years; no independent temporal validation or final-model change.",
    )

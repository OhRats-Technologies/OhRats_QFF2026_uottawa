"""Offline policy-code evaluation over measured flat history, never invented edges."""

import hashlib
import json
from collections import defaultdict
from wildfire_lab.evolution_policy import next_action, score


def replay_history(root, plan, policies=("classical_gate", "evolved_v1")):
    paths = list(
        (root / ".cache/wildfire/experiments").glob(
            "*/" + plan["history_attempt"] + "-outcome.json"
        )
    )
    (path,) = paths
    raw = path.read_bytes()
    if hashlib.sha256(raw).hexdigest() != plan["history_sha256"]:
        raise ValueError("Policy development history changed")
    panels = defaultdict(dict)
    for row in json.loads(raw)["rows"]:
        if row["fold"][-1] <= 2014:
            if (
                row["features"] != plan["features"]
                or row["train_rows"] != 256
                or row["validation_rows"] != 512
            ):
                raise ValueError("Historical candidate inputs or label budgets changed")
            panels[(tuple(row["fold"]), row["seed"])][row["predictor"]] = row["metric"][
                "average_precision"
            ]
    if len(panels) != 6:
        raise ValueError("Expected six historical development panels")
    rows = []
    for (fold, seed), panel in sorted(panels.items()):
        for policy in policies:
            revealed = [
                dict(
                    id="root",
                    parent=None,
                    candidate="standard_logistic",
                    ap=panel["standard_logistic"],
                )
            ]
            while (
                action := next_action(
                    revealed, policy, plan["query_budget"], plan["query_penalty"]
                )
            ) is not None:
                if action["candidate"] not in panel:
                    raise ValueError(
                        "Replay has no recorded outcome for requested candidate"
                    )
                revealed.append(
                    dict(
                        id=f"node-{len(revealed)}",
                        ap=panel[action["candidate"]],
                        **action,
                    )
                )
            rows.append(
                dict(
                    fold=list(fold),
                    seed=seed,
                    policy=policy,
                    trace=[n["candidate"] for n in revealed[1:]],
                    requests=len(revealed) - 1,
                    best_ap=max(n["ap"] for n in revealed),
                    reward=score(revealed, plan["query_penalty"]),
                )
            )
    means = {
        p: {
            k: sum(r[k] for r in rows if r["policy"] == p) / len(panels)
            for k in ("best_ap", "requests", "reward")
        }
        for p in policies
    }
    chosen = max(policies, key=lambda p: (means[p]["reward"], -means[p]["requests"]))
    return dict(
        status="offline_code_revision_evaluated",
        source_sha256=plan["history_sha256"],
        rows=rows,
        means=means,
        selected_policy=chosen,
        historical_topology="Flat panels; decision traces do not create historical ancestry.",
        online_model_evaluations=0,
    )

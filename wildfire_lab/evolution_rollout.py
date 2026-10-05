"""Prospective query trees: policies see revealed nodes, evaluator owns outcomes."""

from wildfire_lab.evolution_policy import next_action, score


def run_world(evaluator, policies, budget=3, penalty=0.005, checkpoint=lambda _: None):
    cache = {}

    def request(candidate):
        reused = candidate in cache
        if not reused:
            cache[candidate] = evaluator(candidate)
        return dict(cache[candidate], shared_execution=reused)

    root = dict(request("standard_logistic"), id="root", parent=None)
    trees = []
    for position, policy in enumerate(policies):
        tree = [dict(root, shared_execution=position > 0)]
        while (action := next_action(tree, policy, budget, penalty)) is not None:
            children = {node["parent"] for node in tree[1:]}
            eligible = {"root"} | {
                node["id"] for node in tree if node["id"] not in children
            }
            if action["parent"] not in eligible or action["candidate"] in {
                n["candidate"] for n in tree
            }:
                raise ValueError(
                    "Policy requested an ineligible parent or duplicate candidate"
                )
            if len(tree) - 1 >= budget:
                raise ValueError("Policy exceeded its frozen budget")
            node = dict(
                request(action["candidate"]),
                id=f"node-{len(tree)}",
                parent=action["parent"],
            )
            tree.append(node)
            checkpoint(dict(policy=policy, nodes=tree))
        trees.append(
            dict(
                policy=policy,
                nodes=tree,
                requests=len(tree) - 1,
                best_ap=max(n["ap"] for n in tree),
                reward=score(tree, penalty),
            )
        )
    return dict(
        trees=trees,
        executed_candidates=list(cache),
        predictor_fits=sum(n.get("predictor_fits", 0) for n in cache.values()),
        simulated_state_preparations=sum(
            n.get("simulated_state_preparations", 0) for n in cache.values()
        ),
        measured_candidate_seconds=sum(n.get("seconds", 0) for n in cache.values()),
    )

"""Versioned exploration policies over revealed controlled-configuration trees.

The evaluator owns data, candidate generation, execution and tree validation.
This module receives no panel of future scores. Historical flat panels do not
gain ancestry by replaying these decisions; only live expansion creates edges.
"""

BASELINE_VERSION = "classical_gate"
EVOLVED_VERSION = "evolved_v1"
ROOT_CANDIDATE = "standard_logistic"
RBF_ROBUST = "robust_tanh/rbf"
RBF_STANDARD = "standard_tanh/rbf"
ZZ_ROBUST = "robust_tanh/qiskit_ZZ"


def next_action(tree, policy, budget=3, penalty=0.005):
    """Return the next leaf mutation or stop, using revealed scores only.

    Baseline preserves the historical gate's order and two-query stop rule.
    V1 stops after the first RBF probe unless its AP gain exceeds the fixed
    per-query penalty, then probes the alternative RBF preprocessing and stops.
    The second action preserves the kernel while mutating preprocessing.
    """
    if policy not in (BASELINE_VERSION, EVOLVED_VERSION):
        raise ValueError(f"Unknown exploration policy: {policy}")
    queries = len(tree) - 1
    if queries >= budget:
        return None
    observed = {node["candidate"]: node["ap"] for node in tree}
    root_ap = observed[ROOT_CANDIDATE]
    if policy == BASELINE_VERSION:
        order = (RBF_ROBUST, RBF_STANDARD, ZZ_ROBUST)
        if queries >= len(order):
            return None
        if queries == 2 and max(observed.values()) <= root_ap:
            return None
        candidate = order[queries]
    else:
        if queries == 0:
            candidate = RBF_ROBUST
        elif queries == 1 and observed[RBF_ROBUST] - root_ap > penalty:
            candidate = RBF_STANDARD
        else:
            return None
    return {"parent": tree[-1]["id"], "candidate": candidate}


def score(tree, penalty=0.005):
    """Fixed reward: best revealed AP less the non-root query charge."""
    return max(node["ap"] for node in tree) - penalty * (len(tree) - 1)

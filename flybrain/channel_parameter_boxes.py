"""Certified joint sensitivity to count errors and coherence-retention intervals."""

from fractions import Fraction as F
import hashlib
import json
from pathlib import Path

import numpy as np

from .channel_certificates import (
    phase_certificate,
    profile,
    exact_certificate,
    analytic_choi,
)
from .channel_robustness import SCALE, transition_box, power_bound
from .data import load_graph


def joint_box(weights, epsilon, gamma_lower, gamma_upper, scale=SCALE):
    gl, gu = F(gamma_lower), F(gamma_upper)
    if not 0 < gl <= gu < 1:
        raise ValueError("0<gamma_lower<=gamma_upper<1 required")
    Ll, Ul = transition_box(weights, epsilon, gl, scale)
    Lu, Uu = transition_box(weights, epsilon, gu, scale)
    n = len(Ll)
    # Diagonals increase with gamma; off-diagonals decrease with gamma.
    lower = [[Ll[i][j] if i == j else Lu[i][j] for j in range(n)] for i in range(n)]
    upper = [[Uu[i][j] if i == j else Ul[i][j] for j in range(n)] for i in range(n)]
    return lower, upper


def verify_joint(weights, epsilon, gamma_lower, gamma_upper, v, r=7, scale=SCALE):
    if not isinstance(r, int) or r < 2:
        raise ValueError("r>=2 required")
    L, U = joint_box(weights, epsilon, gamma_lower, gamma_upper, scale)
    n = len(L)
    gl, gu = F(gamma_lower), F(gamma_upper)
    scales = [F(str(x)) for x in v]
    if len(scales) != n or min(scales) <= 0:
        raise ValueError("Positive rational scales required")
    Lr = power_bound(L, r, scale)
    Ur = power_bound(U, r, scale, True)
    Uprevious = power_bound(U, r - 1, scale, True)
    minimum = min(
        F(Lr[i][j], scale) - gu**r * scales[i] / scales[j]
        for i in range(n)
        for j in range(n)
    )
    witness = None
    for i in range(n):
        for j in range(i + 1, n):
            det = F(Uprevious[i][j] * Uprevious[j][i], scale**2) - gl ** (2 * (r - 1))
            if det < 0:
                witness = dict(
                    pair=[i, j], step=r - 1, upper_determinant_rational=str(det)
                )
                break
        if witness:
            break
    tau, i, k = max(
        (sum(max(Lr[i][j] - Ur[k][j], 0) for j in range(n)), i, k)
        for i in range(n)
        for k in range(n)
    )
    return dict(
        epsilon_rational=str(F(epsilon)),
        gamma_lower_rational=str(gl),
        gamma_upper_rational=str(gu),
        r=r,
        scale=scale,
        v_rational=[str(x) for x in scales],
        minimum_residual_lower_rational=str(minimum),
        previous_npt_uniform_witness=witness,
        separability_for_entire_box=minimum >= 0,
        exact_eb_index_for_entire_box=r if minimum >= 0 and witness else None,
        population_dobrushin_uniform_lower_rational=str(F(tau, scale)),
        population_witness_pair=[i, k],
        transition_lower_integer=L,
        transition_upper_integer=U,
        powered_lower_integer=Lr,
        powered_upper_integer=Ur,
        previous_powered_upper_integer=Uprevious,
    )


def run(weights):
    W = np.asarray(weights)
    n = len(W)
    records = []
    for epsilon in ["0", ".0025", ".005", ".01"]:
        for width in ["0", ".0001", ".0005", ".001", ".002", ".005", ".01"]:
            gl = F("3/5") - F(width)
            gu = F("3/5") + F(width)
            L, _ = joint_box(W, epsilon, gl, gu)
            Lr = power_bound(L, 7)
            candidate = phase_certificate(np.array(Lr, float) / SCALE, float(gu**7))
            item = verify_joint(
                W, epsilon, gl, gu, candidate["v"] if candidate else np.ones(n)
            )
            item["scale_search_found_candidate"] = candidate is not None
            records.append(item)
    point_certificates = []
    P = W / W.sum(1, keepdims=True)
    for gamma in [".58", ".59", ".6", ".61", ".62"]:
        bounds = profile(P, float(gamma))
        r = bounds["constructive_eb_upper_bound"]
        if r is None:
            continue
        _, B, c = analytic_choi(P, float(gamma), r)
        candidate = phase_certificate(B, c)
        if candidate is None:
            continue
        proof = exact_certificate(W, gamma, r, candidate["v"])
        point_certificates.append(proof)
    return dict(
        adjacency_integer=W.astype(int).tolist(),
        scope="Exploratory conditional model sensitivity: independent multiplicative count boxes and static gamma intervals, not inferred biological/hardware parameters.",
        records=records,
        point_certificates=point_certificates,
    )


def main():
    nodes, W, provenance = load_graph()
    data = run(W)
    data.update(nodes=nodes, dataset_source_commit=provenance["source_commit"])
    output = Path("artifacts/channel-parameter-boxes-20261003")
    output.mkdir(exist_ok=True)
    (output / "results.json").write_text(json.dumps(data, indent=2) + "\n")
    sources = [
        "flybrain/channel_parameter_boxes.py",
        "flybrain/channel_robustness.py",
        "flybrain/channel_certificates.py",
    ]
    manifest = dict(
        files_sha256={
            "results.json": hashlib.sha256(
                (output / "results.json").read_bytes()
            ).hexdigest()
        },
        source_sha256={
            p: hashlib.sha256(Path(p).read_bytes()).hexdigest() for p in sources
        },
    )
    (output / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    for e in ["0", "1/400", "1/200", "1/100"]:
        selected = [
            x
            for x in data["records"]
            if x["epsilon_rational"] == e and x["exact_eb_index_for_entire_box"] == 7
        ]
        print(
            "count epsilon",
            e,
            "largest certified grid gamma half-width:",
            max(
                (F(x["gamma_upper_rational"]) - F("3/5") for x in selected),
                default=None,
            ),
        )
    for proof in data["point_certificates"]:
        print(
            "point gamma", proof["gamma_rational"], "exact EB", proof["exact_eb_index"]
        )


if __name__ == "__main__":
    main()

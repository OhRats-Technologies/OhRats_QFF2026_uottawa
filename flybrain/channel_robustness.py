"""Outward-rounded rational certificates over independent synapse-count boxes.

An assumed error box is a sensitivity model, not a data-derived confidence set.
"""

from fractions import Fraction as F
import hashlib
import json
from pathlib import Path

import numpy as np

from .channel_certificates import phase_certificate
from .data import load_graph

SCALE = 10**12


def rounded(value, scale, upward=False):
    value = F(value)
    numerator = value.numerator * scale
    return (
        -(-numerator // value.denominator) if upward else numerator // value.denominator
    )


def transition_box(weights, epsilon, gamma="3/5", scale=SCALE):
    W = np.asarray(weights)
    if W.ndim != 2 or W.shape[0] != W.shape[1] or len(W) < 2:
        raise ValueError("Square adjacency of dimension >=2 required")
    if (
        not np.isfinite(W).all()
        or (W < 0).any()
        or not np.equal(W, np.floor(W)).all()
        or (W.sum(1) <= 0).any()
    ):
        raise ValueError("Nonnegative integer weights and positive row sums required")
    e = F(epsilon)
    g = F(gamma)
    if not 0 <= e < 1 or not 0 < g < 1 or not isinstance(scale, int) or scale < 1:
        raise ValueError("0<=epsilon<1, 0<gamma<1, positive integer scale required")
    lower = []
    upper = []
    for i, row in enumerate(W):
        total = int(row.sum())
        lo = []
        hi = []
        for j, weight in enumerate(row):
            w = int(weight)
            p_lo = (1 - e) * w / ((1 - e) * w + (1 + e) * (total - w))
            p_hi = (1 + e) * w / ((1 + e) * w + (1 - e) * (total - w))
            lo.append(rounded((g if i == j else 0) + (1 - g) * p_lo, scale))
            hi.append(rounded((g if i == j else 0) + (1 - g) * p_hi, scale, True))
        lower.append(lo)
        upper.append(hi)
    return lower, upper


def power_bound(matrix, r, scale=SCALE, upward=False):
    """Nonnegative fixed-point powers, rounding outward after every product."""
    if not isinstance(r, int) or r < 1 or not isinstance(scale, int) or scale < 1:
        raise ValueError("Positive integer power and scale required")
    n = len(matrix)
    if n < 2 or any(
        len(row) != n or any(not isinstance(x, int) or x < 0 for x in row)
        for row in matrix
    ):
        raise ValueError("Nonnegative square integer fixed-point matrix required")
    result = [[scale * int(i == j) for j in range(n)] for i in range(n)]
    for _ in range(r):
        product = [
            [sum(result[i][k] * matrix[k][j] for k in range(n)) for j in range(n)]
            for i in range(n)
        ]
        result = [
            [(-(-x // scale) if upward else x // scale) for x in row] for row in product
        ]
    return result


def verify(weights, epsilon, v, gamma="3/5", r=7, scale=SCALE):
    """Verify a fixed scale vector over the full count box using integer bounds."""
    if not isinstance(r, int) or r < 2:
        raise ValueError("r>=2 required")
    L, U = transition_box(weights, epsilon, gamma, scale)
    n = len(L)
    scales = [F(str(x)) for x in v]
    if len(scales) != n or min(scales) <= 0:
        raise ValueError("Positive rational scale vector required")
    Lr = power_bound(L, r, scale)
    Ur = power_bound(U, r, scale, True)
    Uprevious = power_bound(U, r - 1, scale, True)
    g = F(gamma)
    c = g**r
    residue = min(
        F(Lr[i][j], scale) - c * scales[i] / scales[j]
        for i in range(n)
        for j in range(n)
    )
    witness = None
    for i in range(n):
        for j in range(i + 1, n):
            determinant = F(Uprevious[i][j] * Uprevious[j][i], scale**2) - g ** (
                2 * (r - 1)
            )
            if determinant < 0:
                witness = dict(
                    pair=[i, j], step=r - 1, upper_determinant_rational=str(determinant)
                )
                break
        if witness:
            break
    pair_bounds = [
        (sum(max(Lr[i][j] - Ur[k][j], 0) for j in range(n)), i, k)
        for i in range(n)
        for k in range(n)
    ]
    value, i, k = max(pair_bounds)
    return dict(
        epsilon_rational=str(F(epsilon)),
        gamma_rational=str(g),
        r=r,
        scale=scale,
        v_rational=[str(x) for x in scales],
        minimum_residual_lower_rational=str(residue),
        previous_npt_uniform_witness=witness,
        separability_for_entire_box=residue >= 0,
        exact_eb_index_for_entire_box=r if residue >= 0 and witness else None,
        population_dobrushin_uniform_lower_rational=str(F(value, scale)),
        population_witness_pair=[i, k],
        transition_lower_integer=L,
        transition_upper_integer=U,
        powered_lower_integer=Lr,
        powered_upper_integer=Ur,
        previous_powered_upper_integer=Uprevious,
    )


def run(weights):
    records = []
    for epsilon in [
        "0",
        ".001",
        ".002",
        ".005",
        ".01",
        ".012",
        ".015",
        ".02",
        ".05",
        ".1",
        ".15",
        ".2",
    ]:
        L, _ = transition_box(weights, epsilon)
        L7 = power_bound(L, 7)
        certificate = phase_certificate(np.array(L7, float) / SCALE, (0.6) ** 7)
        v = certificate["v"] if certificate else np.ones(len(L))
        result = verify(weights, epsilon, v)
        result["scale_search_found_candidate"] = certificate is not None
        records.append(result)
    return dict(
        adjacency_integer=np.asarray(weights, dtype=int).tolist(),
        scope="Conditional sensitivity to independent real-valued multiplicative changes in every supplied integer count, fixed gamma=3/5; not empirical error bars or biological quantum evidence.",
        epsilon_grid_preregistered=False,
        records=records,
    )


def main():
    nodes, W, provenance = load_graph()
    result = run(W)
    result.update(nodes=nodes, dataset_source_commit=provenance["source_commit"])
    output = Path("artifacts/channel-robustness-20261003")
    output.mkdir(exist_ok=True)
    (output / "results.json").write_text(json.dumps(result, indent=2) + "\n")
    sources = ["flybrain/channel_robustness.py", "flybrain/channel_certificates.py"]
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
    for item in result["records"]:
        print(
            "epsilon",
            item["epsilon_rational"],
            "uniform exact EB",
            item["exact_eb_index_for_entire_box"],
            "NPT lower witness",
            item["previous_npt_uniform_witness"] is not None,
            "Dobrushin lower",
            float(F(item["population_dobrushin_uniform_lower_rational"])),
        )


if __name__ == "__main__":
    main()

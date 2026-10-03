"""Exact rational isospectral controls for identity-retention quantum channels.

These are synthetic symmetric Markov chains, not additional connectome samples.
"""

from fractions import Fraction as F
import hashlib
import json
from math import lcm
from pathlib import Path

import numpy as np
from scipy.linalg import hadamard

from .channel_certificates import (
    analytic_choi,
    exact_certificate,
    phase_certificate,
    profile,
)


def transpose(A):
    return list(map(list, zip(*A)))


def multiply(A, B):
    return [[sum(x * y for x, y in zip(row, col)) for col in zip(*B)] for row in A]


def identity(n):
    return [[F(int(i == j)) for j in range(n)] for i in range(n)]


def reflection(vector):
    """A rational orthogonal matrix fixing ones for a zero-sum integer vector."""
    v = [F(int(x)) for x in vector]
    if sum(v) != 0 or not any(v):
        raise ValueError("Nonzero zero-sum integer vector required")
    norm = sum(x * x for x in v)
    return [
        [F(int(i == j)) - 2 * v[i] * v[j] / norm for j in range(len(v))]
        for i in range(len(v))
    ]


def seed_chain(n):
    spectra = {
        4: ["1", ".75", ".15", ".05"],
        8: ["1", ".75", ".15", ".1", ".08", ".06", ".04", ".02"],
    }
    if n not in spectra:
        raise ValueError("Only registered four/eight-state controls are supported")
    eigenvalues = list(map(F, spectra[n]))
    H = hadamard(n).tolist()
    P = [
        [
            sum(F(H[i][k] * H[j][k]) * eigenvalues[k] for k in range(n)) / n
            for j in range(n)
        ]
        for i in range(n)
    ]
    return P, eigenvalues


def integer_weights(P):
    """Clear rational row denominators without changing transition probabilities."""
    W = []
    for row in P:
        if min(row) < 0 or sum(row) != 1:
            raise ValueError("Nonnegative exactly stochastic chain required")
        denominator = lcm(*(x.denominator for x in row))
        W.append([int(x * denominator) for x in row])
    if max(x for row in W for x in row) > 2**50:
        raise ValueError("Weights exceed conservative exact float-integer range")
    return np.array(W, dtype=np.int64)


def summarize(P):
    floating = np.array(P, dtype=float)
    result = profile(floating, 0.6, 30)
    return {
        key: result[key]
        for key in ["npt_based_eb_lower_bound", "constructive_eb_upper_bound"]
    }


def run(samples=150, seed=76031):
    if not isinstance(samples, int) or samples < 1:
        raise ValueError("Positive sample count required")
    rng = np.random.default_rng(seed)
    groups = []
    certificates = []
    for n in [4, 8]:
        original, eigenvalues = seed_chain(n)
        baseline = summarize(original)
        accepted = [dict(sample=-1, vector=None, **baseline)]
        excluded = []
        representatives = {
            (
                baseline["npt_based_eb_lower_bound"],
                baseline["constructive_eb_upper_bound"],
            ): (original, identity(n), None, -1)
        }
        max_spectral_error = 0.0
        for sample in range(samples):
            raw = rng.integers(-3, 4, size=n)
            v = n * raw - raw.sum()
            if not np.any(v):
                excluded.append(dict(sample=sample, reason="Zero reflection vector"))
                continue
            O = reflection(v)
            Q = multiply(multiply(O, original), transpose(O))
            assert multiply(transpose(O), O) == identity(n)
            assert all(sum(row) == 1 for row in O)
            assert Q == transpose(Q) and all(sum(row) == 1 for row in Q)
            minimum = min(x for row in Q for x in row)
            if minimum <= 0:
                excluded.append(
                    dict(
                        sample=sample,
                        reason="Nonpositive transition entry",
                        minimum_rational=str(minimum),
                    )
                )
                continue
            floating = np.array(Q, dtype=float)
            error = float(
                np.max(
                    np.abs(
                        np.linalg.eigvalsh(floating)
                        - np.sort(np.array(eigenvalues, dtype=float))
                    )
                )
            )
            max_spectral_error = max(max_spectral_error, error)
            bounds = summarize(Q)
            accepted.append(dict(sample=sample, vector=v.tolist(), **bounds))
            key = (
                bounds["npt_based_eb_lower_bound"],
                bounds["constructive_eb_upper_bound"],
            )
            representatives.setdefault(key, (Q, O, v.tolist(), sample))
        for (lower, upper), (Q, O, v, sample) in representatives.items():
            if upper is None or lower != upper:
                continue
            W = integer_weights(Q)
            _, B, c = analytic_choi(np.array(Q, dtype=float), 0.6, upper)
            certificate = phase_certificate(B, c)
            if certificate is None:
                continue
            proof = exact_certificate(W, "0.6", upper, certificate["v"])
            assert proof["exact_eb_index"] == upper
            certificates.append(
                dict(
                    dimension=n,
                    sample=sample,
                    reflection_vector=v,
                    orthogonal_matrix_rational=[[str(x) for x in row] for row in O],
                    seed_transition_rational=[
                        [str(x) for x in row] for row in original
                    ],
                    transformed_transition_rational=[
                        [str(x) for x in row] for row in Q
                    ],
                    certificate=proof,
                )
            )
        groups.append(
            dict(
                dimension=n,
                spectrum_rational=[str(x) for x in eigenvalues],
                classical_spectral_gap_rational="1/4",
                gamma_rational="3/5",
                stationary_distribution_rational=[str(F(1, n))] * n,
                accepted=accepted,
                excluded=excluded,
                max_numerical_spectral_error=max_spectral_error,
                distinct_eb_intervals=[
                    list(x)
                    for x in sorted(representatives, key=lambda x: (x[0], x[1] or 999))
                ],
            )
        )
    return dict(
        seed=seed,
        attempts_per_dimension=samples,
        scope="Exploratory synthetic positive symmetric controls, not biological samples or a novelty claim.",
        groups=groups,
    ), certificates


def main():
    output = Path("artifacts/isospectral-controls-20261003")
    output.mkdir(exist_ok=True)
    results, proofs = run()
    for name, data in [
        ("results.json", results),
        ("exact-representatives.json", proofs),
    ]:
        (output / name).write_text(json.dumps(data, indent=2) + "\n")
    manifest = {
        "files_sha256": {
            p.name: hashlib.sha256(p.read_bytes()).hexdigest()
            for p in output.glob("*.json")
            if p.name != "manifest.json"
        },
        "source_sha256": {
            p: hashlib.sha256(Path(p).read_bytes()).hexdigest()
            for p in [
                "flybrain/isospectral_controls.py",
                "flybrain/channel_certificates.py",
            ]
        },
    }
    (output / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    for group in results["groups"]:
        print(
            group["dimension"],
            "states:",
            len(group["accepted"]),
            "positive controls incl. baseline;",
            len(group["excluded"]),
            "excluded; EB intervals:",
            group["distinct_eb_intervals"],
        )
    print("Exact representative certificates:", len(proofs))


if __name__ == "__main__":
    main()

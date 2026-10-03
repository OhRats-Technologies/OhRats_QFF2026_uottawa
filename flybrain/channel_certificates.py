"""NPT lower bounds and constructive EB upper bounds for gamma I+(1-gamma)D_P.

Finite phase twirls and pairwise decompositions supply sufficient separability tests.
Only the identity-retention channel is covered; Hamiltonian mixtures are excluded.
"""

import json
import itertools
from fractions import Fraction
from pathlib import Path
import numpy as np
from scipy.optimize import linprog
from .data import load_graph


def validate(P, gamma, r):
    P = np.asarray(P, dtype=float)
    if P.ndim != 2 or P.shape[0] != P.shape[1] or len(P) < 2:
        raise ValueError("Square transition matrix required")
    if (
        not np.isfinite(P).all()
        or (P < 0).any()
        or not np.allclose(P.sum(1), 1, atol=1e-12, rtol=0)
    ):
        raise ValueError("Finite nonnegative row-stochastic matrix required")
    if not np.isfinite(gamma) or not 0 <= gamma <= 1 or not isinstance(r, int) or r < 1:
        raise ValueError("gamma in [0,1] and integer r>=1 required")
    return P


def analytic_choi(P, gamma, r):
    P = validate(P, gamma, r)
    n = len(P)
    B = np.linalg.matrix_power(gamma * np.eye(n) + (1 - gamma) * P, r)
    c = gamma**r
    J = np.diag(B.reshape(-1)).astype(complex) / n
    for i in range(n):
        for j in range(n):
            if i != j:
                J[i * n + i, j * n + j] = c / n
    return J, B, c


def ppt_min_eigenvalue(B, c):
    n = len(B)
    values = [float(B[i, i]) / n for i in range(n)]
    for i in range(n):
        for j in range(i + 1, n):
            x, y = B[i, j], B[j, i]
            values.append(float((x + y - np.hypot(x - y, 2 * c)) / (2 * n)))
    return min(values)


def product_certificate(B, c, tolerance=1e-12):
    """Return explicit unnormalized product vectors and nonnegative diagonal residue.

    For every i<j allocate c to ii and jj; allocate x=c sqrt(Bij/Bji),
    y=c sqrt(Bji/Bij) to ij and ji. xy=c^2. Four opposite phase rotations
    kill unwanted coherences while retaining |ii><jj|. All remaining entries
    must be nonnegative. tolerance is a positive safety margin, not clipping.
    """
    n = len(B)
    if c == 0:
        return {"terms": [], "residual": B.copy(), "minimum_residual": float(B.min())}
    residual = B.copy()
    terms = []
    for i in range(n):
        for j in range(i + 1, n):
            if B[i, j] <= 0 or B[j, i] <= 0:
                return None
            x = c * np.sqrt(B[i, j] / B[j, i])
            y = c * np.sqrt(B[j, i] / B[i, j])
            residual[i, j] -= x
            residual[j, i] -= y
            residual[i, i] -= c
            residual[j, j] -= c
            for k in range(4):
                phase = np.exp(1j * np.pi * k / 2)
                a = np.zeros(n, complex)
                b = np.zeros(n, complex)
                a[i] = np.sqrt(c)
                a[j] = np.sqrt(y) * phase
                b[i] = 1
                b[j] = np.sqrt(x / c) * phase.conjugate()
                terms.append((a, b, 1 / (4 * n)))
    if residual.min() < tolerance:
        return None
    return {
        "terms": terms,
        "residual": residual,
        "minimum_residual": float(residual.min()),
    }


def phase_certificate(B, c, tolerance=1e-12):
    """Finite 3-phase product twirl, with a directly checked positive residue.

    Find positive v with c*v_i/v_j < B_ij for i != j. A three-phase twirl
    of a_i=sqrt(v_i), b_i=sqrt(c/v_i) has all ii,jj coherences c and
    populations c*v_i/v_j. Subtracting it leaves diagonal product states.
    Optimize common logarithmic slack, then check every entry explicitly;
    solver success alone is never accepted as a separability certificate.
    """
    n = len(B)
    if c == 0 or (B <= 0).any():
        return None
    inequalities = []
    bounds = []
    for i in range(n):
        for j in range(n):
            if i == j:
                continue
            row = np.zeros(n + 1)
            row[i], row[j], row[-1] = 1, -1, 1
            inequalities.append(row)
            bounds.append(np.log(B[i, j] / c))
    objective = np.zeros(n + 1)
    objective[-1] = -1
    solution = linprog(
        objective,
        A_ub=inequalities,
        b_ub=bounds,
        bounds=[(None, None)] * (n + 1),
        method="highs",
    )
    if not solution.success:
        return None
    logarithms = solution.x[:-1] - solution.x[:-1].mean()
    v = np.exp(logarithms)
    residue = B - c * v[:, None] / v[None, :]
    if not np.isfinite(residue).all() or residue.min() < tolerance:
        return None
    return {
        "kind": "phase_twirl",
        "v": v,
        "c": c,
        "residual": residue,
        "minimum_residual": float(residue.min()),
        "log_ratio_slack": float(solution.x[-1]),
    }


def phase_terms(cert):
    """Generate the complete finite mixture; no Monte Carlo phase sampling."""
    n = len(cert["v"])
    for indices in itertools.product(range(3), repeat=n):
        phase = np.exp(2j * np.pi * np.asarray(indices) / 3)
        a = np.sqrt(cert["v"]) * phase
        b = np.sqrt(cert["c"] / cert["v"]) * phase.conjugate()
        yield a, b, 1 / (n * 3**n)


def reconstruct(cert):
    residual = cert["residual"]
    n = len(residual)
    result = np.diag(residual.reshape(-1)).astype(complex) / n
    terms = phase_terms(cert) if cert.get("kind") == "phase_twirl" else cert["terms"]
    for a, b, weight in terms:
        v = np.kron(a, b)
        result += weight * np.outer(v, v.conj())
    return result


def profile(P, gamma, limit=80):
    rows = []
    first_ppt = None
    first_cert = None
    last_npt = 0
    for r in range(1, limit + 1):
        J, B, c = analytic_choi(P, gamma, r)
        minimum = ppt_min_eigenvalue(B, c)
        if minimum < -1e-10:
            last_npt = r
        if minimum > 1e-10 and first_ppt is None:
            first_ppt = r
        cert = phase_certificate(B, c) or product_certificate(B, c)
        if cert is not None and first_cert is None:
            error = float(np.max(np.abs(reconstruct(cert) - J)))
            assert error < 1e-10
            first_cert = r
        tau = float(np.max(np.sum(np.abs(B[:, None, :] - B[None, :, :]), axis=2)) / 2)
        rows.append(
            {
                "r": r,
                "ppt_min_eigenvalue": minimum,
                "population_dobrushin": tau,
                "constructive_separable": cert is not None,
                "certificate_kind": cert.get("kind", "pairwise") if cert else None,
                "minimum_residual": cert["minimum_residual"] if cert else None,
            }
        )
        if first_cert is not None:
            break
    return {
        "gamma": gamma,
        "npt_based_eb_lower_bound": last_npt + 1,
        "first_strict_ppt_step": first_ppt,
        "constructive_eb_upper_bound": first_cert,
        "steps": rows,
        "scope": "Identity retention plus measured-and-prepared Markov channel only; finite-precision margins, not interval arithmetic.",
    }


def exact_certificate(adjacency, gamma, r, v):
    """Check the twirl residual and preceding NPT determinant in rational arithmetic.

    Integer synapse counts define exact row-normalized probabilities. Positive
    rational v need not be the exact solver output: it merely supplies a valid
    algebraic product mixture. Gamma is a decimal string, never a binary float.
    """
    W = np.asarray(adjacency)
    if W.ndim != 2 or W.shape[0] != W.shape[1] or not np.isfinite(W).all():
        raise ValueError("Square finite integer adjacency required")
    if (W < 0).any() or not np.equal(W, np.floor(W)).all() or (W.sum(1) <= 0).any():
        raise ValueError("Nonnegative integer weights with positive row sums required")
    n = len(W)
    g = Fraction(gamma)
    if not 0 < g < 1 or not isinstance(r, int) or r < 2:
        raise ValueError("Exact certificate requires 0<gamma<1 and r>=2")
    scales = [Fraction(str(x)) for x in v]
    if len(scales) != n or min(scales) <= 0:
        raise ValueError("Positive rational scales required")
    M = [
        [
            (g if i == j else 0) + (1 - g) * Fraction(int(W[i, j]), int(W[i].sum()))
            for j in range(n)
        ]
        for i in range(n)
    ]
    B = [[Fraction(int(i == j)) for j in range(n)] for i in range(n)]
    previous = None
    for _ in range(r):
        previous = B
        B = [
            [sum(B[i][k] * M[k][j] for k in range(n)) for j in range(n)]
            for i in range(n)
        ]
    c = g**r
    residue = [
        [B[i][j] - c * scales[i] / scales[j] for j in range(n)] for i in range(n)
    ]
    if min(x for row in residue for x in row) < 0:
        raise ValueError("Exact negative residue: no valid product mixture")
    witness = None
    for i in range(n):
        for j in range(i + 1, n):
            determinant = previous[i][j] * previous[j][i] - g ** (2 * (r - 1))
            if determinant < 0:
                witness = {
                    "pair": [i, j],
                    "step": r - 1,
                    "unscaled_pt_block_determinant": str(determinant),
                }
                break
        if witness:
            break
    return {
        "gamma_rational": str(g),
        "r": r,
        "v_rational": [str(x) for x in scales],
        "adjacency_integer": W.astype(int).tolist(),
        "minimum_residual_rational": str(min(x for row in residue for x in row)),
        "previous_step_npt_witness": witness,
        "exact_eb_index": r if witness else None,
        "scope": "Exact rational-arithmetic certificate for the specified ideal mathematical channel; not hardware or full-CNS evidence.",
    }


def main():
    import hashlib

    nodes, A, provenance = load_graph()
    P = A / A.sum(axis=1, keepdims=True)
    n = len(P)
    exact_weights = {"fly": A, "uniform_reset": np.ones((n, n), dtype=int)}
    distributions = {"fly": P, "uniform_reset": np.full((n, n), 1 / n)}
    stationary = np.full(n, 1 / n)
    for _ in range(10000):
        nxt = stationary @ P
        if np.max(np.abs(nxt - stationary)) < 1e-14:
            break
        stationary = nxt
    distributions["stationary_reset"] = np.tile(stationary, (n, 1))
    excluded = []
    for threshold in [1000, 5000]:
        W = np.where(A >= threshold, A, 0)
        if np.all(W.sum(1) > 0):
            distributions[f"pruned_{threshold}"] = W / W.sum(1, keepdims=True)
            exact_weights[f"pruned_{threshold}"] = W
        else:
            excluded.append(
                {
                    "model": f"pruned_{threshold}",
                    "reason": "Pruning creates zero-outdegree rows; no silent repair or SCC substitution.",
                }
            )
    output = Path("artifacts/channel-certificates-20261003")
    output.mkdir(exist_ok=True)
    experiments = []
    for name, Q in distributions.items():
        for gamma in [0.2, 0.4, 0.6, 0.8]:
            result = profile(Q, gamma)
            result.update(model=name, transition_matrix=Q.tolist())
            experiments.append(result)
            print(
                name,
                gamma,
                "EB interval:",
                result["npt_based_eb_lower_bound"],
                result["constructive_eb_upper_bound"],
            )
    exact_proofs = []
    for result in experiments:
        if (
            result["model"] not in exact_weights
            or result["constructive_eb_upper_bound"] is None
        ):
            continue
        r = result["constructive_eb_upper_bound"]
        _, B, c = analytic_choi(
            np.asarray(result["transition_matrix"]), result["gamma"], r
        )
        certificate = phase_certificate(B, c)
        if certificate is None:
            continue
        proof = exact_certificate(
            exact_weights[result["model"]], str(result["gamma"]), r, certificate["v"]
        )
        proof["model"] = result["model"]
        exact_proofs.append(proof)
        result["rationally_certified_eb_index"] = proof["exact_eb_index"]
    (output / "exact-certificates.json").write_text(
        json.dumps(exact_proofs, indent=2) + "\n"
    )
    baseline = next(x for x in experiments if x["model"] == "fly" and x["gamma"] == 0.6)
    r = baseline["constructive_eb_upper_bound"]
    J, B, c = analytic_choi(P, 0.6, r)
    cert = phase_certificate(B, c) or product_certificate(B, c)
    serialized = {
        "model": "fly",
        "gamma": 0.6,
        "r": r,
        "dimension": n,
        "kind": cert["kind"],
        "v": cert["v"].tolist(),
        "c": cert["c"],
        "residual": cert["residual"].tolist(),
        "phase_alphabet": [0, 1, 2],
        "phase_angle": "2*pi*k/3",
        "phase_product_count": 3**n,
        "product_weight": 1 / (n * 3**n),
        "a": "sqrt(v)*phase",
        "b": "sqrt(c/v)*conjugate(phase)",
        "log_ratio_slack": cert["log_ratio_slack"],
        "max_reconstruction_error": float(np.max(np.abs(reconstruct(cert) - J))),
        "minimum_residual": cert["minimum_residual"],
    }
    (output / "product-decomposition.json").write_text(
        json.dumps(serialized, indent=2) + "\n"
    )
    (output / "results.json").write_text(
        json.dumps(
            {
                "nodes": nodes,
                "dataset_source_commit": provenance["source_commit"],
                "prediction": "Sparse mutual transitions delay NPT loss relative to dense reset controls at fixed gamma; not a claim of biological quantumness or novelty.",
                "experiments": experiments,
                "excluded_models": excluded,
            },
            indent=2,
        )
        + "\n"
    )
    files = ["results.json", "product-decomposition.json", "exact-certificates.json"]
    (output / "manifest.json").write_text(
        json.dumps(
            {
                "files_sha256": {
                    p: hashlib.sha256((output / p).read_bytes()).hexdigest()
                    for p in files
                },
                "source_sha256": hashlib.sha256(
                    Path(__file__).read_bytes()
                ).hexdigest(),
            },
            indent=2,
        )
        + "\n"
    )


if __name__ == "__main__":
    main()

"""Independent, time-boxed distribution/gradient audit; no LeJEPA training claim."""

import hashlib
import json
import time
from pathlib import Path

import numpy as np
from qiskit import QuantumCircuit
from qiskit.circuit import ParameterVector
from qiskit.primitives import StatevectorSampler
from qiskit.quantum_info import Statevector
from qiskit_machine_learning.neural_networks import SamplerQNN
from scipy.linalg import svd
from scipy.optimize import linprog, minimize
from scipy.spatial.distance import cdist


def feature_map(parameters, final_cz=True):
    circuit = QuantumCircuit(4)
    circuit.h(range(4))
    for j in range(4):
        circuit.ry(parameters[j], j)
        circuit.rz(parameters[j], j)
    for j in range(4):
        circuit.cz(j, (j + 1) % 4)
    for j in range(4):
        circuit.ry(parameters[(j + 1) % 4], j)
    if final_cz:
        for j in range(4):
            circuit.cz(j, (j + 1) % 4)
    return circuit


def states(z, scale=1.0, final_cz=True):
    """Vectorized exact simulator, independently compared with Qiskit below."""
    theta = np.pi / 2 * np.tanh(np.asarray(z) / scale)
    psi = np.full((len(theta), 16), 0.25, dtype=complex)
    indices = np.arange(16)

    def ry(q, angle):
        zero = indices[(indices & (1 << q)) == 0]
        one = zero + (1 << q)
        a, b = psi[:, zero].copy(), psi[:, one].copy()
        c, s = np.cos(angle[:, None] / 2), np.sin(angle[:, None] / 2)
        psi[:, zero] = c * a - s * b
        psi[:, one] = s * a + c * b

    def cz_ring():
        for j in range(4):
            bits = ((indices >> j) & 1) * ((indices >> ((j + 1) % 4)) & 1)
            psi[:] *= 1 - 2 * bits

    for j in range(4):
        ry(j, theta[:, j])
        bits = (indices >> j) & 1
        psi *= np.exp(1j * theta[:, j, None] * (bits - 0.5))
    cz_ring()
    for j in range(4):
        ry(j, theta[:, (j + 1) % 4])
    if final_cz:
        cz_ring()
    return psi


def quantum_kernel(x, y):
    return np.abs(states(x) @ states(y).conj().T) ** 2


def rbf(x, y):
    # Fixed bandwidth sqrt(d), registered before results; not tuned per alternative.
    return np.exp(-cdist(x, y, "sqeuclidean") / 8)


def unbiased_mmd(kxx, kyy, kxy):
    n, m = len(kxx), len(kyy)
    return float(
        (kxx.sum() - np.trace(kxx)) / (n * (n - 1))
        + (kyy.sum() - np.trace(kyy)) / (m * (m - 1))
        - 2 * kxy.mean()
    )


def linear_draws(kxx, kyy, kxy, rng, count=2000):
    """Bq=8, four independent paired terms, 16 fidelity evaluations per draw."""
    a = rng.integers(len(kxx), size=(count, 8))
    b = rng.integers(len(kyy), size=(count, 8))
    u, v = a[:, ::2], a[:, 1::2]
    g, h = b[:, ::2], b[:, 1::2]
    values = (kxx[u, v] + kyy[g, h] - kxy[u, h] - kxy[v, g]).mean(1)
    return {
        "mean": float(values.mean()),
        "std": float(values.std(ddof=1)),
        "negative_fraction": float((values < 0).mean()),
        "draws": count,
        "batch": 8,
        "sampling": "Independent draws with replacement from each empirical distribution; no hardware shot noise",
    }


def distribution_pilot(seed):
    rng = np.random.default_rng(seed)
    n = 384
    reference = rng.normal(size=(n, 4))
    sphere = rng.normal(size=(n, 4))
    sphere *= 2 / np.linalg.norm(sphere, axis=1, keepdims=True)
    candidates = {
        "gaussian": rng.normal(size=(n, 4)),
        "collapsed_zero": np.zeros((n, 4)),
        "near_collapsed": 0.01 * rng.normal(size=(n, 4)),
        "rademacher": rng.choice([-1.0, 1.0], size=(n, 4)),
        "sphere": sphere,
        "student_t3": rng.standard_t(3, size=(n, 4)) / np.sqrt(3),
    }
    kyy = quantum_kernel(reference, reference)
    rows = []
    for name, z in candidates.items():
        kxx, kxy = quantum_kernel(z, z), quantum_kernel(z, reference)
        covariance = np.cov(z, rowvar=False, bias=True)
        rows.append(
            {
                "seed": seed,
                "name": name,
                "quantum_unbiased_mmd": unbiased_mmd(kxx, kyy, kxy),
                "rbf_unbiased_mmd": unbiased_mmd(
                    rbf(z, z), rbf(reference, reference), rbf(z, reference)
                ),
                "moment_penalty": float(
                    np.square(z.mean(0)).sum() + np.square(covariance - np.eye(4)).sum()
                ),
                "linear_estimator": linear_draws(kxx, kyy, kxy, rng),
            }
        )
    return rows


def density_features(psi):
    rho = np.einsum("ni,nj->nij", psi, psi.conj())
    i, j = np.triu_indices(16, 1)
    return np.concatenate(
        [
            rho[:, np.arange(16), np.arange(16)].real,
            rho[:, i, j].real,
            rho[:, i, j].imag,
        ],
        axis=1,
    )


def collision_pilot(seed=442):
    """Different nonnegative empirical weights with same density and moments."""
    rng = np.random.default_rng(seed)
    x = rng.normal(size=(512, 4))
    psi = states(x)
    i, j = np.triu_indices(4)
    features = np.column_stack(
        [np.ones(len(x)), density_features(psi), x, x[:, i] * x[:, j]]
    )
    A = features.T
    _U, singular, Vh = svd(A, full_matrices=False)
    rank = int((singular > 1e-10).sum())
    constraints = Vh[:rank]
    baseline = np.full(len(x), 1 / len(x))
    solution = linprog(
        rng.normal(size=len(x)),
        A_eq=constraints,
        b_eq=constraints @ baseline,
        bounds=(0, None),
        method="highs",
        options={
            "primal_feasibility_tolerance": 1e-9,
            "dual_feasibility_tolerance": 1e-9,
        },
    )
    if not solution.success:
        raise RuntimeError(solution.message)
    weights = solution.x
    residual = float(np.max(np.abs(A @ (weights - baseline))))
    if residual > 1e-7 or weights.min() < 0:
        raise RuntimeError("Invalid finite-feature collision")
    delta = np.einsum("n,ni,nj->ij", weights - baseline, psi, psi.conj())
    difference = weights - baseline
    return {
        "seed": seed,
        "feature_rank": rank,
        "original_support": len(x),
        "alternative_support": int((weights > 1e-9).sum()),
        "weight_total_variation": float(np.abs(difference).sum() / 2),
        "quantum_mmd_squared": float(np.square(np.abs(delta)).sum()),
        "rbf_mmd_squared": float(difference @ rbf(x, x) @ difference),
        "maximum_density_and_raw_moment_residual": residual,
        "points": x.tolist(),
        "baseline_weights": baseline.tolist(),
        "alternative_weights": weights.tolist(),
        "scope": "Numerical finite-support counterexample, matches empirical Gaussian sample moments, not exact population Gaussian moments",
    }


class CountingSampler(StatevectorSampler):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.publications = 0
        self.bindings = 0

    def run(self, pubs, *, shots=None):
        from qiskit.primitives.containers import SamplerPub

        pubs = [SamplerPub.coerce(p, shots or self.default_shots) for p in pubs]
        self.publications += len(pubs)
        self.bindings += sum(p.parameter_values.size for p in pubs)
        return super().run(pubs, shots=shots)


def gradient_pilot():
    rng = np.random.default_rng(72)
    x, y = rng.normal(size=4), rng.normal(size=4)
    theta = np.pi / 2 * np.tanh(np.r_[x, y])
    xp, yp = ParameterVector("x", 4), ParameterVector("y", 4)
    pair = feature_map(xp).compose(feature_map(yp).inverse())
    pair.measure_all()
    sampler = CountingSampler(default_shots=16384, seed=73)
    qnn = SamplerQNN(
        circuit=pair,
        input_params=[*xp, *yp],
        weight_params=[],
        sampler=sampler,
        input_gradients=True,
        interpret=lambda outcome: int(outcome != 0),
        output_shape=2,
    )
    begin = time.perf_counter()
    value = float(qnn.forward(theta, [])[0, 0])
    gradient = qnn.backward(theta, [])[0][0, 0]
    duration = time.perf_counter() - begin
    eps = 1e-5

    def exact(parameters):
        circuit = feature_map(parameters[:4]).compose(
            feature_map(parameters[4:]).inverse()
        )
        return float(abs(Statevector.from_instruction(circuit).data[0]) ** 2)

    finite = np.array(
        [
            (exact(theta + eps * np.eye(8)[j]) - exact(theta - eps * np.eye(8)[j]))
            / (2 * eps)
            for j in range(8)
        ]
    )
    return {
        "exact_kernel": exact(theta),
        "sampled_kernel": value,
        "sampled_input_gradient": gradient.tolist(),
        "exact_finite_difference_gradient": finite.tolist(),
        "max_gradient_error": float(np.abs(gradient - finite).max()),
        "elapsed_seconds_one_forward_backward_pair": duration,
        "shots_per_binding": 16384,
        "sampler_publications": sampler.publications,
        "circuit_parameter_bindings": sampler.bindings,
        "estimated_bindings_Bq8_update": 16 * sampler.bindings,
        "gradient_scope": "SamplerQNN input-angle gradients directly verified; no TorchConnector/encoder training in this audit",
    }


def toy_optimization(seed):
    """Six synthetic affine view-consistency losses, not canonical LeJEPA training.

    Uses exact state features and a fixed Gaussian reference to isolate optimization.
    It deliberately does not test the proposed intermittent noisy paired gradient.
    """
    rng = np.random.default_rng(seed)
    x = rng.normal(size=(128, 4))
    noise = rng.normal(size=(128, 4)) * 0.1
    held = rng.normal(size=(512, 4))
    reference = rng.normal(size=(512, 4))
    target = states(reference)
    rho_target = target.T @ target.conj() / len(target)
    directions = rng.normal(size=(16, 4))
    directions /= np.linalg.norm(directions, axis=1, keepdims=True)
    initial = np.r_[np.eye(4).reshape(-1) * 0.01, np.zeros(4)]

    def moments(z):
        centered = z - z.mean(0)
        return float(
            np.square(z.mean(0)).sum()
            + np.square(centered.T @ centered / len(z) - np.eye(4)).sum()
        )

    def qmmd(z):
        psi = states(z)
        rho = psi.T @ psi.conj() / len(psi)
        return float(np.square(np.abs(rho - rho_target)).sum())

    def rmmd(z):
        # Analytic population Gaussian reference for fixed RBF bandwidth sqrt(4).
        return float(
            rbf(z, z).mean()
            - 2 * (4 / 5) ** 2 * np.exp(-np.square(z).sum(1) / 10).mean()
            + (4 / 6) ** 2
        )

    def sliced_proxy(z):
        projections = z @ directions.T
        pair = projections[:, None, :] - projections[None, :, :]
        return float(
            np.exp(-(pair**2) / 2).mean()
            - np.sqrt(2) * np.exp(-(projections**2) / 4).mean()
            + 1 / np.sqrt(3)
        )

    rows = []
    for name in [
        "none",
        "moments",
        "rbf_mmd",
        "quantum_mmd",
        "quantum_plus_moments",
        "fixed_sliced_ep_proxy",
    ]:

        def loss(parameters, name=name):
            A, b = parameters[:16].reshape(4, 4), parameters[16:]
            z = x @ A.T + b
            consistency = np.square(noise @ A.T).mean()
            regularizer = {
                "none": lambda: 0.0,
                "moments": lambda: moments(z),
                "rbf_mmd": lambda: rmmd(z),
                "quantum_mmd": lambda: qmmd(z),
                "quantum_plus_moments": lambda: qmmd(z) + moments(z),
                "fixed_sliced_ep_proxy": lambda: sliced_proxy(z),
            }[name]()
            return consistency + regularizer

        begin = time.perf_counter()
        fitted = minimize(
            loss,
            initial,
            method="L-BFGS-B",
            options={"maxiter": 60, "ftol": 1e-9, "gtol": 1e-6},
        )
        A, b = fitted.x[:16].reshape(4, 4), fitted.x[16:]
        z = held @ A.T + b
        eigen = np.linalg.eigvalsh(np.cov(z, rowvar=False, bias=True))
        spectrum = np.maximum(eigen, 0)
        probabilities = spectrum / max(spectrum.sum(), 1e-300)
        rank = float(
            np.exp(
                -np.sum(
                    probabilities[probabilities > 0]
                    * np.log(probabilities[probabilities > 0])
                )
            )
        )
        rows.append(
            {
                "seed": seed,
                "name": name,
                "effective_rank": rank,
                "minimum_covariance_eigenvalue": float(eigen.min()),
                "mean_feature_std": float(np.std(z, axis=0).mean()),
                "covariance_condition": float(eigen.max() / max(eigen.min(), 1e-300)),
                "held_out_rbf_mmd_biased": float(
                    rbf(z, z).mean()
                    + rbf(reference, reference).mean()
                    - 2 * rbf(z, reference).mean()
                ),
                "held_out_energy_distance_biased": float(
                    2 * cdist(z, reference).mean()
                    - cdist(z, z).mean()
                    - cdist(reference, reference).mean()
                ),
                "elapsed_seconds": time.perf_counter() - begin,
                "optimizer_success": bool(fitted.success),
                "optimizer_message": str(fitted.message),
                "iterations": fitted.nit,
                "function_evaluations": fitted.nfev,
                "affine_parameters": fitted.x.tolist(),
                "objective": float(fitted.fun),
            }
        )
    return rows


def main():
    begin = time.perf_counter()
    rng = np.random.default_rng(61)
    x = rng.normal(size=(10, 4))
    exact = np.array(
        [
            Statevector.from_instruction(feature_map(np.pi / 2 * np.tanh(row))).data
            for row in x
        ]
    )
    maximum = float(np.max(np.abs(states(x) - exact)))
    assert maximum < 1e-12
    final_gate_error = float(
        np.max(
            np.abs(
                quantum_kernel(x, x)
                - np.abs(states(x, final_cz=False) @ states(x, final_cz=False).conj().T)
                ** 2
            )
        )
    )
    rows = [r for seed in [2026, 2027, 2028] for r in distribution_pilot(seed)]
    collision = collision_pilot()
    gradients = gradient_pilot()
    toy = [row for seed in [2026, 2027, 2028] for row in toy_optimization(seed)]
    result = {
        "qubits": 4,
        "scale": 1,
        "max_vectorized_state_error": maximum,
        "final_common_CZ_kernel_difference": final_gate_error,
        "distribution_pilot": rows,
        "finite_feature_collision": collision,
        "qiskit_gradient": gradients,
        "toy_optimization": toy,
        "elapsed_seconds": time.perf_counter() - begin,
        "scope": "Independent feasibility audit, not six-way LeJEPA training, downstream performance, or hardware evidence",
    }
    output = Path("artifacts/q-sigreg-audit-20261003")
    output.mkdir(exist_ok=True)
    (output / "results.json").write_text(json.dumps(result, indent=2) + "\n")
    (output / "manifest.json").write_text(
        json.dumps(
            {
                "files_sha256": {
                    "results.json": hashlib.sha256(
                        (output / "results.json").read_bytes()
                    ).hexdigest()
                },
                "source_sha256": {
                    str(Path(__file__).relative_to(Path.cwd())): hashlib.sha256(
                        Path(__file__).read_bytes()
                    ).hexdigest()
                },
            },
            indent=2,
        )
        + "\n"
    )
    print(
        json.dumps(
            {
                "collision": {
                    k: v
                    for k, v in collision.items()
                    if k not in ["points", "baseline_weights", "alternative_weights"]
                },
                "gradient": gradients,
                "elapsed": result["elapsed_seconds"],
            },
            indent=2,
        ),
        flush=True,
    )
    for row in rows:
        print(
            row["seed"],
            row["name"],
            round(row["quantum_unbiased_mmd"], 5),
            round(row["rbf_unbiased_mmd"], 5),
            round(row["linear_estimator"]["std"], 4),
        )


if __name__ == "__main__":
    main()

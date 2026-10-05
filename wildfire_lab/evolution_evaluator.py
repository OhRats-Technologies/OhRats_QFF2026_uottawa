"""Fixed training-only candidate evaluator for genuine policy-driven rollouts."""

import hashlib
import time
import numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.metrics.pairwise import euclidean_distances, rbf_kernel
from sklearn.svm import SVC
from wildfire_lab.encoding_screen import preprocess, normalize_kernel
from wildfire_lab.evaluation import scores
from wildfire_lab.kernel import angle_states, fidelity

CANDIDATES = (
    "standard_logistic",
    "robust_tanh/rbf",
    "standard_tanh/rbf",
    "robust_tanh/qiskit_ZZ",
)


def evaluate(train, valid, candidate, plan):
    if candidate not in CANDIDATES:
        raise ValueError("Candidate is outside the frozen generator")
    start = time.perf_counter()
    variant = (
        "standard_tanh" if candidate == "standard_logistic" else candidate.split("/")[0]
    )
    x, v, bx, bv = preprocess(train, valid, plan["features"], variant)
    y, target = train.target.to_numpy(), valid.target.to_numpy()
    states = 0
    if candidate == "standard_logistic":
        model = LogisticRegression(C=plan["C"], max_iter=1000).fit(x, y)
        prediction = model.decision_function(v)
        numerical = dict(iterations=int(model.n_iter_[0]), fit_status=0)
    else:
        if candidate.endswith("/rbf"):
            distances = euclidean_distances(bx, squared=True)[
                np.triu_indices(len(bx), 1)
            ]
            gamma = float(1 / np.median(distances[distances > 0]))
            gram, cross = rbf_kernel(bx, gamma=gamma), rbf_kernel(bv, bx, gamma=gamma)
        else:
            angles = np.pi * (0.5 + plan["angle_scale"] * bx)
            va = np.pi * (0.5 + plan["angle_scale"] * bv)
            a, b = angle_states(angles, plan["reps"]), angle_states(va, plan["reps"])
            gram, cross = fidelity(a, a), fidelity(b, a)
            states = len(a) + len(b)
        gram, cross, variance = normalize_kernel(gram, cross)
        model = SVC(C=plan["C"], kernel="precomputed").fit(gram, y)
        prediction = model.decision_function(cross)
        numerical = dict(
            iterations=int(model.n_iter_[0]),
            fit_status=int(model.fit_status_),
            centered_variance=variance,
        )
    return dict(
        candidate=candidate,
        ap=scores(target, prediction, False)["average_precision"],
        metric=scores(target, prediction, False),
        predictions=prediction.tolist(),
        prediction_sha256=hashlib.sha256(prediction.tobytes()).hexdigest(),
        numerical=numerical,
        seconds=time.perf_counter() - start,
        predictor_fits=1,
        simulated_state_preparations=states,
        pair_circuits=0,
        shots=0,
        hardware_jobs=0,
    )

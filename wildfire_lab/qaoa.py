"""Small exact-state Qiskit QAOA screen with finite-shot subset extraction."""
import time
import numpy as np
from scipy.optimize import minimize
from qiskit import QuantumCircuit
from qiskit.quantum_info import Statevector
from wildfire_lab.selection import configurations, energies, ising


def circuit(objective, parameters):
    single, pair, _ = ising(objective)
    n = len(single)
    qc = QuantumCircuit(n)
    qc.h(range(n))
    for gamma, beta in np.asarray(parameters).reshape(-1, 2):
        for i, value in enumerate(single):
            qc.rz(2*gamma*value, i)
        for i in range(n):
            for j in range(i+1, n):
                if pair[i,j]:
                    qc.rzz(2*gamma*pair[i,j], i, j)
        qc.rx(2*beta, range(n))
    return qc


def select(objective, seed=7, depth=1, shots=512, maxiter=40):
    start = time.perf_counter()
    rng = np.random.default_rng(seed)
    bits = configurations(len(objective["linear"]))
    costs = energies(objective, bits)
    calls = 0
    def expected(parameters):
        nonlocal calls
        calls += 1
        probabilities = Statevector.from_instruction(circuit(objective, parameters)).probabilities()
        return float(probabilities @ costs)
    result = minimize(expected, rng.uniform(0,.5,size=2*depth), method="COBYLA", options={"maxiter":maxiter})
    probabilities = Statevector.from_instruction(circuit(objective,result.x)).probabilities()
    draws = rng.choice(len(bits), size=shots, p=probabilities)
    eligible = draws[bits[draws].sum(axis=1)==objective["k"]]
    if not len(eligible):
        return None, dict(status="no_feasible_sample", shots=shots, circuit_evaluations=calls+1, seconds=time.perf_counter()-start)
    best = eligible[np.argmin(costs[eligible])]
    return np.flatnonzero(bits[best]).tolist(), dict(status="measured_simulation", objective=float(costs[best]),
          feasible_probability=float(probabilities[bits.sum(axis=1)==objective["k"]].sum()),
          feasible_shots=len(eligible), shots=shots, circuit_evaluations=calls+1, depth=depth,
          parameters=result.x.tolist(), optimizer_success=bool(result.success), seconds=time.perf_counter()-start,
          limitations="Exact-state optimization plus synthetic sampling; not a hardware timing or quantum speedup.")

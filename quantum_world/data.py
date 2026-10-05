"""Independent initial states; action draws have separate deterministic seeds."""
from __future__ import annotations
import numpy as np
from .physics import haar_states, state_to_pauli, unitary, pauli_rotation, GENERATORS


def transitions(n: int, seed: int, angle_limit: float = 1.2) -> dict:
    rng = np.random.default_rng(seed+100000)
    psi = haar_states(n, seed)
    gate = rng.integers(0, 6, size=n)
    duration = np.ones(n)
    duration[gate >= 4] = rng.uniform(-angle_limit, angle_limit, size=(gate>=4).sum())
    x = state_to_pauli(psi)
    future = np.array([unitary(int(a),float(t))@s for a,t,s in zip(gate,duration,psi)])
    return dict(x=x, y=state_to_pauli(future), psi=psi, future=future,
                gate=gate, duration=duration)


def physical_path(data: dict, tau: np.ndarray) -> tuple[np.ndarray,np.ndarray]:
    """Chosen fractional-gate paths; derivative labels use known simulator physics.

    This is richer supervision than endpoint-only data, explicitly an ablation.
    """
    r = np.array([pauli_rotation(unitary(int(g),float(t*d)))@x
                  for g,d,t,x in zip(data['gate'],data['duration'],tau,data['x'])])
    v = np.einsum('nij,nj->ni',GENERATORS[data['gate']],r)*data['duration'][:,None]
    return r,v


def trajectory(n: int, length: int, seed: int, angle_limit: float = np.pi) -> dict:
    rng=np.random.default_rng(seed+100000)
    start=haar_states(n,seed)
    gates=rng.integers(0,6,size=(length,n))
    durations=np.ones((length,n))
    durations[gates>=4]=rng.uniform(-angle_limit,angle_limit,size=(gates>=4).sum())
    states=[start]
    for g,t in zip(gates,durations):
        states.append(np.array([unitary(int(a),float(d))@s for a,d,s in zip(g,t,states[-1])]))
    return dict(psi=np.array(states),gate=gates,duration=durations)

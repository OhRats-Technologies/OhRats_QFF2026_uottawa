"""Polynomial conditional-count Dicke preparation and cardinality-sector QAOA."""
import numpy as np
from qiskit import QuantumCircuit
from qiskit.circuit.library import RYGate, MCXGate, XXPlusYYGate
from wildfire_lab.selection import ising


def preparation(n, k):
    """Counter holds remaining ones; P(next=1|r)=r/(n-j). Ends in counter0."""
    width = k.bit_length()
    counter = list(range(n,n+width))
    qc = QuantumCircuit(n+width)
    for i in range(width):
        if (k >> i) & 1:
            qc.x(counter[i])
    for j in range(n):
        remaining = n-j
        for r in range(max(1,k-j),min(k,remaining)+1):
            if r == remaining:
                qc.append(MCXGate(width,ctrl_state=r),counter+[j])
            else:
                theta = 2*np.arcsin(np.sqrt(r/remaining))
                qc.append(RYGate(theta).control(width,ctrl_state=r,annotated=False),counter+[j])
        # Decrement conditioned on emitted1. High bits flip before low bits,
        # with an open-control borrow chain (little-endian counter).
        for bit in reversed(range(width)):
            qc.append(MCXGate(bit+1,ctrl_state=1),[j]+counter[:bit]+[counter[bit]])
    return qc


def circuit(objective, parameters):
    n, k = len(objective['linear']), objective['k']
    qc = preparation(n,k)
    # On cardinality-k states the penalty vanishes exactly. Removing it gives
    # identical ideal sector phases with fewer/smaller hardware rotations.
    unpenalized = dict(objective)
    penalty = objective['penalty']
    unpenalized['linear'] = objective['linear']-penalty*(1-2*k)
    unpenalized['pair'] = objective['pair']-np.triu(np.full((n,n),2*penalty),1)
    unpenalized['constant'] = objective['constant']-penalty*k*k
    single, pair, _ = ising(unpenalized)
    for gamma,beta in np.array(parameters).reshape(-1,2):
        for i, value in enumerate(single):
            qc.rz(2*gamma*value,i)
        for i in range(n):
            for j in range(i+1,n):
                if pair[i,j]:
                    qc.rzz(2*gamma*pair[i,j],i,j)
        for offset in [0,1]:
            for i in range(offset,n,2):
                qc.append(XXPlusYYGate(2*beta),[i,(i+1)%n])
    return qc

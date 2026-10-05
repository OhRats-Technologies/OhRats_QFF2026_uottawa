"""Fixed-cardinality initialization/mixer factorial; local exact optimization."""
from functools import lru_cache
import time
import numpy as np
from scipy.optimize import minimize
from qiskit import QuantumCircuit,transpile
from qiskit.circuit.library import StatePreparation,XXPlusYYGate
from qiskit.quantum_info import Statevector
from wildfire_lab.selection import configurations,energies,ising


@lru_cache(maxsize=8)
def feasible_preparation(n,k):
    eligible=configurations(n).sum(axis=1)==k
    if not eligible.any():raise ValueError('Empty cardinality sector')
    gate=StatePreparation(eligible.astype(float)/np.sqrt(eligible.sum()))
    _=gate.definition
    return gate


def circuit(objective,parameters,initial='all',mixer='X'):
    single,pair,_=ising(objective);n=len(single);qc=QuantumCircuit(n)
    if initial=='all':qc.h(range(n))
    elif initial=='feasible':qc.append(feasible_preparation(n,objective['k']),range(n))
    else:raise ValueError('Unknown initialization')
    gamma,beta=parameters
    for i,value in enumerate(single):qc.rz(2*gamma*value,i)
    for i in range(n):
        for j in range(i+1,n):
            if pair[i,j]:qc.rzz(2*gamma*pair[i,j],i,j)
    if mixer=='X':qc.rx(2*beta,range(n))
    elif mixer=='XY':
        if n%2:raise ValueError('Even ring required by frozen mixer')
        for offset in [0,1]:
            for i in range(offset,n,2):qc.append(XXPlusYYGate(2*beta),[i,(i+1)%n])
    else:raise ValueError('Unknown mixer')
    return qc


def select(objective,initial,mixer,seed,plan):
    start=time.perf_counter();rng=np.random.default_rng(seed);bits=configurations(len(objective['linear']))
    cost=energies(objective,bits);mask=bits.sum(axis=1)==objective['k'];calls=0
    def expected(parameters):
        nonlocal calls
        calls+=1
        return float(Statevector.from_instruction(circuit(objective,parameters,initial,mixer)).probabilities()@cost)
    initial_parameters=rng.uniform(0,.5,2)
    result=minimize(expected,initial_parameters,method='COBYLA',options={'maxiter':plan['max_objective_calls']})
    qc=circuit(objective,result.x,initial,mixer);probability=Statevector.from_instruction(qc).probabilities()
    draws=rng.choice(len(bits),size=plan['shots'],p=probability);eligible=draws[mask[draws]]
    chosen=int(eligible[np.argmin(cost[eligible])]) if len(eligible) else None
    compiled=transpile(qc,basis_gates=plan['logical_gate_basis'],optimization_level=plan['transpiler_optimization_level'],seed_transpiler=seed)
    return dict(initial=initial,mixer=mixer,parameters=result.x.tolist(),initial_parameters=initial_parameters.tolist(),
        probabilities=probability.tolist(),draws=draws.tolist(),selected_state=chosen,
        selected_indices=np.flatnonzero(bits[chosen]).tolist() if chosen is not None else None,
        selected_objective=float(cost[chosen]) if chosen is not None else None,
        feasible_probability=float(probability[mask].sum()),feasible_draws=len(eligible),expected_objective=float(probability@cost),
        optimizer_success=bool(result.success),optimizer_message=str(result.message),objective_calls=calls,
        quantum_state_evaluations=calls+1,logical_gate_counts=dict(compiled.count_ops()),logical_depth=compiled.depth(),
        seconds=time.perf_counter()-start)

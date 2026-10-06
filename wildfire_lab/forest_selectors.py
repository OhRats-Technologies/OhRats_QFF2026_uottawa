"""Same regression labels/objective, fixed QAOA sampling and diagonal SQD controls."""
import json
import numpy as np
from qiskit import qpy,transpile
from qiskit.primitives import StatevectorSampler
from qiskit.quantum_info import Statevector
from wildfire_lab.annual_selectors import objective
from wildfire_lab.constrained_qaoa import circuit
from wildfire_lab.selection import configurations,exact_subset,energies
from wildfire_lab.sqd_selection import sampled_subspace


def select(x,y,plan,output):
    config=plan['selection']
    obj=objective(x,y,config,config['seed'])
    bits=configurations(x.shape[1])
    feasible=np.flatnonzero(bits.sum(axis=1)==config['selected_count'])
    exact,minimum=exact_subset(obj)
    qc=circuit(obj,config['parameters'],initial='feasible',mixer='XY')
    ideal=Statevector.from_instruction(qc).probabilities()
    if abs(ideal[feasible].sum()-1)>1e-9:
        raise ValueError('Ideal cardinality-preserving selector leaked from sector')
    logical=transpile(qc,basis_gates=['rz','sx','x','cx'],optimization_level=1,
                      seed_transpiler=config['seed'])
    qc.measure_all()
    with (output/'selector.qpy').open('wb') as stream:
        qpy.dump(qc,stream)
    counts=StatevectorSampler(default_shots=config['shots'],seed=config['seed']).run([qc]).result()[0].data.meas.get_counts()
    if sum(counts.values())!=config['shots']:
        raise ValueError('Local selector returned unexpected shot count')
    draws=np.array([int(b,2) for b,n in counts.items() for _ in range(n)])
    sampled=sampled_subspace(obj,draws)
    uniform=np.random.default_rng(config['seed']).choice(feasible,size=config['shots'])
    uniform_sqd=sampled_subspace(obj,uniform)
    choices=dict(mi=np.argsort(-obj['relevance'],kind='stable')[:config['selected_count']].tolist(),
        exact=exact,sqd=sampled['selected_subset'],uniform=uniform_sqd['selected_subset'])
    result=dict(objective={k:v.tolist() if isinstance(v,np.ndarray) else v for k,v in obj.items()},
        choices=choices,exact_minimum=minimum,feasible_subsets=len(feasible),
        sampled=sampled,uniform=uniform_sqd,counts=counts,uniform_draws=uniform.tolist(),
        ideal_probabilities=ideal.tolist(),parameters=config['parameters'],
        ideal_feasible_probability=float(ideal[feasible].sum()),
        compiled_depth=logical.depth(),compiled_operations=dict(logical.count_ops()),
        local_quantum_shots=config['shots'],auxiliary_classical_draws=config['shots'],
        quantum_state_evaluations=2,hardware_jobs=0,
        limitation='Generic StatePreparation; fixed QAOA parameters, no optimization. Diagonal SQD equals the sampled feasible minimum; exact enumeration and uniform feasible draws are controls.')
    (output/'selection.json').write_text(json.dumps(result,indent=2)+'\n')
    return choices,result

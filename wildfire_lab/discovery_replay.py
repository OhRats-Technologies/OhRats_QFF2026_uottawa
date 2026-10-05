"""Finite-panel historical policy replay; only queried outcomes are revealed."""
ORDERS={
    'classical_first':['robust_tanh/rbf','standard_tanh/rbf','robust_tanh/product_rotation'],
    'quantum_first':['robust_tanh/qiskit_ZZ','standard_tanh/qiskit_ZZ','robust_tanh/product_rotation'],
    'balanced':['robust_tanh/rbf','robust_tanh/qiskit_ZZ','robust_tanh/product_rotation'],
    'classical_gate':['robust_tanh/rbf','standard_tanh/rbf','robust_tanh/qiskit_ZZ']}


def replay(panel,policy,budget=3):
    root=panel['standard_logistic']['ap']
    observed={'standard_logistic':root};trace=[];seconds=0.
    for name in ORDERS[policy][:budget]:
        # Stop decision sees revealed scores only, before accessing the next arm.
        if policy=='classical_gate' and len(trace)==2 and max(observed.values())<=root:
            break
        result=panel[name]
        observed[name]=result['ap'];seconds+=result['seconds'];trace.append(name)
    return dict(policy=policy,root_ap=root,best_ap=max(observed.values()),
                evaluations=len(trace),measured_component_seconds=seconds,trace=trace)

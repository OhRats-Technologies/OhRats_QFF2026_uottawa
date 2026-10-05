# Endpoint-only quantum-world study

Model learning rates selected using independent validation seeds before final states were generated.

| Transitions | Shots / observable | Model | Unseen-angle fidelity | Long-rollout fidelity | Raw validity |
|---:|---:|---|---:|---:|---:|
| 48 | 0 | direct | 0.320412 | 0.246708 | 0.002 |
| 48 | 0 | generator | 0.556334 | 0.239562 | 0.000 |
| 48 | 0 | hamiltonian | 0.958318 | 0.824503 | 1.000 |
| 48 | 0 | linear | 0.285243 | 0.250000 | 1.000 |
| 48 | 128 | direct | 0.318659 | 0.241961 | 0.003 |
| 48 | 128 | generator | 0.482511 | 0.250747 | 0.000 |
| 48 | 128 | hamiltonian | 0.880434 | 0.507099 | 1.000 |
| 48 | 128 | linear | 0.285331 | 0.254274 | 0.923 |
| 192 | 0 | direct | 0.347308 | 0.249953 | 0.022 |
| 192 | 0 | generator | 0.999999 | 0.999995 | 0.055 |
| 192 | 0 | hamiltonian | 1.000000 | 1.000000 | 1.000 |
| 192 | 0 | linear | 0.549317 | 0.251749 | 1.000 |
| 192 | 128 | direct | 0.360284 | 0.252974 | 0.014 |
| 192 | 128 | generator | 0.882981 | 0.294428 | 0.000 |
| 192 | 128 | hamiltonian | 0.993747 | 0.787310 | 1.000 |
| 192 | 128 | linear | 0.467366 | 0.250491 | 0.678 |
| 768 | 0 | direct | 0.496254 | 0.248389 | 0.013 |
| 768 | 0 | generator | 1.000000 | 1.000000 | 0.627 |
| 768 | 0 | hamiltonian | 1.000000 | 1.000000 | 1.000 |
| 768 | 0 | linear | 0.999998 | 0.999975 | 1.000 |
| 768 | 128 | direct | 0.486359 | 0.248885 | 0.009 |
| 768 | 128 | generator | 0.963284 | 0.807744 | 0.000 |
| 768 | 128 | hamiltonian | 0.998713 | 0.911398 | 1.000 |
| 768 | 128 | linear | 0.826046 | 0.332389 | 0.000 |

All methods receive the same endpoint data. Inputs are exact known preparations; only targets receive simulated shot noise.
All four families receive equal-count hyperparameter searches; linear ridge and neural learning rates are selected on the same validation criterion.
Hamiltonian and skew-generator composition are structural constraints, not independently discovered laws.
Fidelity is reported after spectral projection, alongside raw validity. No quantum hardware or quantum computational advantage.

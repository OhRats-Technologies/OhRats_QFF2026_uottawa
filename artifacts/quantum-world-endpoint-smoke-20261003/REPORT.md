# Endpoint-only quantum-world study

Model learning rates selected using independent validation seeds before final states were generated.

| Transitions | Shots / observable | Model | Unseen-angle fidelity | Long-rollout fidelity | Raw validity |
|---:|---:|---|---:|---:|---:|
| 96 | 0 | direct | 0.338997 | 0.255840 | 0.000 |
| 96 | 0 | generator | 0.916272 | 0.298596 | 0.000 |
| 96 | 0 | hamiltonian | 1.000000 | 1.000000 | 1.000 |
| 96 | 0 | linear | 0.349550 | 0.250191 | 1.000 |
| 96 | 128 | direct | 0.341069 | 0.243396 | 0.000 |
| 96 | 128 | generator | 0.678836 | 0.242738 | 0.000 |
| 96 | 128 | hamiltonian | 0.985341 | 0.910865 | 1.000 |
| 96 | 128 | linear | 0.340891 | 0.253759 | 0.891 |

All methods receive the same endpoint data. Inputs are exact known preparations; only targets receive simulated shot noise.
The linear baseline has fixed ridge=1e-4 and receives no ridge tuning; conclusions about outperforming it require a tuned check.
Hamiltonian and skew-generator composition are structural constraints, not independently discovered laws.
Fidelity is reported after spectral projection, alongside raw validity. No quantum hardware or quantum computational advantage.

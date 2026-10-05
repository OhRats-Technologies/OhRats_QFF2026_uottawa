# Two-qubit world model: validation pilot

Local exact simulation. This is screening, not final confirmation.

| Model | Seed | One-step fidelity | Unseen-angle fidelity | Long-rollout fidelity | Raw valid fraction |
|---|---:|---:|---:|---:|---:|
| direct | 4101 | 0.964065 | 0.485661 | 0.282227 | 0.008 |
| chord | 4101 | 0.497290 | 0.365437 | 0.263677 | 0.000 |
| source_chord | 4101 | 0.924249 | 0.500930 | 0.255543 | 0.227 |
| generator | 4101 | 0.999999 | 1.000000 | 0.999992 | 0.000 |
| hamiltonian | 4101 | 1.000000 | 1.000000 | 1.000000 | 1.000 |
| direct | 4102 | 0.962043 | 0.467682 | 0.278053 | 0.000 |
| chord | 4102 | 0.491878 | 0.370562 | 0.248398 | 0.000 |
| source_chord | 4102 | 0.928807 | 0.446361 | 0.256142 | 0.016 |
| generator | 4102 | 0.999999 | 1.000000 | 0.999995 | 0.000 |
| hamiltonian | 4102 | 1.000000 | 1.000000 | 1.000000 | 1.000 |
| direct | 4103 | 0.964128 | 0.508636 | 0.289880 | 0.062 |
| chord | 4103 | 0.491765 | 0.363105 | 0.245619 | 0.000 |
| source_chord | 4103 | 0.929433 | 0.483551 | 0.241152 | 0.297 |
| generator | 4103 | 0.999999 | 1.000000 | 0.999994 | 0.000 |
| hamiltonian | 4103 | 1.000000 | 1.000000 | 1.000000 | 1.000 |

Fidelity uses spectral simplex projection; raw validity and correction size are recorded separately.
Generator models receive chosen physical-path derivative supervision. Endpoint models receive endpoints only.
The orthogonal latent encoder cannot collapse; it is a learned basis, not representation compression.
An action-conditioned linear least-squares baseline with periodic RZ features is included.

# Two-qubit world model: validation pilot

Local exact simulation. This is screening, not final confirmation.

| Model | Seed | One-step fidelity | Unseen-angle fidelity | Long-rollout fidelity | Raw valid fraction |
|---|---:|---:|---:|---:|---:|
| direct | 4101 | 0.943593 | 0.432974 | 0.247847 | 0.312 |
| chord | 4101 | 0.509062 | 0.318786 | nan | 0.000 |
| source_chord | 4101 | 0.875972 | 0.434822 | 0.248994 | 0.719 |
| generator | 4101 | 0.998124 | 0.999214 | 0.977800 | 0.000 |
| hamiltonian | 4101 | 0.999703 | 1.000000 | 0.968230 | 0.000 |

Fidelity uses spectral simplex projection; raw validity and correction size are recorded separately.
Generator models receive chosen physical-path derivative supervision. Endpoint models receive endpoints only.
The orthogonal latent encoder cannot collapse; it is a learned basis, not representation compression.
An action-conditioned linear least-squares baseline with periodic RZ features is included.

# IBM hardware results · 3 October 2026

One circuit per experiment, 128 shots each, using the owner's IBM account on `ibm_marrakesh`.

| Experiment | IBM turnaround | Running duration | QPU charge |
| --- | ---: | ---: | ---: |
| Bell pair | 5.913 s | 4.391 s | 2 s |
| Six-qubit connectome Choi walk, t=1 | 5.502 s | 4.135 s | 2 s |

Each folder contains `result.json` (raw counts, ideal probabilities, timing and provenance) and `logical-circuit.qpy` (the measured logical circuit, before hardware compilation). `manifest.json` hashes those files. Load QPY with the recorded Qiskit version; no IBM connection is needed to inspect or simulate it.

Timing comes from IBM's created/running/finished timestamps. Retrieval took longer because of polling; that delay is recorded separately. Running duration includes overhead and differs from charged QPU time.

The Choi run reuses `flybrain.hardware_channel.prepare_choi_circuit`: three Bell pairs and the MaleCNS graph unitary on system qubits 3–5. Matching registers occurred in 93/128 shots (72.7%), versus 96.1% ideally. Total variation from ideal was 0.2463. With only 128 shots, sampling uncertainty is substantial; computational-basis counts do not certify entanglement retention.

## Conjugate-basis entanglement witness (6 qubits, paired Z and X bases)

Measured on `ibm_fez` (128 shots per basis) across reference qubits 0–2 and system qubits 3–5 (`conjugate-witness/`).

| Bipartite pair | $\langle ZZ \rangle$ | $\langle XX \rangle$ | Witness $S = \langle ZZ \rangle + \langle XX \rangle$ | Standard error $\sigma$ | Separable bound ($S \le 1$) |
| --- | ---: | ---: | ---: | ---: | --- |
| Pair 0 (0, 3) | +0.7031 | +0.6562 | 1.3594 | $\pm 0.0916$ | Violated ($3.92\sigma > 1.0$) |
| Pair 1 (1, 4) | +0.7969 | +0.6094 | 1.4062 | $\pm 0.0881$ | Violated ($4.61\sigma > 1.0$) |
| Pair 2 (2, 5) | +0.7188 | +0.6094 | 1.3281 | $\pm 0.0932$ | Violated ($3.52\sigma > 1.0$) |

Under trusted local Pauli measurements and fair projective sampling, $S > 1.0$ strictly certifies pairwise reference-system non-separability (entanglement preservation under step 1 of the connectome walk generator). The observed degradation from noiseless simulation ($S \approx 1.84$) to hardware ($S \approx 1.33 - 1.41$) reflects physical gate/readout noise on `ibm_fez`, not a pre-run calibration forecast.

Credentials, account/instance identifiers and private job IDs are excluded. Private service records remain in ignored `results/`. These new runs are separate from the frozen overnight sprint evidence.

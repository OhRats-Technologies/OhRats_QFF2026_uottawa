# IBM hardware results · 3 October 2026

One circuit per experiment, 128 shots each, using the owner's IBM account on `ibm_marrakesh`.

| Experiment | IBM turnaround | Running duration | QPU charge |
| --- | ---: | ---: | ---: |
| Bell pair | 5.913 s | 4.391 s | 2 s |
| Six-qubit connectome Choi walk, t=1 | 5.502 s | 4.135 s | 2 s |

Each folder contains `result.json` (raw counts, ideal probabilities, timing and provenance) and `logical-circuit.qpy` (the measured logical circuit, before hardware compilation). `manifest.json` hashes those files. Load QPY with the recorded Qiskit version; no IBM connection is needed to inspect or simulate it.

Timing comes from IBM's created/running/finished timestamps. Retrieval took longer because of polling; that delay is recorded separately. Running duration includes overhead and differs from charged QPU time.

The Choi run reuses `flybrain.hardware_channel.prepare_choi_circuit`: three Bell pairs and the MaleCNS graph unitary on system qubits 3–5. Matching registers occurred in 93/128 shots (72.7%), versus 96.1% ideally. Total variation from ideal was 0.2463. With only 128 shots, sampling uncertainty is substantial; computational-basis counts do not certify entanglement retention.

Credentials, account/instance identifiers and private job IDs are excluded. Private service records remain in ignored `results/`. These new runs are separate from the frozen overnight sprint evidence.

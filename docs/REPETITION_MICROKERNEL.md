# Restricted repetition-code overlap benchmark

The October 7 hardware extension tests the deferred logical microkernel from [the error study](QSVR_QEC_ERROR_STUDY.md), using IBM Marrakesh and Quebec. This is a quantum-overlap diagnostic connected to QSVR kernels, not a retrained wildfire predictor.

## Task and controls

Prepare a phase state, then estimate its overlap with the zero-phase state:

$$k(\delta)=\cos^2(\delta/2).$$

The encoded circuit prepares $(|000\rangle+|111\rangle)/\sqrt2$, applies $R_Z(\delta)$ to one data qubit, extracts two parity checks, conditionally corrects one bit flip, decodes and measures **all three data qubits**. The all-zero frequency is the encoded overlap; reading only the first decoded qubit would ignore leakage outside the code subspace. The dynamic arm uses five physical qubits: three data and two syndrome ancillas.

Compare unencoded, encoded without correction and encoded with one dynamic correction round. Inputs are $\delta=0,\pi/4,\pi/2$; storage delays are 0 or 20 microseconds. Fault controls are none, each single-data-qubit X, and Z on data zero. Each device gets two blocks of 90 circuits, 4,096 shots each: four jobs and 1,474,560 planned shots. Block repetition samples shot/short-term variation; it is not independent calibration-day replication. Report extra depth, gates and charged time rather than claiming equal gate costs.

A physical X after phase encoding leaves this particular overlap probability unchanged. Therefore X-injection cells diagnose recovery from **encoded leakage**, not a generic advantage over the unencoded kernel. The no-injection idle cells address whether the overhead helps under actual device noise. Z is an explicit failure control: repetition coding does not correct phase errors. This restricted logical RZ construction does not implement the full ZZ feature map or fault-tolerant QSVR.

## Execution and evidence

[Frozen plan](../experiments/repetition_microkernel.json) · [circuits](../wildfire_lab/repetition_kernel.py) · [acquisition](../wildfire_lab/repetition_hardware.py).

```sh
uv run --no-sync python -m unittest tests.test_repetition_kernel -v
uv run --no-sync --env-file .env python scripts/run_repetition_microkernel.py collect
```

Local exact-state tests verify the single-X correction mapping, no-fault overlap and uncorrected phase-flip response. Device-native circuits have been prepared on both requested devices. Hardware results remain pending until validated returned counts exist. Private intents, identifiers and acquisition metrics stay under ignored `results/repetition-microkernel-v1`; submission is exclusive per block and ambiguous submissions are never retried.

The public report will include every cell/block, overlap errors and shot uncertainty, syndrome frequencies, compiled resources and charged time. Neither postselection nor new predictive fitting is part of this study; 2019–2024 data are not read.

Method reference: [IBM repetition-code tutorial](https://quantum.cloud.ibm.com/docs/en/tutorials/repetition-codes). The tutorial teaches dynamic correction of bit flips; this extension tests coherent phase-overlap readout rather than only classical basis-state memory.

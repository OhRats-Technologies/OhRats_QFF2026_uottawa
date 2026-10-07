"""Restricted phase-overlap kernel with audited three-data-qubit X correction."""
import numpy as np
from qiskit import QuantumCircuit, ClassicalRegister


def circuit(delta, arm, fault="none", idle_us=0, mid_measure=False):
    """Encode |+>, apply logical RZ, correct storage faults, uncompute overlap.

    RZ on data zero implements logical RZ in span{|000>,|111>}.
    Correction is before decoding; final majority voting would not measure this
    coherent phase overlap and is deliberately not substituted for correction.
    """
    encoded = arm != "physical"
    qc = QuantumCircuit(5 if encoded else 1)
    out = ClassicalRegister(3 if encoded else 1, "overlap")
    qc.add_register(out)
    qc.h(0)
    if encoded:
        qc.cx(0, 1)
        qc.cx(1, 2)
    qc.rz(delta, 0)
    qc.barrier()
    if idle_us:
        for q in range(3 if encoded else 1):
            qc.delay(idle_us, q, unit="us")
    if fault != "none":
        getattr(qc, fault[0].lower())(int(fault[1:]) if encoded else 0)
    qc.barrier()
    if arm == "corrected":
        syndrome = ClassicalRegister(2, "syndrome")
        qc.add_register(syndrome)
        # Five-qubit line: data 0,1,2; checks 3,4. Transpiler routes it.
        qc.cx(0, 3)
        qc.cx(1, 3)
        qc.cx(1, 4)
        qc.cx(2, 4)
        for q, bit in [(3, syndrome[0]), (4, syndrome[1])]:
            if mid_measure:
                from qiskit_ibm_runtime.circuit import MidCircuitMeasure
                qc.append(MidCircuitMeasure(), [q], [bit])
            else:
                qc.measure(q, bit)
        # s=(d0 XOR d1, d1 XOR d2), little-endian integer.
        for value, data in [(1, 0), (3, 1), (2, 2)]:
            with qc.if_test((syndrome, value)):
                qc.x(data)
    if encoded:
        qc.cx(1, 2)
        qc.cx(0, 1)
    qc.h(0)
    qc.measure(range(len(out)), out)
    return qc


def cases(plan):
    return [dict(delta=delta, arm=arm, fault=fault, idle_us=idle,
                 ideal=float(np.cos(delta / 2)**2))
            for delta in plan["deltas"] for idle in plan["idle_us"]
            for fault in plan["faults"] for arm in plan["arms"]]


def summarize(counts, metadata, shots):
    rows = []
    for row, case in zip(counts, metadata, strict=True):
        n = sum(row.values())
        if n != shots:
            raise ValueError("Returned shot count differs from plan")
        successes = sum(v for k, v in row.items() if int(k, 2) == 0)
        p = successes / n
        rows.append(dict(**case, shots=n, zero_count=successes, estimate=p,
                         error=p-case["ideal"], squared_error=(p-case["ideal"])**2,
                         standard_error=float(np.sqrt(p*(1-p)/n))))
    return rows

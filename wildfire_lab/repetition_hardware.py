"""Exclusive, hashed hardware acquisition for the restricted repetition kernel."""
import json
import time
from pathlib import Path
from qiskit import qpy
from qiskit.transpiler import generate_preset_pass_manager
from qiskit_ibm_runtime.executor_sampler import Sampler
from .mitigation_hardware import service, connected_path, write, sha, now
from .repetition_kernel import circuit, cases, summarize


SOURCES = ["wildfire_lab/repetition_kernel.py", "wildfire_lab/repetition_hardware.py",
           "scripts/run_repetition_microkernel.py"]


def prepare(root, output):
    plan_path = root / "experiments/repetition_microkernel.json"
    plan = json.loads(plan_path.read_text())
    output.mkdir(parents=True, exist_ok=False)
    metadata = cases(plan)
    for device in plan["devices"]:
        backend = service(device["credential"], device["instance"]).backend(device["backend"])
        path = connected_path(backend, 5)
        mid = "measure_2" in backend.operation_names
        if "if_else" not in backend.operation_names:
            raise ValueError("Requested backend lacks conditional correction")
        circuits = []
        for case in metadata:
            qc = circuit(case["delta"], case["arm"], case["fault"], case["idle_us"], mid)
            layout = path[:qc.num_qubits]
            pm = generate_preset_pass_manager(backend=backend, initial_layout=layout,
                                              optimization_level=1, seed_transpiler=41)
            circuits.append(pm.run(qc))
        directory = output / device["backend"]
        directory.mkdir()
        with (directory / "circuits.qpy").open("wb") as stream:
            qpy.dump(circuits, stream)
        write(directory / "prepared.json", dict(device=device, metadata=metadata,
              plan=plan, plan_sha256=sha(plan_path), circuits_sha256=sha(directory/"circuits.qpy"),
              code_sha256={p: sha(root/p) for p in SOURCES}, prepared_utc=now(),
              layout=path, midcircuit_measure=mid,
              resources=[dict(depth=qc.depth(), operations=dict(qc.count_ops())) for qc in circuits]))
    return dict(status="prepared", devices=[d["backend"] for d in plan["devices"]],
                circuits_per_job=len(metadata), shots_per_circuit=plan["shots"])


def submit(root, output, backend_name, block):
    directory = output / backend_name
    receipt = json.loads((directory / "prepared.json").read_text())
    plan = receipt["plan"]
    if block not in range(plan["blocks"]):
        raise ValueError("Block outside frozen plan")
    if sha(root/"experiments/repetition_microkernel.json") != receipt["plan_sha256"]:
        raise ValueError("Plan changed after preparation")
    for p, expected in receipt["code_sha256"].items():
        if sha(root/p) != expected:
            raise ValueError("Code changed after preparation")
    if sha(directory/"circuits.qpy") != receipt["circuits_sha256"]:
        raise ValueError("Circuit bytes changed")
    device = receipt["device"]
    backend = service(device["credential"], device["instance"]).backend(backend_name)
    with (directory/"circuits.qpy").open("rb") as stream:
        circuits = qpy.load(stream)
    intent = directory / f"block-{block}-intent.json"
    with intent.open("x") as stream:
        json.dump(dict(created_utc=now(), block=block, shots=plan["shots"],
                       circuits=len(circuits)), stream)
    sampler = Sampler(mode=backend, options=dict(max_execution_time=plan["max_execution_time"]))
    tick = time.perf_counter()
    job = sampler.run(circuits, shots=plan["shots"])
    write(directory/f"block-{block}-submitted.json", dict(job_id=job.job_id(),
          submitted_utc=now(), api_roundtrip_seconds=time.perf_counter()-tick))
    return dict(backend=backend_name, block=block, status="accepted")


def collect(output):
    statuses = []
    for directory in sorted(output.iterdir()):
        receipt = json.loads((directory/"prepared.json").read_text())
        device = receipt["device"]
        svc = service(device["credential"], device["instance"])
        for submitted in sorted(directory.glob("block-*-submitted.json")):
            prefix = submitted.name.removesuffix("-submitted.json")
            collected = directory / f"{prefix}-collected.json"
            if collected.exists():
                statuses.append(dict(backend=directory.name, block=prefix, status="collected"))
                continue
            job = svc.job(json.loads(submitted.read_text())["job_id"])
            status = str(job.status()).upper()
            statuses.append(dict(backend=directory.name, block=prefix, status=status))
            if status in {"DONE", "ERROR", "CANCELLED"}:
                write(directory/f"{prefix}-metrics.json", job.metrics())
                write(directory/f"{prefix}-usage.json", job.usage())
            if status == "DONE":
                results = job.result()
                counts = [item.data.overlap.get_counts() for item in results]
                rows = summarize(counts, receipt["metadata"], receipt["plan"]["shots"])
                syndromes = [item.data.syndrome.get_counts() if hasattr(item.data, "syndrome")
                             else None for item in results]
                write(collected, dict(rows=rows, counts=counts, syndrome_counts=syndromes,
                                     collected_utc=now()))
    return statuses

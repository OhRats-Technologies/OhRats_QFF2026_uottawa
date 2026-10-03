"""Bounded IBM measurements for validated chemistry and sustainability cases."""

import argparse
from datetime import datetime, timezone
import json
from pathlib import Path

from qiskit import qpy
from qiskit.quantum_info import Statevector
from qiskit.transpiler import generate_preset_pass_manager
from qiskit_ibm_runtime import SamplerV2

from flybrain.data import REPO
from flybrain.hardware import collect, service, check_sprint_budget
from flybrain.progress import record


def chemistry_cases():
    from .chemistry import molecule, measurement_circuits

    cases = []
    for distance in [0.735, 1.4]:
        model = molecule(distance)
        metadata = {key: value for key, value in model.items() if key != "circuit"}
        for basis, circuit in zip(
            ["z", "bell"], measurement_circuits(model["circuit"])
        ):
            state_circuit = circuit.remove_final_measurements(inplace=False)
            cases.append(
                (
                    circuit,
                    {
                        "name": f"h2_{distance}_{basis}",
                        "basis": basis,
                        "distance": distance,
                        "model": metadata,
                        "expected": Statevector.from_instruction(state_circuit)
                        .probabilities()
                        .tolist(),
                    },
                )
            )
    return cases, ["00", "01", "10", "11"]


def submit(args):
    manifest_path = args.output / "submitted.json"
    if manifest_path.exists():
        print("Already submitted; no duplicate job created.")
        return
    if (args.output / "submission_intent.json").exists():
        raise ValueError(
            "Prior intent without job ID; inspect workload history before retrying"
        )
    # Include the FlyWalk job in the session cap, rather than hiding it in another module.
    check_sprint_budget()
    if args.experiment == "chemistry":
        cases, nodes = chemistry_cases()
    else:
        from .scheduling import hardware_cases

        cases, nodes = hardware_cases()
        from .spinweave import hardware_cases as spin_cases

        cases.extend(spin_cases())
    if len(cases) > 6:
        raise ValueError("At most six circuits per track job")
    runtime = service()
    backend = runtime.backend("ibm_quebec")
    manager = generate_preset_pass_manager(
        backend=backend, optimization_level=3, seed_transpiler=2026
    )
    compiled = manager.run([c for c, _ in cases])
    args.output.mkdir(parents=True, exist_ok=True)
    summaries = [
        {**reference, "depth": circuit.depth(), "operations": dict(circuit.count_ops())}
        for circuit, (_, reference) in zip(compiled, cases)
    ]
    intent = {
        "created_utc": datetime.now(timezone.utc).isoformat(),
        "backend": backend.name,
        "experiment": args.experiment,
        "shots_per_circuit": args.shots,
        "max_execution_seconds": 300,
        "nodes": nodes,
        "cases": summaries,
    }
    with (args.output / "circuits.qpy").open("wb") as stream:
        qpy.dump(compiled, stream)
    (args.output / "submission_intent.json").write_text(
        json.dumps(intent, indent=2) + "\n"
    )
    job = SamplerV2(mode=backend, options={"max_execution_time": 300}).run(
        compiled, shots=args.shots
    )
    manifest = {
        **intent,
        "job_id": job.job_id(),
        "status": str(job.status()),
        "evidence": "hardware_submission",
    }
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n")
    record(
        args.experiment,
        "hardware",
        "submitted",
        backend=backend.name,
        circuits=len(cases),
        shots_per_circuit=args.shots,
        evidence=f"results/{args.experiment}-hardware/submitted.json",
    )
    print(
        json.dumps(
            {
                "experiment": args.experiment,
                "job_id": job.job_id(),
                "circuits": len(cases),
                "shots": args.shots,
                "status": manifest["status"],
            }
        )
    )


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("experiment", choices=["chemistry", "scheduling"])
    parser.add_argument("command", choices=["submit", "collect"])
    parser.add_argument("--output", type=Path)
    parser.add_argument("--shots", type=int, default=1024)
    args = parser.parse_args()
    args.output = args.output or REPO / f"results/{args.experiment}-hardware"
    if not 128 <= args.shots <= 4096:
        parser.error("Shots must be 128–4096")
    try:
        {"submit": submit, "collect": collect}[args.command](args)
    except Exception as error:
        parser.exit(
            1,
            f"Hardware action failed ({type(error).__name__}); no credentials printed. Inspect local intent/status and IBM workload history before retrying.\n",
        )


if __name__ == "__main__":
    main()

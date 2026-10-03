"""Local noise-model forecasts from an IBM calibration snapshot; never hardware data."""

import json
from datetime import datetime, timezone
import numpy as np
from qiskit import qpy
from qiskit_aer import AerSimulator
from flybrain.data import REPO
from flybrain.hardware import service
from flybrain.progress import timed_stage


def main():
    output = REPO / "results/calibrated"
    output.mkdir(parents=True, exist_ok=True)
    backend = service().backend("ibm_quebec")
    simulator = AerSimulator.from_backend(
        backend,
        method="density_matrix",
        enable_truncation=True,
        max_parallel_threads=2,
        max_memory_mb=1024,
    )
    rows = []
    with timed_stage("calibration-forecast", "local_isa_simulation") as evidence:
        for folder in ["hardware", "chemistry-hardware", "scheduling-hardware"]:
            root = REPO / "results" / folder
            manifest = json.loads((root / "submitted.json").read_text())
            with (root / "circuits.qpy").open("rb") as stream:
                circuits = qpy.load(stream)
            result = simulator.run(circuits, shots=8192, seed_simulator=2026).result()
            if not result.success:
                raise ValueError("Local calibration simulation failed")
            counts = result.get_counts()
            for reference, observed in zip(manifest["cases"], counts):
                p = np.zeros(len(manifest["nodes"]))
                for bits, count in observed.items():
                    p[int(bits, 2)] = count / 8192
                rows.append(
                    {
                        **reference,
                        "counts": observed,
                        "observed": p.tolist(),
                        "total_variation_from_ideal": float(
                            np.abs(p - np.array(reference["expected"])).sum() / 2
                        ),
                        "actual_shots": 8192,
                        "source_folder": folder,
                    }
                )
        evidence.update(
            circuits=len(rows),
            hardware_execution=False,
            calibration_source=backend.name,
        )
    report = {
        "evidence": "LOCAL_AER_BACKEND_CALIBRATION_FORECAST_NOT_HARDWARE",
        "backend": backend.name,
        "created_utc": datetime.now(timezone.utc).isoformat(),
        "cases": rows,
        "limitations": "Aer model derived from current backend calibration. Markovian gate and readout approximations omit drift, crosstalk, correlated errors and other systematics. These are locally simulated counts, not collected IBM shots.",
    }
    (output / "forecast.json").write_text(json.dumps(report, indent=2) + "\n")
    # Persist the exact local model for reproducibility, without service credentials.
    (output / "noise_model.json").write_text(
        json.dumps(
            simulator.options.noise_model.to_dict(),
            default=lambda x: x.tolist() if hasattr(x, "tolist") else str(x),
        )
        + "\n"
    )
    print(
        json.dumps(
            {
                "local_forecast_circuits": len(rows),
                "hardware_results": False,
                "tv": {r["name"]: r["total_variation_from_ideal"] for r in rows},
            }
        )
    )


if __name__ == "__main__":
    try:
        main()
    except Exception as error:
        raise SystemExit(
            f"Local calibration forecast failed ({type(error).__name__}); credentials not printed."
        )

"""Fit maintained MBI 2.0 at a pinned commit from aggregate query packages."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import jax
import numpy as np
from mbi import Domain, LinearMeasurement, estimation, save

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from scripts.pgm_integration_probe import MaskSumQuery

OUT = ROOT / "reports/published_references"
EXPECTED_MBI_COMMIT = "9429881f0f21ef413424f6011b9d6ae20728176d"


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--cell", required=True)
    args = ap.parse_args()
    if args.cell not in {c["name"] for c in json.loads((OUT / "pgm_cell_manifest.json").read_text())["cells"]}:
        raise ValueError("Unregistered PGM cell")
    manifest = json.loads((OUT / "pgm_cell_manifest.json").read_text())
    if manifest["mbi_commit"] != EXPECTED_MBI_COMMIT:
        raise ValueError("Pinned maintained MBI source changed")
    entry = next(c for c in manifest["cells"] if c["name"] == args.cell)
    cell = OUT / args.cell
    package_path = cell / "measurement_package.json"
    if sha(package_path) != entry["measurement_package_sha256"]:
        raise ValueError("Permitted aggregate measurement package hash mismatch")
    if (cell / "pgm_complete.json").is_file():
        print(args.cell, "cached")
        return
    package = json.loads(package_path.read_text())
    if package["access"] != "aggregate unnoised calibration query means and public domain only; nonprivate":
        raise ValueError("PGM access contract changed")
    if package["optimizer"] != {"name": "maintained MBI UniversalAcceleratedMethod", "iters": 500, "tol": None}:
        raise ValueError("PGM optimizer settings changed")
    jax.config.update("jax_enable_x64", True)
    jax.config.update("jax_enable_compilation_cache", False)
    sizes = [len(package["domain"][c]["values"]) for c in package["domain"]]
    domain = Domain(list(package["domain"]), sizes)
    measurements = []
    for item in package["measurements"]:
        mask = tuple(float(v) for v in item["mask"])
        expected_size = int(np.prod([len(package["domain"][c]["values"]) for c in item["clique"]]))
        if len(mask) != expected_size or not -1e-9 <= item["value"] <= 1+1e-9:
            raise ValueError("Invalid released scalar query measurement")
        # Alpha-weighted means can exceed one by a floating-point ulp.
        value = float(np.clip(item["value"], 0.0, 1.0))
        measurements.append(LinearMeasurement(value, tuple(item["clique"]),
                                              package["stddev"], MaskSumQuery(mask)))
    started = time.monotonic()
    model = estimation.UniversalAcceleratedMethod().estimate(
        domain, measurements, known_total=package["known_total"],
        iters=500, tol=None)
    fit_seconds = time.monotonic() - started
    checkpoint = cell / "model_mbi2.npz"
    save(model, checkpoint)
    predictions = []
    for item in package["measurements"]:
        factor = model.project(tuple(item["clique"]))
        expected = float(np.dot(np.asarray(factor.datavector()), np.asarray(item["mask"])))
        predictions.append({"query": item["query"], "released_calibration_mean": item["value"],
                            "fitted_mean": expected, "absolute_residual": abs(expected-item["value"])})
    (cell / "fitted_query_means.json").write_text(json.dumps(predictions, indent=2)+"\n")
    draws = []
    for rep, seed in enumerate(package["sampling"]["seeds"]):
        np.random.seed(seed)
        sampled = model.synthetic_data(rows=package["sampling"]["rows"], method="sample")
        arrays = {c: np.asarray(sampled.data[c], dtype=np.int16) for c in package["domain"]}
        path = cell / f"discrete_draw_{rep}.npz"
        np.savez_compressed(path, **arrays)
        draws.append({"replicate": rep, "seed": seed, "path": path.name,
                      "sha256": sha(path), "rows": len(next(iter(arrays.values())))})
    record = {"status": "complete", "finished_utc": datetime.now(timezone.utc).isoformat(),
              "fit_seconds": fit_seconds, "total_elapsed_seconds": time.monotonic()-started,
              "model_checkpoint_sha256": sha(checkpoint), "draws": draws,
              "query_linf_calibration": max(p["absolute_residual"] for p in predictions),
              "query_mae_calibration": float(np.mean([p["absolute_residual"] for p in predictions])),
              "mbi_commit": EXPECTED_MBI_COMMIT, "mbi_version": "2.0.0",
              "python": sys.version, "jax_version": jax.__version__,
              "native_thread_env": {k: os.environ.get(k) for k in
                 ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS", "NUMEXPR_NUM_THREADS", "XLA_FLAGS")}}
    (cell / "pgm_complete.json").write_text(json.dumps(record, indent=2)+"\n")
    print(json.dumps({"cell": args.cell, "fit_seconds": fit_seconds,
                      "calibration_query_linf": record["query_linf_calibration"]}))


if __name__ == "__main__":
    main()

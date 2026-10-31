"""Checkpoint-only Exp9 projection and released-query ablations."""
from __future__ import annotations

import argparse
import fcntl
import hashlib
import json
import os
import pickle
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd
import yaml

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from btp.evaluation import empirical_metrics, sample_mixture
from btp.privacy import PUBLIC_EDUCATION_NUMBER_MAP, public_schema
from btp.projected_workload import projected_workloads_v2
from scripts.representation_constrained import check_capacity, constrained_query_minimax, reference_parts

SOURCE = ROOT / "results/ec2_projected_v2_deterministic_20261024"
WEIGHTS = ROOT / "results/representation_constrained_projected_v2_deterministic_20261024"
OUT = ROOT / "reports/mechanisms"
REPEATS = 5
ROWS = 10000
EXPECTED_HASH = "25c89ff4971fa79be992e93f4c92d2ce51ab7d3368a569389a3118bd07b47868"


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def specs(kind: str) -> list[tuple[str, str, int, int]]:
    if kind == "projection":
        return [(g, p, k, seed) for g in ("chow_liu", "mixed_gmm")
                for p, k in (("age", 5), ("label_skew", 10))
                for seed in (101, 202, 303)]
    if kind == "summaries":
        return [("copula", p, k, seed) for p, k in (("age_education", 5), ("label_skew", 10))
                for seed in (101, 202, 303)]
    raise ValueError(kind)


def find_cell(key: tuple) -> Path:
    found = []
    for cell in SOURCE.iterdir():
        if not cell.is_dir():
            continue
        cfg = json.loads((cell / "configuration.json").read_text())
        if (cfg["generator"], cfg["partition"], cfg["k"], cfg["seed"]) == key:
            found.append(cell)
    if len(found) != 1:
        raise ValueError(f"Expected unique corrected cell {key}, found {found}")
    cfg = json.loads((found[0] / "configuration.json").read_text())
    if cfg["code_hash"] != EXPECTED_HASH or cfg["workload_version"] != "projected_v2":
        raise ValueError("Incompatible saved checkpoint")
    return found[0]


def manifest(kind: str) -> list[dict]:
    records = []
    for key in specs(kind):
        cell = find_cell(key)
        records.append({"generator": key[0], "partition": key[1], "k": key[2],
                        "seed": key[3], "source_cell": str(cell.relative_to(ROOT)),
                        "source_configuration_sha256": sha(cell / "configuration.json")})
    OUT.mkdir(parents=True, exist_ok=True)
    path = OUT / f"{kind}_cell_manifest.json"
    if path.exists():
        if json.loads(path.read_text())["cells"] != records:
            raise ValueError("Mechanism cell manifest changed")
    else:
        path.write_text(json.dumps({"registered_at": "2026-10-25 pre-execution",
                                    "cells": records}, indent=2) + "\n")
    return records


def models_and_parts(cell: Path):
    cfg = json.loads((cell / "configuration.json").read_text())
    alpha = np.asarray(json.loads((cell / "partition.json").read_text())["alpha"], float)
    models = [pickle.loads((cell / "releases" / f"client_{i}.pkl").read_bytes())
              for i in range(cfg["k"])]
    parts = reference_parts(cell, cfg, alpha)
    primary, audit = projected_workloads_v2(public_schema())
    declared = json.loads((cell / "workloads.json").read_text())
    if declared != json.loads(json.dumps({"calibration": primary.to_dict(),
                                          "unseen_audit": audit.to_dict()})):
        raise ValueError("Saved workload differs")
    return cfg, alpha, models, parts, primary, audit


def projection(cell: Path) -> None:
    cfg, alpha, models, parts, primary, audit = models_and_parts(cell)
    fit_path = WEIGHTS / cell.name / "weight_fits.json"
    fit = json.loads(fit_path.read_text())
    rows = []
    for method in ("size", "constrained"):
        w = np.asarray(fit[method]["weights"], float)
        if abs(w.sum()-1) > 1e-7:
            raise ValueError("Saved weights not on simplex")
        for rep in range(REPEATS):
            seed = cfg["seed"] + 5200 + rep
            raw, counts = sample_mixture([m.raw_model for m in models], w, ROWS, seed)
            projected = raw.copy()
            target = projected.education.map(PUBLIC_EDUCATION_NUMBER_MAP)
            known = target.notna()
            projected.loc[known, "education-num"] = target.loc[known].astype(int)
            for name, synth in (("raw", raw), ("projected_same_rows", projected)):
                metrics = empirical_metrics(parts["test"], synth, primary, audit, alpha)
                expected = synth.education.map(PUBLIC_EDUCATION_NUMBER_MAP)
                mapped = expected.notna()
                violation = float(synth.loc[mapped, "education-num"].ne(expected.loc[mapped]).mean())
                rows.append({"cell": str(cell.relative_to(ROOT)), "generator": cfg["generator"],
                             "partition": cfg["partition"], "k": cfg["k"], "seed": cfg["seed"],
                             "method": method, "replicate": rep, "draw_seed": seed,
                             "sample_type": name, "mapped_relation_violation": violation,
                             "allocation_counts": json.dumps(counts.tolist()),
                             "weight_l1": float(np.abs(w-alpha).sum()), **metrics})
    output = OUT / "projection" / cell.name
    output.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(rows).to_csv(output / "metrics.csv", index=False)
    (output / "complete.json").write_text(json.dumps({"status": "complete", "metrics_sha256": sha(output / "metrics.csv")}, indent=2)+"\n")


def summaries(cell: Path) -> None:
    cfg, alpha, models, parts, primary, audit = models_and_parts(cell)
    released = np.load(cell / "releases/permitted_summary.npz")
    H = released["H"]
    b = released["target_query_mean"]
    if H.shape != (len(primary.queries), cfg["k"]) or b.shape != (len(primary.queries),):
        raise ValueError("Saved pilot/workload shape mismatch")
    sets = {
        "one_way": [i for i, q in enumerate(primary.queries) if len(q.terms) == 1],
        "one_two_way": [i for i, q in enumerate(primary.queries) if 1 <= len(q.terms) <= 2],
        "full": list(range(len(primary.queries))),
    }
    output = OUT / "summary_ablation" / cell.name
    output.mkdir(parents=True, exist_ok=True)
    weights = {"size": alpha}
    certificates = {}
    for name, indices in sets.items():
        if not indices:
            raise ValueError("Summary access set empty")
        restricted_H, restricted_b = H[indices], b[indices]
        w, cert = constrained_query_minimax(restricted_H, restricted_b, alpha, .25, .5)
        weights[name] = w
        path = output / f"released_summary_{name}.npz"
        np.savez_compressed(path, H=restricted_H, b=restricted_b, alpha=alpha)
        certificates[name] = {"query_count": len(indices), "indices": indices,
                              "released_payload_bytes_npz": path.stat().st_size, **cert}
    (output / "weight_fits.json").write_text(json.dumps({
        "weights": {name: w.tolist() for name, w in weights.items()},
        "certificates": certificates, "access": "unnoised nonprivate aggregate summaries",
    }, indent=2)+"\n")
    rows = []
    for name, w in weights.items():
        for rep in range(REPEATS):
            seed = cfg["seed"] + 5200 + rep
            synth, counts = sample_mixture(models, w, ROWS, seed)
            metrics = empirical_metrics(parts["test"], synth, primary, audit, alpha)
            rows.append({"cell": str(cell.relative_to(ROOT)), "generator": cfg["generator"],
                         "partition": cfg["partition"], "k": cfg["k"], "seed": cfg["seed"],
                         "variant": name, "replicate": rep, "draw_seed": seed,
                         "allocation_counts": json.dumps(counts.tolist()),
                         "weight_l1": float(np.abs(w-alpha).sum()), **metrics})
    pd.DataFrame(rows).to_csv(output / "metrics.csv", index=False)
    (output / "complete.json").write_text(json.dumps({"status": "complete", "metrics_sha256": sha(output / "metrics.csv")}, indent=2)+"\n")


def run(kind: str) -> None:
    records = manifest(kind)
    resources = yaml.safe_load((ROOT / "configs/resources.yaml").read_text())
    lane = Path(os.path.expanduser(resources["shared_compute_lease"]))
    started = time.monotonic()
    with lane.open("a+") as handle:
        fcntl.flock(handle.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        for record in records:
            check_capacity(resources)
            cell = ROOT / record["source_cell"]
            output = OUT / ("projection" if kind == "projection" else "summary_ablation") / cell.name
            if (output / "complete.json").is_file():
                print(cell.name, "cached", flush=True)
                continue
            if time.monotonic()-started > resources["campaign_wall_seconds"]:
                raise TimeoutError("Mechanism invocation reached shared two-hour ceiling")
            try:
                (projection if kind == "projection" else summaries)(cell)
                print(cell.name, "complete", flush=True)
            except Exception as exc:
                output.mkdir(parents=True, exist_ok=True)
                (output / "failure.json").write_text(json.dumps({"status": "failed", "error": f"{type(exc).__name__}: {exc}"}, indent=2)+"\n")
                raise


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--kind", choices=("projection", "summaries"), required=True)
    ap.add_argument("--prepare-manifest", action="store_true")
    args = ap.parse_args()
    if args.prepare_manifest:
        print(len(manifest(args.kind)))
    else:
        run(args.kind)


if __name__ == "__main__":
    main()

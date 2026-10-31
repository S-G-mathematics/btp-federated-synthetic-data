"""Package only permitted Adult aggregate query means for maintained MBI."""
from __future__ import annotations

import argparse
import hashlib
import itertools
import json
from pathlib import Path

import numpy as np
import pandas as pd

import sys
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from btp.data import ALL_COLUMNS
from btp.privacy import public_schema
from btp.projected_workload import projected_workloads_v2

SOURCE = ROOT / "results/ec2_projected_v2_deterministic_20261024"
OUT = ROOT / "reports/published_references"
SPECS = (("age_education", 5, 101), ("age_education", 5, 202),
         ("label_skew", 10, 101), ("label_skew", 10, 202))


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def find_cell(partition: str, k: int, seed: int) -> Path:
    found = []
    for cell in SOURCE.iterdir():
        if not cell.is_dir():
            continue
        cfg = json.loads((cell / "configuration.json").read_text())
        if (cfg["generator"], cfg["partition"], cfg["k"], cfg["seed"]) == ("copula", partition, k, seed):
            found.append(cell)
    if len(found) != 1:
        raise ValueError(f"Expected one corrected copula source: {partition}, K{k}, seed{seed}")
    return found[0]


def domain_for_workloads(primary, audit, schema: dict) -> dict:
    domain = {}
    all_queries = [*primary.queries, *audit.queries]
    for column in ALL_COLUMNS:
        if column in schema["numeric_ranges"]:
            lo, hi = map(int, schema["numeric_ranges"][column])
            cuts = {lo, hi+1}
            if column == "education-num":
                cuts.update(range(lo, hi+2))
            for query in all_queries:
                for c, op, value in query.terms:
                    if c != column:
                        continue
                    if op == "le": cuts.add(int(value)+1)
                    elif op == "gt": cuts.add(int(value)+1)
                    elif op == "eq": cuts.update((int(value), int(value)+1))
                    elif op == "between": cuts.update((int(value[0]), int(value[1])+1))
            if column in ("capital-gain", "capital-loss"):
                cuts.update((0, 1))
            edges = sorted(v for v in cuts if lo <= v <= hi+1)
            intervals = [[int(a), int(b-1)] for a, b in zip(edges[:-1], edges[1:])]
            if not intervals or intervals[0][0] != lo or intervals[-1][1] != hi:
                raise ValueError(f"Invalid public numeric domain for {column}")
            domain[column] = {"kind": "integer_interval", "values": intervals}
        else:
            domain[column] = {"kind": "category", "values": list(schema["categories"][column])}
    return domain


def clique_for_query(query) -> tuple[str, ...]:
    if query.name == "education_number_relation_violation_v2":
        used = {"education", "education-num"}
    else:
        used = {term[0] for term in query.terms}
    if not used:
        raise ValueError(f"Unknown empty-term query: {query.name}")
    return tuple(c for c in ALL_COLUMNS if c in used)


def representative(spec: dict, code: int, endpoint: str = "middle"):
    value = spec["values"][code]
    if spec["kind"] == "category":
        return value
    if endpoint == "lower": return value[0]
    if endpoint == "upper": return value[1]
    return (value[0]+value[1])//2


def mask_for_query(query, clique: tuple[str, ...], domain: dict) -> list[float]:
    mask = []
    sizes = [len(domain[c]["values"]) for c in clique]
    for codes in itertools.product(*(range(n) for n in sizes)):
        values = {c: representative(domain[c], code) for c, code in zip(clique, codes)}
        middle = float(query.evaluate(pd.DataFrame([values]))[0])
        for endpoint in ("lower", "upper"):
            trial = {c: representative(domain[c], code, endpoint) for c, code in zip(clique, codes)}
            if float(query.evaluate(pd.DataFrame([trial]))[0]) != middle:
                raise ValueError(f"Public domain does not represent query exactly: {query.name}")
        mask.append(middle)
    return mask


def prepare() -> None:
    schema = public_schema()
    primary, audit = projected_workloads_v2(schema)
    domain = domain_for_workloads(primary, audit, schema)
    masks = [(q.name, clique_for_query(q), mask_for_query(q, clique_for_query(q), domain))
             for q in primary.queries]
    OUT.mkdir(parents=True, exist_ok=True)
    cells = []
    for partition, k, seed in SPECS:
        source = find_cell(partition, k, seed)
        cfg = json.loads((source / "configuration.json").read_text())
        if cfg["workload_version"] != "projected_v2" or cfg["reference_role"] != "development_assessment":
            raise ValueError("Reference source outside corrected development")
        summary = np.load(source / "releases/permitted_summary.npz")
        b = summary["target_query_mean"]
        if b.shape != (len(primary.queries),) or not np.isfinite(b).all():
            raise ValueError("Aggregate calibration query means missing")
        name = f"pgm_{partition}_k{k}_s{seed}"
        target = OUT / name
        target.mkdir(parents=True, exist_ok=True)
        package = {"name": name, "source_cell": str(source.relative_to(ROOT)),
                   "source_config_sha256": sha(source / "configuration.json"),
                   "source_released_summary_sha256": sha(source / "releases/permitted_summary.npz"),
                   "access": "aggregate unnoised calibration query means and public domain only; nonprivate",
                   "domain": domain, "known_total": 1.0, "stddev": 1.0,
                   "stddev_interpretation": "common objective scale, no synthetic DP noise",
                   "measurements": [{"query": q, "clique": clique, "mask": mask,
                                     "value": float(value)}
                                    for (q, clique, mask), value in zip(masks, b)],
                   "optimizer": {"name": "maintained MBI UniversalAcceleratedMethod",
                                 "iters": 500, "tol": None},
                   "sampling": {"rows": 10000, "repeats": 5,
                                "seeds": [seed+5200+rep for rep in range(5)]},
                   "public_projection": "education-to-education-number map after discrete sampling"}
        path = target / "measurement_package.json"
        if path.exists():
            if json.loads(path.read_text()) != package:
                raise ValueError("Existing PGM measurement package differs")
        else:
            path.write_text(json.dumps(package, sort_keys=True, separators=(",", ":")) + "\n")
        cells.append({"name": name, "source_cell": package["source_cell"],
                      "measurement_package_sha256": sha(path), "status": "prepared"})
    (OUT / "pgm_cell_manifest.json").write_text(json.dumps({"cells": cells,
        "mbi_commit": "9429881f0f21ef413424f6011b9d6ae20728176d",
        "notes": "No real rows or extra marginals are in measurement packages"}, indent=2)+"\n")
    print(json.dumps({"prepared_cells": len(cells), "queries": len(masks),
                      "domain_sizes": {c: len(s["values"]) for c, s in domain.items()}}))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--prepare", action="store_true", required=True)
    parser.parse_args()
    prepare()

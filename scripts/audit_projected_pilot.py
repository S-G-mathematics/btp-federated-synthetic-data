"""Audit one version-2 projected Exp 1/2 development pilot."""
from __future__ import annotations

import argparse
import hashlib
import json
import pickle
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from btp.privacy import PUBLIC_EDUCATION_NUMBER_MAP
from btp.projection import EducationNumberProjection


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--cell", type=Path, required=True)
    ap.add_argument("--out", type=Path, required=True)
    args = ap.parse_args()
    cell, out = args.cell, args.out
    cfg = json.loads((cell / "configuration.json").read_text())
    assert cfg["workload_version"] == "projected_v2"
    assert cfg["reference_role"] == "development_assessment"
    assert cfg["profile"]["repeats"] == 5
    assert (cell / "exp01_complete.json").is_file()
    assert (cell / "exp02_complete.json").is_file()
    release = json.loads((cell / "releases/release_contract.json").read_text())
    assert release["public_education_number_map"] == PUBLIC_EDUCATION_NUMBER_MAP
    assert release["formal_dp"] is False
    workload_bytes = (cell / "workloads.json").read_bytes()
    workloads = json.loads(workload_bytes)
    assert workloads["calibration"][-1]["name"] == "education_number_relation_violation_v2"
    assert workloads["unseen_audit"][-1]["name"] == "audit:Bachelors_num13_income_high_v2"
    map_bytes = json.dumps(PUBLIC_EDUCATION_NUMBER_MAP, sort_keys=True,
                           separators=(",", ":")).encode()
    models = [pickle.loads(path.read_bytes()) for path in sorted((cell / "releases").glob("client_*.pkl"))]
    assert len(models) == cfg["k"] and all(isinstance(m, EducationNumberProjection) for m in models)
    assert all(m.likelihood_kind == "exact_discretized" for m in models)
    fits = json.loads((cell / "weight_fits.json").read_text())
    failed = [r["method"] for r in fits["methods"] if not r["success"]]
    exp1 = pd.read_csv(cell / "exp01_test.csv")
    repeated = exp1.groupby("method").replicate.nunique()
    assert repeated.eq(5).all()
    selected = json.loads((cell / "selection_frozen.json").read_text())
    assert not selected["audit_used_for_selection"] and not selected["test_used"]
    synthetic = pd.read_csv(cell / "synthetic_selected.csv.gz")
    expected = synthetic.education.map(PUBLIC_EDUCATION_NUMBER_MAP)
    known = expected.notna()
    mapped_mismatch = int(synthetic.loc[known, "education-num"].ne(expected.loc[known]).sum())
    assert mapped_mismatch == 0
    assert len(synthetic) == cfg["profile"]["synthetic_rows"]
    means = exp1.groupby("method")[["query_linf", "unseen_query_linf", "invalid_income_rate"]].mean()
    means["delta_vs_size"] = means.query_linf - means.loc["size", "query_linf"]
    means["audit_delta_vs_size"] = means.unseen_query_linf - means.loc["size", "unseen_query_linf"]
    out.mkdir(parents=True, exist_ok=True)
    means.reset_index().to_csv(out / "method_means.csv", index=False)
    summary = {
        "cell": str(cell), "status": "completed_development_pilot",
        "code_hash": cfg["code_hash"], "reference_role": cfg["reference_role"],
        "generator": cfg["generator"], "partition": cfg["partition"],
        "clients": cfg["k"], "seed": cfg["seed"],
        "selected_within_cell": selected["method"], "failed_weight_fits": failed,
        "method_count": int(len(means)), "repeats_per_method": 5,
        "synthetic_rows": int(len(synthetic)),
        "mapped_education_rows": int(known.sum()),
        "unmapped_education_rows": int((~known).sum()),
        "known_education_mismatches": mapped_mismatch,
        "public_map_canonical_bytes": len(map_bytes),
        "public_map_sha256": hashlib.sha256(map_bytes).hexdigest(),
        "serialized_workloads_sha256": hashlib.sha256(workload_bytes).hexdigest(),
        "primary_query_count": len(workloads["calibration"]),
        "audit_query_count": len(workloads["unseen_audit"]),
        "released_model_checkpoint_bytes": int(sum(p.stat().st_size for p in (cell / "releases").glob("client_*.pkl"))),
        "aggregate_summary_bytes": int((cell / "releases/permitted_summary.npz").stat().st_size),
        "release_contract_file_bytes": int((cell / "releases/release_contract.json").stat().st_size),
        "size_query_linf": float(means.loc["size", "query_linf"]),
        "selected_query_linf": float(means.loc[selected["method"], "query_linf"]),
        "selected_delta_vs_size": float(means.loc[selected["method"], "delta_vs_size"]),
        "selected_audit_delta_vs_size": float(means.loc[selected["method"], "audit_delta_vs_size"]),
        "fixed_pilot_oracle_lp_success": bool(json.loads((cell / "exp02_oracle.json").read_text())["solver"]["success"]),
        "formal_dp": False, "official_test_used": False,
    }
    (out / "audit.json").write_text(json.dumps(summary, indent=2) + "\n")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()

"""Postpilot matched bridge from legacy public bins to declared zero atoms."""
from __future__ import annotations

import fcntl
import json
import os
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import yaml

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT), str(ROOT / "scripts")]
from btp.evaluation import empirical_metrics, sample_mixture
from btp.privacy import fit_nonprivate_public_histogram, public_schema
from btp.projected_workload import projected_workloads_v2
from eval_public_atom_privacy import client_train_parts, mapping_violation, rate
from representation_constrained import reference_parts

SOURCE = ROOT / "results/ec2_projected_v2_deterministic_20261024"
ATOM = ROOT / "results/public_atom_privacy_20261024"
OUT = ROOT / "reports/public_atom_legacy_bridge_20261024"


def main() -> None:
    resources = yaml.safe_load((ROOT / "configs/resources.yaml").read_text())
    lease = Path(os.path.expanduser(resources["shared_compute_lease"]))
    rows = []
    with lease.open("a+") as handle:
        fcntl.flock(handle.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        for generator, partition, k in (("chow_liu", "age", 5), ("mixed_gmm", "label_skew", 10)):
            for seed in (101, 202, 303):
                matches = list(SOURCE.glob(f"{generator}_{partition}_k{k}_s{seed}_*"))
                if len(matches) != 1:
                    raise ValueError("Missing fixed bridge cell")
                cell, = matches
                cfg = json.loads((cell / "configuration.json").read_text())
                prior = pd.read_csv(ATOM / cell.name / "metrics.csv")
                prior = prior.loc[prior.method == "nonprivate"].sort_values("replicate")
                train = client_train_parts(cell, cfg)
                alpha = np.asarray(json.loads((cell / "partition.json").read_text())["alpha"], float)
                reference = reference_parts(cell, cfg, alpha)["test"]
                workload, audit = projected_workloads_v2(public_schema())
                models = [fit_nonprivate_public_histogram(part,
                    schema=public_schema(n_public=len(part), bins=8)) for part in train]
                for row in prior.itertuples(index=False):
                    synthetic, counts = sample_mixture(models, alpha, 10000, int(row.synthetic_seed))
                    if counts.sum() != 10000:
                        raise RuntimeError("Legacy allocation mismatch")
                    metrics = empirical_metrics(reference, synthetic, workload, audit, alpha)
                    rows.append({"family": f"{generator}_{partition}_k{k}", "seed": seed,
                        "replicate": int(row.replicate), "synthetic_seed": int(row.synthetic_seed),
                        "legacy_query_linf": metrics["query_linf"],
                        "atom_query_linf": float(row.query_linf),
                        "legacy_gain_zero_abs_error": abs(synthetic["capital-gain"].eq(0).mean()
                            - rate(reference, alpha, "capital-gain")),
                        "atom_gain_zero_abs_error": abs(float(row.synthetic_gain_zero)
                            - float(row.real_alpha_gain_zero)),
                        "legacy_mapped_education_violation": mapping_violation(
                            synthetic, public_schema()["education_number_map"]),
                        "atom_mapped_education_violation": float(row.mapped_education_violation)})
    frame = pd.DataFrame(rows)
    if len(frame) != 30:
        raise RuntimeError("Incomplete legacy bridge")
    summary = frame.groupby("family", as_index=False).agg(
        legacy_query_linf_mean=("legacy_query_linf", "mean"),
        atom_query_linf_mean=("atom_query_linf", "mean"),
        legacy_gain_zero_abs_error_mean=("legacy_gain_zero_abs_error", "mean"),
        atom_gain_zero_abs_error_mean=("atom_gain_zero_abs_error", "mean"),
        legacy_mapped_education_violation_mean=("legacy_mapped_education_violation", "mean"),
        atom_mapped_education_violation_mean=("atom_mapped_education_violation", "mean"))
    OUT.mkdir(parents=True, exist_ok=True)
    frame.to_csv(OUT / "paired_draws.csv", index=False)
    summary.to_csv(OUT / "summary.csv", index=False)
    (OUT / "LIMITS.md").write_text("Postpilot structural bridge; old and atom histograms use the same train partitions, alpha, workload, 10,000 rows and public sample seeds. The comparison changes both zero atoms and education projection, so the query error difference is not an isolated zero-atom effect. All methods are nonprivate here; no official Adult test was evaluated.\n")
    print(summary.to_string(index=False))


if __name__ == "__main__":
    main()

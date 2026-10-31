"""Inventory serialized projected-campaign releases and privileged artifacts."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import pandas as pd


def inventory(root: Path, out: Path) -> None:
    rows = []
    cells = sorted(path for path in root.iterdir() if (path / "configuration.json").exists())
    core = []
    for cell in cells:
        cfg = json.loads((cell / "configuration.json").read_text())
        if (cfg["generator"] not in {"chow_liu", "copula", "mixed_gmm"}
            or cfg["partition"] not in {"age", "age_education", "label_skew"}):
            continue
        core.append(cell)
        client_models = sorted((cell / "releases").glob("client_*.pkl"))
        if len(client_models) != cfg["k"]:
            raise ValueError(f"Missing client release: {cell}")
        paths = {
            "fitted_client_models": client_models,
            "unnoised_aggregate_query_kernel_summary": [cell / "releases/permitted_summary.npz"],
            "server_derived_operator_checkpoints": sorted(
                path for path in (cell / "releases").glob("*.pkl")
                if not path.name.startswith("client_")),
            "declared_client_mass_assignment_metadata": [cell / "partition.json"],
            "public_workload_and_release_contract": [cell / "workloads.json",
                                                    cell / "releases/release_contract.json"],
            "server_derived_weights_including_privileged_track": [cell / "weight_fits.json"],
            "privileged_row_partition_manifest_not_a_release": [cell / "partition_manifest.csv"],
            "client_private_tuning_not_a_release": sorted((cell / "client_private").glob("*")),
            "evaluator_private_artifacts_not_a_release": sorted((cell / "evaluator_private").glob("*")),
        }
        for category, files in paths.items():
            if (category in {"fitted_client_models", "unnoised_aggregate_query_kernel_summary",
                             "declared_client_mass_assignment_metadata",
                             "public_workload_and_release_contract",
                             "server_derived_weights_including_privileged_track"}
                and not files) or any(not path.exists() for path in files):
                raise ValueError(f"Missing declared artifact category {category}: {cell}")
            rows.append({"cell": cell.name, "generator": cfg["generator"],
                         "partition": cfg["partition"], "k": cfg["k"], "seed": cfg["seed"],
                         "category": category, "files": len(files),
                         "serialized_disk_bytes": sum(path.stat().st_size for path in files),
                         "paths": json.dumps([str(path.relative_to(cell)) for path in files])})
    if len(core) != 54:
        raise ValueError(f"Expected 54 core cells, found {len(core)}")
    frame = pd.DataFrame(rows)
    overview = frame.groupby("category", as_index=False).agg(
        cells=("cell", "nunique"), total_files=("files", "sum"),
        total_serialized_disk_bytes=("serialized_disk_bytes", "sum"),
        mean_bytes_per_cell=("serialized_disk_bytes", "mean"),
        min_bytes_per_cell=("serialized_disk_bytes", "min"),
        max_bytes_per_cell=("serialized_disk_bytes", "max"))
    out.mkdir(parents=True, exist_ok=True)
    frame.to_csv(out / "per_cell_artifacts.csv", index=False)
    overview.to_csv(out / "category_summary.csv", index=False)
    (out / "configuration.json").write_text(json.dumps({
        "source_root": str(root), "scope": "54 projected core development cells",
        "measurement": "serialized file sizes on EC2 disk, not actual network traffic",
        "main_pipeline_formal_dp": False,
        "privileged_scores_have_greater_access": True,
        "official_test_used": False,
    }, indent=2) + "\n")
    print(overview.to_string(index=False))


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    inventory(args.root, args.out)


if __name__ == "__main__":
    main()

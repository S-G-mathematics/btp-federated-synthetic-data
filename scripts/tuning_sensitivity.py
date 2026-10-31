"""Development-only sensitivity audit for local generator tuning boundaries."""
import csv
import json
import pickle
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from btp.data import build_partition_rule, prepare_splits
from btp.evaluation import public_workloads
from btp.models import fit_model
from btp.privacy import public_schema

SEED = 101
K = 5
PROFILE = "pilot"
GENERATORS = ("independent", "chow_liu", "copula", "mixed_gmm")


def main():
    out = ROOT / "reports" / "tuning_sensitivity_20261024"
    out.mkdir(parents=True, exist_ok=True)
    schema = public_schema()
    workload, _ = public_workloads(schema)
    splits = prepare_splits(ROOT / "data" / "raw", seed=SEED)
    rule = build_partition_rule(splits["train"], K, "age", SEED, .8)
    train = [splits["train"].loc[rule.assign(splits["train"]) == i] for i in range(K)]
    tune = [splits["tune"].loc[rule.assign(splits["tune"]) == i] for i in range(K)]
    result_root = ROOT / "results" / "ec2_pilot_gls_fixed_20261024"
    rows = []
    for generator in GENERATORS:
        cell = next(p for p in result_root.iterdir() if p.name.startswith(generator + "_age_"))
        for client in range(K):
            selected_params = json.loads((cell / "client_private" / f"tuning_{client}.json").read_text())["selected"]
            selected_model = pickle.loads((cell / "releases" / f"client_{client}.pkl").read_bytes())
            extras = ([{"components": c, "alpha": a, "max_iter": 300, "n_init": 2}
                       for c in (12, 16) for a in (.1, 1.)] if generator == "mixed_gmm" else
                      [{"bins": 64, "alpha": a} for a in (.1, 1.)])
            target = workload.mean(tune[client])
            for setting_index, (kind, params, model) in enumerate(
                [("selected_grid", selected_params, selected_model)] +
                [("extra", params, None) for params in extras]
            ):
                if model is None:
                    settings = {**params, "numeric_bounds": schema["numeric_ranges"],
                                "category_vocab": schema["categories"]}
                    model = fit_model(generator, train[client],
                                      SEED + 31 * client + 1000 + setting_index, settings)
                errors = []
                for rep in range(3):
                    sample = model.sample(1000, 1701 + rep)
                    errors.append(float(np.mean(np.abs(target - workload.mean(sample)))))
                gmm = getattr(model, "gmm", None)
                rows.append({"generator": generator, "client": client, "kind": kind,
                             "parameters": json.dumps(params, sort_keys=True),
                             "train_rows": len(train[client]), "tune_rows": len(tune[client]),
                             "query_mae_mean": float(np.mean(errors)),
                             "query_mae_std": float(np.std(errors, ddof=1)),
                             "gmm_converged": None if gmm is None else bool(gmm.converged_),
                             "gmm_iterations": None if gmm is None else int(gmm.n_iter_),
                             "gmm_lower_bound": None if gmm is None else float(gmm.lower_bound_),
                             "reference_role": "local_tune_only"})
            print(generator, client, "checked", 1 + len(extras), "settings", flush=True)
    with (out / "local_tuning_sensitivity.csv").open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    (out / "scope.json").write_text(json.dumps({"seed": SEED, "partition": "age", "clients": K,
        "repeats_per_setting": 3, "synthetic_rows_per_repeat": 1000,
        "reference_role": "local_tune_only", "source_results": str(result_root),
        "purpose": "diagnose upper-edge tuning choices; not a final method selection"}, indent=2) + "\n")
    print("Wrote", out / "local_tuning_sensitivity.csv", flush=True)


if __name__ == "__main__":
    main()

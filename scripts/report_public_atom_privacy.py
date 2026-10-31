"""Audit matched public zero-atom private/nonprivate histogram outputs."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import pandas as pd


def markdown(frame: pd.DataFrame) -> str:
    cols = list(frame.columns)
    lines = ["| " + " | ".join(cols) + " |", "| " + " | ".join("---" for _ in cols) + " |"]
    for row in frame.itertuples(index=False, name=None):
        lines.append("| " + " | ".join(f"{x:.6f}" if isinstance(x, float) else str(x) for x in row) + " |")
    return "\n".join(lines)


def report(root: Path, out: Path) -> None:
    files = sorted(root.glob("*/configuration.json"))
    if len(files) != 6:
        raise ValueError(f"Expected six completed privacy cells, found {len(files)}")
    metrics, attacks = [], []
    for path in files:
        cfg = json.loads(path.read_text())
        if cfg["status"] != "complete" or cfg["official_test_used"]:
            raise ValueError(f"Invalid privacy cell: {path}")
        name = path.parent.name
        family = "chow_liu_age_k5" if name.startswith("chow_liu_age_k5_") else "mixed_gmm_label_skew_k10"
        split_seed = int(name.split("_s")[-1].split("_")[0])
        frame = pd.read_csv(path.parent / "metrics.csv")
        attack = pd.read_csv(path.parent / "membership_diagnostic.csv")
        ledger = json.loads((path.parent / "privacy_ledger.json").read_text())
        if (len(frame) != 20 or set(frame.method) != {"nonprivate", "epsilon_1", "epsilon_4", "epsilon_8"}
            or frame.groupby("method").size().min() != 5
            or frame.mapped_education_violation.max() != 0
            or frame.invalid_income_rate.max() != 0
            or ledger["sum_epsilons_if_all_private_settings_released_per_client_same_cell"] != 13
            or ledger["full_pipeline_dp"]):
            raise ValueError(f"Privacy metric/ledger failure: {path.parent}")
        for item in ledger["individual_client_releases"]:
            if item["method"] == "nonprivate":
                if item["formal_dp_eligible"]:
                    raise ValueError("Nonprivate model mislabeled DP")
            elif (not item["formal_dp_eligible"] or item["noise_seed_mode"] != "fresh_os_entropy"
                  or "seed" in item):
                raise ValueError("Private model noise ledger invalid")
        frame.insert(0, "family", family)
        frame.insert(1, "split_seed", split_seed)
        attack.insert(0, "family", family)
        attack.insert(1, "split_seed", split_seed)
        metrics.append(frame)
        attacks.append(attack)
    metrics = pd.concat(metrics, ignore_index=True)
    attacks = pd.concat(attacks, ignore_index=True)
    metrics["gain_zero_abs_error"] = (metrics.synthetic_gain_zero-metrics.real_alpha_gain_zero).abs()
    metrics["loss_zero_abs_error"] = (metrics.synthetic_loss_zero-metrics.real_alpha_loss_zero).abs()
    by_cell = metrics.groupby(["family", "split_seed", "method"], as_index=False).agg(
        query_linf_mean=("query_linf", "mean"),
        unseen_query_linf_mean=("unseen_query_linf", "mean"),
        gain_zero_abs_error_mean=("gain_zero_abs_error", "mean"),
        loss_zero_abs_error_mean=("loss_zero_abs_error", "mean"),
        model_bytes=("model_bytes", "first"),
        fit_seconds=("fit_seconds", "first"))
    by_family = by_cell.groupby(["family", "method"], as_index=False).agg(
        query_linf_mean=("query_linf_mean", "mean"),
        query_linf_min_seed=("query_linf_mean", "min"),
        query_linf_max_seed=("query_linf_mean", "max"),
        unseen_query_linf_mean=("unseen_query_linf_mean", "mean"),
        gain_zero_abs_error_mean=("gain_zero_abs_error_mean", "mean"),
        loss_zero_abs_error_mean=("loss_zero_abs_error_mean", "mean"),
        model_bytes_mean=("model_bytes", "mean"))
    attack_summary = attacks.groupby(["family", "method"], as_index=False).agg(
        client_models=("client", "size"),
        mean_likelihood_membership_auc=("likelihood_membership_auc", "mean"),
        min_likelihood_membership_auc=("likelihood_membership_auc", "min"),
        max_likelihood_membership_auc=("likelihood_membership_auc", "max"),
        finite_score_fraction_min=("finite_score_fraction", "min"))
    out.mkdir(parents=True, exist_ok=True)
    metrics.to_csv(out / "all_draws.csv", index=False)
    by_cell.to_csv(out / "by_cell.csv", index=False)
    by_family.to_csv(out / "by_family.csv", index=False)
    attacks.to_csv(out / "membership_diagnostics.csv", index=False)
    attack_summary.to_csv(out / "membership_summary.csv", index=False)
    (out / "OVERVIEW.md").write_text("\n".join([
        "# Public zero-atom histogram development audit", "",
        "Six fixed Adult development cells, five public synthetic draws per mechanism. The private and nonprivate histograms share the same public zero atoms, bins and education projection. Official Adult test was not evaluated.", "",
        markdown(by_family), "",
        "## Likelihood membership diagnostic (not a DP proof)", "",
        markdown(attack_summary), "",
        "A single fresh-noise private histogram release per fixed public client membership/size has its stated epsilon-DP scope. Publishing all three epsilon settings on one client would compose to epsilon=13. The research bundle also contains nonprivate releases and raw data; the full pipeline is not DP. Overlapping split seeds and data-dependent assignment are outside the single-release guarantee.", "",
    ]))
    print(by_family.to_string(index=False))
    print(attack_summary.to_string(index=False))


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    report(args.root, args.out)


if __name__ == "__main__":
    main()

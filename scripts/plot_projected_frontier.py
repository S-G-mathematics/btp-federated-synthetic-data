"""Plot version-2 development fidelity against client-mass shift from CSV."""
from __future__ import annotations

import argparse
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--selected", type=Path, required=True)
    ap.add_argument("--constrained", type=Path, required=True)
    ap.add_argument("--out", type=Path, required=True)
    args = ap.parse_args()
    selected = pd.read_csv(args.selected)
    constrained = pd.read_csv(args.constrained)
    constrained = constrained.loc[constrained.method.eq("constrained")]
    colors = {"chow_liu": "#2a9d8f", "copula": "#457b9d", "mixed_gmm": "#e76f51"}
    fig, ax = plt.subplots(figsize=(8.5, 5.4))
    for generator, color in colors.items():
        s = selected.loc[selected.generator.eq(generator)]
        c = constrained.loc[constrained.generator.eq(generator)]
        assert len(s) == 6 and len(c) == 6
        ax.scatter(s.mean_weight_l1, s.mean_paired_delta, marker="o", s=55,
                   color=color, label=f"{generator}: selected rule", alpha=.9)
        ax.scatter(c.mean_weight_l1, c.mean_paired_delta, marker="x", s=85,
                   color=color, label=f"{generator}: constrained rule", alpha=.9)
    ax.scatter([0], [0], marker="s", color="black", s=42, label="size baseline")
    ax.axhline(0, color="0.55", linewidth=.8)
    ax.axhline(-.005, color="green", linestyle="--", linewidth=1,
               label="practical gain margin")
    ax.axvline(.25, color="black", linestyle=":", linewidth=1,
               label="registered L1 limit")
    ax.set(xlabel="Mean L1 shift from fixed client masses alpha",
           ylabel="Mean paired query-max difference vs size",
           title="Adult projected v2 development: three overlapping split seeds per slice")
    ax.grid(alpha=.2)
    ax.legend(fontsize=7, ncol=2, loc="upper right")
    fig.tight_layout()
    args.out.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(args.out, dpi=180)
    print(args.out)


if __name__ == "__main__":
    main()

# Repository reading guide

## For a supervisor

1. Read [results and statistical inference](RESULTS_AND_STATISTICAL_INFERENCE.md) for paired means, medians, ranges, adverse outcomes and inference limits.
2. Read [the twelve acceptance rows](../AUTHOR_READY/TWELVE_PACKAGE_ACCEPTANCE.md) for exactly what closed.
3. Use [the claim map](../results/summaries/claim_to_evidence.csv) to inspect the evidence behind a sentence.
4. Read [the formal statement register](../theory/statements.md) to distinguish definitions, proofs, conditional derivations and open targets.

## For reproduction

The original executable layout is `btp/`, `scripts/`, `configs/` and `tests/`. The [lightweight workflow](../REPRODUCIBILITY.md) rebuilds results from saved evidence. `python scripts/build_statistical_synthesis.py` adds the paired descriptive synthesis. [Artifacts](../ARTIFACTS.md) explains the private full archive, checkpoint trust and exact hash. No full campaign runs during installation.

## Canonical and historical files

| Location | Purpose |
| --- | --- |
| `reports/statistical_synthesis/` | New descriptive synthesis of saved cell means; input hashes retained |
| `results/summaries/` | Closure, headline and claim indexes |
| `figures/main/` | Rebuildable presentation gallery |
| `AUTHOR_READY/PAPER_TABLES/` | Dated editable writing tables and captions |
| `experiments/exp*/README.md` | Per-package questions, scope and evidence links |
| `reports/` and `results/` dated directories | Original saved analysis and cell records; historical/current roles remain separate |
| `docs/` dated protocols and root progress reports | Chronology, original decisions and repairs; not the current landing page |
| `provenance/` and `artifacts/` | Source mapping, hashes, software and large-file availability |

Historical files are retained because removing them would break provenance and hide failed or superseded analyses. They are not additional independent evidence. Generated tables/figures are marked in `.gitattributes` to keep code review focused. Cache files, environments and temporary packaging files are excluded. Source archives remain unchanged.

The main statistical release is nonprivate. Test people recur across configurations. No new result in the descriptive synthesis is a prospective confirmation or method-selection input.

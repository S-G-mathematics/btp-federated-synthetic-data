# Reproducibility levels

1. `python scripts/verify_data_sources.py` checks the included official Adult and Bank source archive/member hashes.
2. `python scripts/audit_repository.py` checks source-map hashes, 12 closure links, claim links, the immutable freeze, key corrected-core/draw counts and relative documentation links.
3. `python scripts/reproduce_repository.py --tables` invokes the original saved-result builder. It regenerates `reports/final_build/` CSVs, JSON and PNG panels plus the normalized primary/claim summaries, without fitting or official-test reselection.
4. `python scripts/reproduce_repository.py --figures` regenerates the 15 original PNG panels and three headline PNG/PDF/SVG figures from saved CSV inputs in `figures/main/`.
5. `python -m pytest -q` runs the original scientific toy/test suite. Fresh packaging runs and timestamps are in `logs/packaging/validation.json`; GitHub CI runs the same lightweight checks.
6. `python scripts/check_theory_examples.py` checks the deterministic arithmetic behind the size-weight counterexample, a dual-certificate example and sharp representation bound. It is not a proof checker or an empirical experiment.
7. `python scripts/check_documentation_release.py` verifies hashes of the later proof/report artifacts, the 27 statement labels and all 29 historical-to-current mappings.

The proof PDF is rebuilt with two passes of `pdflatex -halt-on-error proofs.tex` in `theory/`. TeX is only needed to rebuild the PDF; the lightweight Python checks use the included source and PDF. [Writing packages](paper/README.md) provide separate editable source ZIPs and build instructions. The 31 October documentation release does not rerun frozen model training, query selection or official-test scoring.

Full model/draw replay needs the trusted private v2 archive, Python 3.12 pinned environment and the shared EC2 controller. [Artifact access](ARTIFACTS.md) and the original [full reproduction guide](REPRODUCE.md) give exact roles and commands. Historical 91-test logs are distinct from packaging-time checks. Only trusted, hash-verified pickle checkpoints should be loaded.


# Reproducibility levels

1. `python scripts/verify_data_sources.py` checks the included official Adult and Bank source archive/member hashes.
2. `python scripts/audit_repository.py` checks source-map hashes, 12 closure links, claim links, the immutable freeze, key corrected-core/draw counts and relative documentation links.
3. `python scripts/reproduce_repository.py --tables` invokes the original saved-result builder. It regenerates `reports/final_build/` CSVs, JSON and PNG panels plus the normalized primary/claim summaries, without fitting or official-test reselection.
4. `python scripts/reproduce_repository.py --figures` regenerates the 15 original PNG panels and three headline PNG/PDF/SVG figures from saved CSV inputs in `figures/main/`.
5. `python -m pytest -q` runs the original scientific toy/test suite. Fresh packaging runs and timestamps are in `logs/packaging/validation.json`; GitHub CI runs the same lightweight checks.

Full model/draw replay needs the trusted private v2 archive, Python 3.12 pinned environment and the shared EC2 controller. [Artifact access](ARTIFACTS.md) and the original [full reproduction guide](REPRODUCE.md) give exact roles and commands. Historical 91-test logs are distinct from packaging-time checks. Only trusted, hash-verified pickle checkpoints should be loaded.

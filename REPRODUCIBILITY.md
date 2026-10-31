# Reproducibility levels

1. `python scripts/audit_repository.py` verifies repository evidence links, hashes, main counts and archived provenance.
2. `python scripts/reproduce_repository.py --tables` runs the original saved-result report builder. It does not refit or score official test.
3. `python scripts/reproduce_repository.py --figures` copies the regenerated scientific figures to the gallery.
4. `python -m pytest -q` runs scientific tests.
5. Full model/draw replay needs the trusted v2 archive, Python 3.12 pinned environment, and the shared EC2 controller. See `REPRODUCE.md`. Historical 91 tests and clean extraction are not represented as fresh checks unless separately logged under `logs/packaging/`.

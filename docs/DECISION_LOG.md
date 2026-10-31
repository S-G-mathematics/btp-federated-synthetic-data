# Airbag decision log

- 2026-10-24: Isolated EC2 namespace and separate result roots preserve bundled evidence. See `DECISIONS.md`.
- 2026-10-24: Fixed heavy-profile EC2 guard to use readable DMI vendor/product fields after the live UUID permission failure. See `scripts/run_campaign.py` and pilot launch record.
- 2026-10-24: The Luna worker sandbox failure is an audit failure, not a scientific result. Continue coordinator source review without enabling a broader sandbox solely for delegation.

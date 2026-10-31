# UCI Adult data

The files in `raw/` are the official UCI Machine Learning Repository Adult
(also called Census Income) dataset files. Cite them as:

> Becker, B. & Kohavi, R. (1996). Adult [Dataset]. UCI Machine Learning
> Repository. https://doi.org/10.24432/C5XW20

UCI lists the dataset under the Creative Commons Attribution 4.0 International
(CC BY 4.0) license: <https://creativecommons.org/licenses/by/4.0/>. Attribution
is required. This project does not imply endorsement by the authors or UCI.

The prepared data protocol preserves all rows and the official train/test
boundary, strips surrounding whitespace, normalizes the official test label
period, and retains `?` as a categorical missing-value marker. Exact records
present in both official source partitions are removed from development and
listed in the quarantine split. Remaining official training rows are divided
by duplicate group into train/tune/calibration/validation. See
[`../docs/DATA_PROTOCOL.md`](../docs/DATA_PROTOCOL.md) and
`data_manifest.json` for the reproducibility manifest and raw-file SHA-256
hashes. The manifest is generated with `python scripts/validate_data.py` from
the project directory.

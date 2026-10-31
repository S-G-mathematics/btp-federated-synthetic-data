# Published Genuity comparison (2026-10-24 UTC)

## Package and license

The local D: tree was inspected for APIs and model behavior. No local source,
wheel, signing key or package archive was copied to EC2. The published PyPI
`genuity==2.0.2` Linux CPython 3.12 wheel was installed directly into a
separate EC2 `genuity_env`; the BTP pinned `.venv` was not modified. Its
installed environment is frozen in `logs/genuity_env_dependencies.freeze.txt`.

The first local report token had an invalid signature; `.env` and catalogued
CSV keys were expired. The user authorized issuing a replacement with the
local repository's existing signing tool/key. It was signed locally on D:,
kept at the report's existing 2026-12-01 17:34:01 UTC expiry, locally verified,
then stored outside the local Git repository at
`D:\genuity-license-private\btp_license_20261024.txt`. Only the token was
transferred to `../private/genuity_license.txt` (directory 0700, file 0600). The published wheel activated and returned `active=True`. The
signing key never left D:. Neither token nor signing key appears in project
source, result files or logs. The invalid first token remains in the private
EC2 directory only for audit.

## Protocol boundary

`KDEGenerator` stores `scipy.stats.gaussian_kde` datasets containing client
training values. Its fitted object was never serialized or released to the
server. `CopulaGenerator` likewise stays client-private. These runs are
sample-only comparators: each simulated client fits on the exact same Adult
training partition as the BTP age/age+education/label-skew K=5 seed101 pilot,
then emits its exact largest-remainder sample-size share. The evaluator uses
the same alpha-weighted real development validation and assessment splits,
public query workload and 10,000 synthetic rows. Genuity used fixed documented KDE/gaussian-copula settings and no local
hyperparameter search, whereas BTP local models used local-tune grids; tuning
budgets therefore differ. No common-reference score matrix or calibration
summary was used to fit Genuity models. They are not
part of the BTP eight weighting-family model-release comparison and are not DP.

The library copula's raw numeric output is fractional for every sampled row;
its raw result is schema-invalid for integer-valued Adult fields. A separate
`genuity_copula_projected_size` route applies declared public integer rounding
without fitting anything from real records. Pre- and post-projection invalid
rates are saved; all projected samples passed the declared public schema.
The published `generate(seed=...)` route ignores this seed for copula, so the
comparator explicitly sets its documented internal core seed for each repeat;
that implementation detail is recorded in `scripts/genuity_comparator.py`.

## Development results, not a final ranking

| Method / partition | Assessment query max error, 3 synthetic repeats | Notes |
|---|---:|---|
| Genuity KDE size / age | 0.95547 | Gaussian KDE smooths structural zero capital columns; `capital-loss<=0` real 0.9559, synthetic 0.0004 in repeat 0. |
| Genuity projected copula size / age | 0.03545 | Valid after public integer rounding. |
| Genuity projected copula size / age+education | 0.03415 | Valid after public integer rounding. |
| Genuity projected copula size / label skew | 0.02956 | Valid after public integer rounding. |

Evidence: `results/genuity_kde_pilot_20261024/`,
`results/genuity_copula_pilot_20261024/` (raw fractional),
`results/genuity_copula_projected_pilot_20261024/`,
`results/genuity_copula_projected_age_education_20261024/`,
`results/genuity_copula_projected_label_skew_20261024/`, and
`logs/genuity_*.log`. The exact comparator script versions used for the
initial and projected runs are preserved under `scripts/provenance/` and match
the SHA-256 recorded in each configuration. Same-partition BTP copula size-weight results are in
`reports/ec2_pilot_gls_fixed_20261024/` and
`reports/ec2_development_skew_20261024/`. The small differences among
copula variants can reflect finite synthetic sampling; there is one Adult
split seed here and no claim of superiority or novelty.

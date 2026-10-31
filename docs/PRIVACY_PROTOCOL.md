# Differential privacy baseline

**Versioned structural repair (24 October 2026):** The original public-bin
implementation below remains an auditable historical baseline. Its broad
capital-gain/loss bins failed to represent Adult's zero atoms, and independent
sampling violated the public education/education-number relationship. A
separate corrected zero-atom histogram with the same individual-release
adjacency and Laplace sensitivity is specified in
`docs/PUBLIC_ATOM_PRIVACY_PROTOCOL_20261024.md` and evaluated in
`docs/PUBLIC_ATOM_PRIVACY_FINDINGS_20261024.md`. Its full research campaign
is still nonprivate. Do not use the legacy loss as an estimate of DP cost.

`btp.privacy` implements a standalone, runnable epsilon-DP baseline for the
15-column Adult table. It fits independent one-way histograms from a fixed
public schema, then adds Laplace noise to every histogram count. The sampler
draws each column independently. This deliberately simple baseline does not
make the other candidate generators, validation procedures, or the complete
experiment differentially private.

## Public domain and preprocessing

Call `public_schema(n_public, bins)` before accessing the client records. Its
numeric ranges and category vocabularies are hard-coded from the public Adult
schema, including `?` and `__UNKNOWN__`; they are never learned from a private
client. Numeric inputs are clipped to fixed public ranges and assigned to
uniform public bins. Unrecognized categorical values map to `__UNKNOWN__`.
Income accepts only `<=50K` and `>50K`; malformed or missing labels are
rejected rather than emitted. `?` and `__UNKNOWN__` remain feature categories.
The protocol fixes client size `n_public` as public and rejects any frame with
a different row count. This is replace-one record adjacency at a fixed client
size. If the client size is sensitive, this implementation does not protect
that fact and must not be used under a variable-size adjacency claim.

## Histogram mechanism and guarantee

For each of the `d=15` columns, a record contributes one unit to one bin. The
vector formed by concatenating all one-way count histograms has L1 sensitivity
`2d=30` under replacement of one record: each of the 15 columns can decrement
one old bin and increment one new bin. For allocated epsilon `eps`, the code
adds independent Laplace noise with scale `2d/eps` to every count. Clipping
noisy counts to positive values and normalizing each marginal are postprocessing.
The resulting release is epsilon-DP for the client histogram under the stated
adjacency and public-schema assumptions.

For a formal DP release, call `fit_private_histogram(..., seed=None)` and
`release_query_summary(..., seed=None)`. This obtains fresh noise randomness
from operating-system entropy and does not serialize the entropy source or RNG
state. A public or reused deterministic noise seed can reveal the noise and
invalidate the guarantee. Passing an explicit seed is supported for controlled
research reproducibility only; the ledger marks the result
`formal_dp_eligible: false` and labels it deterministic research noise, not a
DP release. Public-seed sampling from an already released histogram is
postprocessing and does not affect its DP guarantee.

Sampling and `log_prob` use the same product of normalized noisy marginals.
Numeric bins sample an integer uniformly from their integer support; their
log probability includes both the bin mass and the within-bin uniform mass.
This is a simple independent baseline, not a private version of the richer
non-private mixed-data generators.

`fit_nonprivate_public_histogram(frame, schema)` is the matched non-private
reference: it uses the exact same declared vocabularies, integer bins,
clipping, product sampler, and likelihood convention, with observed counts plus
a `1e-12` pseudocount and no noise. Its ledger sets `formal_dp_eligible` to
false and uses JSON-safe `null` (`None`) for epsilon fields. The existing
train-quantile-binned generators are not this matched reference.

## Query releases and composition

`release_query_summary` accepts a predeclared transform returning a fixed
`n-by-L` matrix in `[0,1]`. Its vector of means has replace-one L1 sensitivity
`L/n`; Laplace noise therefore uses scale `L/(n*eps)`. The transform must be
fixed independently of the private records. The function checks numeric
bounds and dimensions, but cannot verify how the transform was selected.

The returned `privacy_ledger` records each release and computes conservative
sequential basic composition by summing epsilon allocations. Reuse the same
ledger for every release on the same client records. Keep the total allocation
within the experiment's declared budget; the helper reports the sum but does
not impose an experiment-specific cap. Do not account for repeated access as
free, and do not describe the overall pipeline as DP unless every data access
and release is covered by the ledger and mechanism assumptions.

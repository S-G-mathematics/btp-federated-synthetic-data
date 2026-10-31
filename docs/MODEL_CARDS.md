# Model cards and scoring notes

The `btp.models.fit_model` API provides six generators. The two categorical
histogram models (`independent` and `chow_liu`) define normalized probability
masses over integer numeric values and categorical vocabularies. Their
`exact_discretized` scores account for the number of integers represented by
each numeric bin. Values outside fitted/configured support and labels outside
the vocabulary have zero probability.

`copula` maps empirical marginals to Gaussian latent scores. Numeric ties and
categorical thresholds make `log_prob` an approximation. Categorical labels
are assigned a deterministic sorted order for threshold construction even
though the fields are nominal; the dependence fit can therefore change when
that arbitrary ordering changes. Do not interpret this score as an exact
categorical copula likelihood.

`mixed_gmm` standardizes every numeric feature using train-only means and
scales. By default it applies `log1p` to `fnlwgt`, `capital-gain`, and
`capital-loss` before standardization. Set `numeric_transform="standardized"`
to disable those log transforms, or pass `log1p_columns` to choose the subset.
Sampling reverses the transform, rounds numeric values to integers, then clips
to the configured/default fitted numeric bounds. `log_prob` applies the inverse
change-of-variables Jacobian to the transformed continuous GMM density, then
combines it with component-conditional categorical probabilities. Since draws
are rounded and clipped, this is an `approximate` score rather than the exact
probability mass of emitted integer rows. Default EM settings use two
initializations and covariance regularization `1e-4` in standardized space;
results are deterministic for a fixed seed and data.

`prototype_kde` is a compressed mixed-data kernel mixture. K-means centers and
component counts are fitted from training-only standardized numeric values;
component-conditional categorical probabilities are smoothed. Numeric draws
use diagonal Gaussian kernels around the centers, then inverse transforms,
rounding and public-bound clipping. Its `approximate` score is a continuous
pre-rounding density. The released model contains centers, bandwidths and
aggregated category probabilities, not raw training rows. It is not a standard
observation-level KDE, and centroids can still disclose information. Its first
full-data pilot had substantial marginal error; this is a baseline under
revision, not a strong result.

`latent_class` is an EM-fitted mixture of product distributions over the
same declared integer bins and categorical vocabularies as the histogram
families. Sampling draws a component, a bin/category per column, and a
uniform integer within each numeric bin. Its `exact_discretized` log mass
includes the within-bin integer correction. Multiple initializations and
convergence checks are recorded; the small first grid may limit capacity.

`btp.operators.fit_operator` pools only synthetic pilot samples. Its logpool
normalizes a geometric pool over a finite candidate set; impossible constituent
scores receive a documented finite floor for optimization. The entropic
transport operator is a regularized finite-support Wasserstein analogue, not
an exact unregularized Wasserstein barycenter. Both report exact masses only
on their finite candidate support. Their optional `.posterior()` is a separate
`kernel_smoothed_approximation` over candidate rows and is not the
income-conditional distribution implied by the operator's joint mass.

These methods do not provide privacy guarantees. Validate synthetic utility,
support behavior, and disclosure risk separately before operational use.

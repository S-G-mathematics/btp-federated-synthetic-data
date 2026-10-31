"""A separate, auditable epsilon-DP baseline based on public-schema marginals.

This baseline releases noisy one-way histograms. It is not a claim that the
non-private generators or the complete experimental pipeline are DP.
"""
from __future__ import annotations

from dataclasses import dataclass
import copy

import numpy as np
import pandas as pd


_CATS = {
    "workclass": ["Private", "Self-emp-not-inc", "Self-emp-inc", "Federal-gov", "Local-gov", "State-gov", "Without-pay", "Never-worked", "?", "__UNKNOWN__"],
    "education": ["Bachelors", "Some-college", "11th", "HS-grad", "Prof-school", "Assoc-acdm", "Assoc-voc", "9th", "7th-8th", "12th", "Masters", "1st-4th", "10th", "Doctorate", "5th-6th", "Preschool", "?", "__UNKNOWN__"],
    "marital-status": ["Married-civ-spouse", "Divorced", "Never-married", "Separated", "Widowed", "Married-spouse-absent", "Married-AF-spouse", "?", "__UNKNOWN__"],
    "occupation": ["Tech-support", "Craft-repair", "Other-service", "Sales", "Exec-managerial", "Prof-specialty", "Handlers-cleaners", "Machine-op-inspct", "Adm-clerical", "Farming-fishing", "Transport-moving", "Priv-house-serv", "Protective-serv", "Armed-Forces", "?", "__UNKNOWN__"],
    "relationship": ["Wife", "Own-child", "Husband", "Not-in-family", "Other-relative", "Unmarried", "?", "__UNKNOWN__"],
    "race": ["White", "Asian-Pac-Islander", "Amer-Indian-Eskimo", "Other", "Black", "?", "__UNKNOWN__"],
    "sex": ["Female", "Male", "?", "__UNKNOWN__"],
    "native-country": ["United-States", "Cambodia", "England", "Puerto-Rico", "Canada", "Germany", "Outlying-US(Guam-USVI-etc)", "India", "Japan", "Greece", "South", "China", "Cuba", "Iran", "Honduras", "Philippines", "Italy", "Poland", "Jamaica", "Vietnam", "Mexico", "Portugal", "Ireland", "France", "Dominican-Republic", "Laos", "Ecuador", "Taiwan", "Haiti", "Columbia", "Hungary", "Guatemala", "Nicaragua", "Scotland", "Thailand", "Yugoslavia", "El-Salvador", "Trinadad&Tobago", "Peru", "Hong", "Holand-Netherlands", "?", "__UNKNOWN__"],
    "income": ["<=50K", ">50K"],
}
_NUM_RANGES = {
    "age": (0, 100), "fnlwgt": (0, 2_000_000), "education-num": (0, 16),
    "capital-gain": (0, 100_000), "capital-loss": (0, 5_000), "hours-per-week": (0, 100),
}
PUBLIC_EDUCATION_NUMBER_MAP = {
    "Preschool": 1, "1st-4th": 2, "5th-6th": 3, "7th-8th": 4,
    "9th": 5, "10th": 6, "11th": 7, "12th": 8, "HS-grad": 9,
    "Some-college": 10, "Assoc-voc": 11, "Assoc-acdm": 12,
    "Bachelors": 13, "Masters": 14, "Prof-school": 15, "Doctorate": 16,
}
_COLUMNS = ("age", "workclass", "fnlwgt", "education", "education-num", "marital-status", "occupation", "relationship", "race", "sex", "capital-gain", "capital-loss", "hours-per-week", "native-country", "income")


def public_schema(n_public: int = 1000, bins: int = 10) -> dict:
    """Return fixed public vocabularies, numeric ranges, bin count, and public n.

    Numeric ranges and category lists are hard-coded from the published Adult
    schema. They are not inferred from records. Override only from a declared
    public protocol, never using private sample minima/maxima or vocabularies.
    """
    if int(n_public) <= 0 or int(bins) <= 0:
        raise ValueError("n_public and bins must be positive")
    return {"columns": list(_COLUMNS), "numeric_ranges": dict(_NUM_RANGES),
            "categories": copy.deepcopy(_CATS), "bins": int(bins),
            "n_public": int(n_public),
            "education_number_map": dict(PUBLIC_EDUCATION_NUMBER_MAP)}


def _check_schema(schema):
    required = {"columns", "numeric_ranges", "categories", "bins", "n_public",
                "education_number_map"}
    if not isinstance(schema, dict) or not required <= schema.keys():
        raise ValueError("schema must come from public_schema() or match its complete public structure")
    if (list(schema["columns"]) != list(_COLUMNS)
            or schema["numeric_ranges"] != _NUM_RANGES
            or schema["categories"] != _CATS
            or schema["education_number_map"] != PUBLIC_EDUCATION_NUMBER_MAP):
        raise ValueError("private histogram requires the documented fixed Adult public vocabulary and ranges")
    if int(schema["bins"]) < 1 or int(schema["n_public"]) < 1:
        raise ValueError("schema bins and n_public must be positive")


def _bin_ids(values, lo, hi, bins):
    x = pd.to_numeric(pd.Series(values), errors="coerce").to_numpy(float)
    x = np.nan_to_num(x, nan=lo, posinf=hi, neginf=lo).clip(lo, hi)
    domain = int(hi - lo + 1)
    n_bins = min(int(bins), domain)
    # Partition the inclusive integer domain into nonempty, nearly equal bins.
    ids = np.floor((x - lo) * n_bins / domain).astype(int)
    return np.clip(ids, 0, n_bins - 1)


def _category_ids(values, categories):
    lookup = {v: i for i, v in enumerate(categories)}
    if "__UNKNOWN__" in lookup:
        return np.asarray([lookup.get(str(v).strip(), lookup["__UNKNOWN__"]) for v in values], dtype=int)
    unknown = sorted({str(v).strip() for v in values} - set(lookup))
    if unknown:
        raise ValueError(f"values outside public categorical domain: {unknown[:3]}")
    return np.asarray([lookup[str(v).strip()] for v in values], dtype=int)


def _integer_bin_support(lo, hi, bins, ids):
    domain = int(hi - lo + 1)
    n_bins = min(int(bins), domain)
    starts = lo + np.ceil(np.asarray(ids) * domain / n_bins).astype(int)
    ends = lo + np.ceil((np.asarray(ids) + 1) * domain / n_bins).astype(int) - 1
    return starts, ends


@dataclass
class PrivateHistogram:
    schema: dict
    probabilities: dict
    privacy_ledger: dict

    def sample(self, n: int, seed: int) -> pd.DataFrame:
        if int(n) < 0:
            raise ValueError("n must be nonnegative")
        rng = np.random.default_rng(seed)
        out = {}
        for c in self.schema["columns"]:
            p = self.probabilities[c]
            ids = rng.choice(len(p), size=int(n), p=p)
            if c in self.schema["numeric_ranges"]:
                lo, hi = self.schema["numeric_ranges"][c]
                lows, highs = _integer_bin_support(lo, hi, self.schema["bins"], ids)
                out[c] = np.array([rng.integers(a, z + 1) for a, z in zip(lows, highs)], dtype=int)
            else:
                cats = self.schema["categories"][c]
                out[c] = np.asarray(cats, dtype=object)[ids]
        return pd.DataFrame(out, columns=self.schema["columns"])

    def log_prob(self, frame: pd.DataFrame) -> np.ndarray:
        """Log probability under the same product-of-marginals sampler."""
        out = np.zeros(len(frame), dtype=float)
        for c in self.schema["columns"]:
            p = self.probabilities[c]
            if c in self.schema["numeric_ranges"]:
                lo, hi = self.schema["numeric_ranges"][c]
                values = pd.to_numeric(frame[c], errors="coerce").to_numpy(float)
                valid = np.isfinite(values) & (values >= lo) & (values <= hi) & (values == np.floor(values))
                ids = _bin_ids(values, lo, hi, self.schema["bins"])
                lows, highs = _integer_bin_support(lo, hi, self.schema["bins"], ids)
                widths = highs - lows + 1
                terms = np.log(p[ids]) - np.log(widths)
                out += np.where(valid, terms, -np.inf)
            else:
                cats = self.schema["categories"][c]
                ids = _category_ids(frame[c], cats)
                out += np.log(p[ids])
        return out


def fit_private_histogram(frame: pd.DataFrame, epsilon: float, seed: int | None = None,
                          schema: dict | None = None) -> PrivateHistogram:
    """Fit noisy independent marginals with replace-one epsilon-DP.

    Each record adds one count to each of d=15 disjoint marginal histograms.
    Their concatenated vector has replace-one L1 sensitivity 2d, so Laplace
    noise has scale 2d/epsilon. Positive clipping and normalization are DP
    postprocessing. Public n is fixed by the schema and checked exactly.
    """
    schema = public_schema() if schema is None else copy.deepcopy(schema)
    _check_schema(schema)
    epsilon = float(epsilon)
    if not np.isfinite(epsilon) or epsilon <= 0:
        raise ValueError("epsilon must be finite and positive")
    if len(frame) != int(schema["n_public"]):
        raise ValueError("frame length must equal the protocol's fixed public n_public")
    if list(frame.columns) != schema["columns"]:
        raise ValueError("frame must contain the 15 schema columns in public order")
    # A published/reused deterministic noise seed voids the usual DP guarantee.
    # NumPy's None path obtains fresh entropy from the operating system; never
    # put the resulting state or seed in the returned model or ledger.
    rng = np.random.default_rng(None if seed is None else int(seed))
    d = len(schema["columns"])
    scale = 2 * d / epsilon
    probs = {}
    for c in schema["columns"]:
        if c in schema["numeric_ranges"]:
            lo, hi = schema["numeric_ranges"][c]
            ids = _bin_ids(frame[c], lo, hi, schema["bins"])
            size = min(schema["bins"], int(hi - lo + 1))
        else:
            ids = _category_ids(frame[c], schema["categories"][c])
            size = len(schema["categories"][c])
        counts = np.bincount(ids, minlength=size).astype(float)
        noisy = counts + rng.laplace(0., scale, size=size)
        noisy = np.maximum(noisy, 1e-12)
        probs[c] = noisy / noisy.sum()
    dp_eligible = seed is None
    ledger = {"accounting": "sequential basic composition", "epsilon_spent": epsilon,
              "formal_dp_eligible": dp_eligible,
              "noise_seed_mode": "fresh_os_entropy" if dp_eligible else "deterministic_research_seed",
              "releases": [{"name": "private_histogram_marginals", "epsilon": epsilon,
                            "mechanism": "Laplace", "sensitivity_l1": 2*d,
                            "scale": scale, "n_public": int(schema["n_public"]),
                            "adjacency": "replace-one record at fixed public client size",
                            "noise_seed_mode": "fresh_os_entropy" if dp_eligible else "deterministic_research_seed",
                            "postprocessing": ["clip counts to positive values", "normalize each marginal"]}],
              "scope": ("this histogram release only; no claim for non-private pipeline" if dp_eligible else
                        "deterministic research noise, not a DP release with exposed seed; no formal DP claim")}
    return PrivateHistogram(schema=schema, probabilities=probs, privacy_ledger=ledger)


def fit_nonprivate_public_histogram(frame: pd.DataFrame, schema: dict | None = None) -> PrivateHistogram:
    """Fit exact public-bin marginals as a non-private matched reference.

    Uses precisely the public schema, clipping, bin assignments, and sampler as
    ``fit_private_histogram`` but adds no noise. A tiny pseudocount keeps every
    probability positive for finite likelihood calculations. The returned
    ledger explicitly reports no DP guarantee; epsilon fields are ``None`` so
    the record remains JSON-safe.
    """
    schema = public_schema() if schema is None else copy.deepcopy(schema)
    _check_schema(schema)
    if len(frame) != int(schema["n_public"]):
        raise ValueError("frame length must equal the protocol's fixed public n_public")
    if list(frame.columns) != schema["columns"]:
        raise ValueError("frame must contain the 15 schema columns in public order")
    tiny = 1e-12
    probs = {}
    expected_counts = {}
    for c in schema["columns"]:
        if c in schema["numeric_ranges"]:
            lo, hi = schema["numeric_ranges"][c]
            ids = _bin_ids(frame[c], lo, hi, schema["bins"])
            size = min(schema["bins"], int(hi - lo + 1))
        else:
            ids = _category_ids(frame[c], schema["categories"][c])
            size = len(schema["categories"][c])
        counts = np.bincount(ids, minlength=size).astype(float)
        expected_counts[c] = counts.tolist()
        stabilized = counts + tiny
        probs[c] = stabilized / stabilized.sum()
    ledger = {"accounting": "not applicable; non-private reference",
              "epsilon": None, "epsilon_spent": None,
              "epsilon_interpretation": "infinite / no finite DP guarantee",
              "formal_dp_eligible": False,
              "noise_seed_mode": "no_noise",
              "releases": [{"name": "nonprivate_public_histogram_marginals",
                            "epsilon": None, "mechanism": "none",
                            "n_public": int(schema["n_public"]),
                            "smoothing": "1e-12 pseudocount",
                            "expected_counts": expected_counts}],
              "scope": "non-private matched baseline; no DP guarantee"}
    return PrivateHistogram(schema=schema, probabilities=probs, privacy_ledger=ledger)


def release_query_summary(frame: pd.DataFrame, query_transform, eps: float, seed: int | None = None,
                          privacy_ledger: dict | None = None, n_public: int | None = None):
    """Privately release a fixed-length vector query with entries in [0,1].

    The transform must be public, fixed before access, and return an n-by-L
    matrix with values in [0,1]. Its mean has replace-one L1 sensitivity
    L/n_public. This release composes sequentially with the supplied ledger.
    """
    if not isinstance(privacy_ledger, dict) or "epsilon_spent" not in privacy_ledger or "releases" not in privacy_ledger:
        raise ValueError("privacy_ledger from an earlier release is required for sequential composition")
    eps = float(eps)
    n = int(n_public if n_public is not None else len(frame))
    if eps <= 0 or not np.isfinite(eps) or n <= 0 or len(frame) != n:
        raise ValueError("eps and fixed n_public must be positive; frame length must equal n_public")
    values = np.asarray(query_transform(frame), dtype=float)
    if values.ndim != 2 or values.shape[0] != n or values.shape[1] < 1 or not np.all(np.isfinite(values)) or np.any(values < 0) or np.any(values > 1):
        raise ValueError("query_transform must return a fixed n-by-L matrix bounded in [0,1]")
    L = values.shape[1]
    scale = L / (n * eps)
    released = values.mean(axis=0) + np.random.default_rng(None if seed is None else int(seed)).laplace(0., scale, size=L)
    dp_eligible = seed is None and bool(privacy_ledger.get("formal_dp_eligible", False))
    if not dp_eligible:
        privacy_ledger["formal_dp_eligible"] = False
        privacy_ledger["scope"] = "deterministic research noise or prior non-DP release; no formal DP claim"
    privacy_ledger.setdefault("noise_seed_mode", "fresh_os_entropy" if seed is None else "deterministic_research_seed")
    privacy_ledger["epsilon_spent"] = float(privacy_ledger["epsilon_spent"]) + eps
    privacy_ledger["releases"].append({"name": "bounded_query_summary", "epsilon": eps,
        "mechanism": "Laplace", "sensitivity_l1": L/n, "scale": scale,
        "n_public": n, "adjacency": "replace-one record at fixed public client size",
        "noise_seed_mode": "fresh_os_entropy" if seed is None else "deterministic_research_seed"})
    modes = {r.get("noise_seed_mode") for r in privacy_ledger["releases"]}
    privacy_ledger["noise_seed_mode"] = next(iter(modes)) if len(modes) == 1 else "mixed"
    return released, privacy_ledger

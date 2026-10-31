"""Versioned standalone public-bin histogram with heavy-tail zero atoms.

Only an individual noisy histogram release has the stated conditional DP scope.
The surrounding research campaign and data-dependent assignment are nonprivate.
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd

from btp.privacy import (_bin_ids, _category_ids, _integer_bin_support,
                         public_schema)

ZERO_ATOMS = ("capital-gain", "capital-loss")


def declared_schema(n_public: int, bins: int = 8) -> dict:
    if bins < 2:
        raise ValueError("zero-atom schema requires at least two numeric bins")
    schema = public_schema(n_public=n_public, bins=bins)
    schema["zero_atom_columns"] = list(ZERO_ATOMS)
    schema["education_projection"] = "public_map_after_sampling"
    return schema


def numeric_ids(values, column: str, schema: dict) -> tuple[np.ndarray, int]:
    lo, hi = schema["numeric_ranges"][column]
    if column in ZERO_ATOMS:
        x = pd.to_numeric(pd.Series(values), errors="coerce").to_numpy(float)
        x = np.nan_to_num(x, nan=lo, posinf=hi, neginf=lo).clip(lo, hi)
        ids = np.zeros(len(x), dtype=int)
        positive = x > 0
        ids[positive] = 1 + _bin_ids(x[positive], 1, hi, schema["bins"]-1)
        return ids, 1 + min(schema["bins"]-1, hi)
    return _bin_ids(values, lo, hi, schema["bins"]), min(schema["bins"], hi-lo+1)


def numeric_support(column: str, schema: dict, ids: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    lo, hi = schema["numeric_ranges"][column]
    if column in ZERO_ATOMS:
        positive_ids = np.maximum(np.asarray(ids, int)-1, 0)
        lows, highs = _integer_bin_support(1, hi, schema["bins"]-1, positive_ids)
        return np.where(np.asarray(ids)==0, 0, lows), np.where(np.asarray(ids)==0, 0, highs)
    return _integer_bin_support(lo, hi, schema["bins"], ids)


@dataclass
class PublicAtomHistogram:
    schema: dict
    probabilities: dict
    privacy_ledger: dict

    @property
    def columns(self):
        return self.schema["columns"]

    @property
    def likelihood_kind(self):
        return "exact_public_integer_product_with_projected_education"

    def sample(self, n: int, seed: int) -> pd.DataFrame:
        if n < 0:
            raise ValueError("n must be nonnegative")
        rng = np.random.default_rng(seed)
        out = {}
        for column in self.columns:
            p = self.probabilities[column]
            ids = rng.choice(len(p), size=int(n), p=p)
            if column in self.schema["numeric_ranges"]:
                lows, highs = numeric_support(column, self.schema, ids)
                out[column] = rng.integers(lows, highs+1)
            else:
                out[column] = np.asarray(self.schema["categories"][column], object)[ids]
        frame = pd.DataFrame(out, columns=self.columns)
        mapped = frame.education.map(self.schema["education_number_map"])
        known = mapped.notna()
        frame.loc[known, "education-num"] = mapped.loc[known].astype(int)
        return frame

    def log_prob(self, frame: pd.DataFrame) -> np.ndarray:
        if not set(self.columns).issubset(frame.columns):
            raise ValueError("frame lacks public Adult schema")
        out = np.zeros(len(frame), float)
        mapped = frame.education.map(self.schema["education_number_map"])
        known = mapped.notna().to_numpy()
        education_num = pd.to_numeric(frame["education-num"], errors="coerce").to_numpy(float)
        mapped_values = mapped.to_numpy(float)
        out[known & (education_num != mapped_values)] = -np.inf
        for column in self.columns:
            p = self.probabilities[column]
            if column in self.schema["numeric_ranges"]:
                lo, hi = self.schema["numeric_ranges"][column]
                values = pd.to_numeric(frame[column], errors="coerce").to_numpy(float)
                valid = np.isfinite(values) & (values >= lo) & (values <= hi) & (values == np.floor(values))
                ids, _ = numeric_ids(values, column, self.schema)
                lows, highs = numeric_support(column, self.schema, ids)
                contribution = np.log(p[ids]) - np.log(highs-lows+1)
                if column == "education-num":
                    contribution = np.where(known, 0., contribution)
                    valid = np.where(known, True, valid)
                out += np.where(valid, contribution, -np.inf)
            else:
                ids = _category_ids(frame[column], self.schema["categories"][column])
                out += np.log(p[ids])
        return out


def fit_histogram(frame: pd.DataFrame, schema: dict, epsilon: float | None) -> PublicAtomHistogram:
    expected = declared_schema(n_public=int(schema["n_public"]), bins=int(schema["bins"]))
    if (schema != expected or len(frame) != schema["n_public"]
        or list(frame.columns) != schema["columns"]):
        raise ValueError("frame/schema violate fixed public zero-atom protocol")
    if epsilon is not None and (not np.isfinite(epsilon) or epsilon <= 0):
        raise ValueError("epsilon must be positive and finite")
    d = len(schema["columns"])
    scale = (2*d/float(epsilon)) if epsilon is not None else None
    rng = np.random.default_rng(None) if epsilon is not None else None
    probabilities = {}
    for column in schema["columns"]:
        if column in schema["numeric_ranges"]:
            ids, size = numeric_ids(frame[column], column, schema)
        else:
            ids = _category_ids(frame[column], schema["categories"][column])
            size = len(schema["categories"][column])
        counts = np.bincount(ids, minlength=size).astype(float)
        perturbed = counts + (rng.laplace(0., scale, size=size) if rng is not None else 1e-12)
        perturbed = np.maximum(perturbed, 1e-12)
        probabilities[column] = perturbed / perturbed.sum()
    ledger = {
        "formal_dp_eligible": epsilon is not None,
        "epsilon_single_release": epsilon,
        "noise_seed_mode": "fresh_os_entropy" if epsilon is not None else "no_noise",
        "adjacency": "replace-one record with fixed public membership and client size",
        "sensitivity_l1": 2*d if epsilon is not None else None,
        "laplace_scale": scale,
        "postprocessing": ["positive clipping", "normalization", "public education-code projection"],
        "scope": "this individual 15-column histogram release only; main pipeline is nonprivate",
    }
    return PublicAtomHistogram(schema, probabilities, ledger)

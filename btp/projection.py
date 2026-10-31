"""Declared public structural projection of an Adult joint generator.

This wrapper is an implementation component, not a claim that earlier campaign
cells emitted or scored projected rows. The projected model must be tuned and
evaluated in a new versioned campaign before use for method selection.
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd
from scipy.special import logsumexp


@dataclass
class EducationNumberProjection:
    raw_model: object
    mapping: dict[str, int]
    integer_support: tuple[int, int]

    def __post_init__(self) -> None:
        if "education" not in self.raw_model.columns or "education-num" not in self.raw_model.columns:
            raise ValueError("projection requires both Adult education columns")
        lo, hi = self.integer_support
        if not (isinstance(lo, int) and isinstance(hi, int) and 0 <= lo <= hi):
            raise ValueError("integer support must be a nonnegative inclusive interval")
        if not self.mapping or any(not isinstance(v, int) or not lo <= v <= hi for v in self.mapping.values()):
            raise ValueError("mapped codes must be integers inside declared support")
        self.mapping = dict(self.mapping)
        self.columns = list(self.raw_model.columns)
        self.likelihood_kind = self.raw_model.likelihood_kind

    def sample(self, n: int, seed: int) -> pd.DataFrame:
        frame = self.raw_model.sample(n, seed).copy()
        code = frame["education"].map(self.mapping)
        known = code.notna()
        frame.loc[known, "education-num"] = code.loc[known].astype(int)
        return frame

    def log_prob(self, frame: pd.DataFrame) -> np.ndarray:
        """Pushforward score; exact only if raw_model has exact integer mass.

        For mapped education, marginalize the preprojection education-number
        value across the complete declared integer support. Unmapped categories
        retain the raw identity score. Incompatible mapped rows have zero mass.
        """
        if not set(self.columns).issubset(frame.columns):
            raise ValueError("frame lacks required model columns")
        code = frame["education"].map(self.mapping)
        known = code.notna().to_numpy()
        actual = pd.to_numeric(frame["education-num"], errors="coerce").to_numpy(float)
        expected = code.to_numpy(float)
        out = np.full(len(frame), -np.inf, dtype=float)
        if (~known).any():
            out[~known] = self.raw_model.log_prob(frame.iloc[np.flatnonzero(~known)])
        valid = known & np.isfinite(actual) & (actual == expected)
        if valid.any():
            base = frame.iloc[np.flatnonzero(valid)].copy()
            terms = []
            lo, hi = self.integer_support
            for value in range(lo, hi + 1):
                trial = base.copy()
                trial["education-num"] = value
                terms.append(self.raw_model.log_prob(trial))
            out[valid] = logsumexp(np.vstack(terms), axis=0)
        return out

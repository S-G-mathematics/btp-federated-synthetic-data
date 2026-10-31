"""Loading, splitting, and non-IID partitioning for UCI Adult.

All preprocessing decisions here are label/category preserving.  Fit-dependent
partition rules are learned from the training split only and can then be applied
unchanged to tune, calibration, validation, and test data.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import hashlib

import numpy as np
import pandas as pd


PREDICTORS = (
    "age", "workclass", "fnlwgt", "education", "education-num",
    "marital-status", "occupation", "relationship", "race", "sex",
    "capital-gain", "capital-loss", "hours-per-week", "native-country",
)
LABEL = "income"
ALL_COLUMNS = PREDICTORS + (LABEL,)
NUMERIC = ("age", "fnlwgt", "education-num", "capital-gain", "capital-loss", "hours-per-week")
CATEGORICAL = tuple(c for c in PREDICTORS if c not in NUMERIC)
SPLIT_FRACTIONS = {"train": .65, "tune": .15, "calibration": .10, "validation": .10}


def _read_file(path: Path, *, test: bool) -> pd.DataFrame:
    if not path.exists():
        raise FileNotFoundError(f"Required UCI Adult file not found: {path}")
    # adult.test has one explanatory/header line; both files have no CSV header.
    df = pd.read_csv(path, header=None, names=ALL_COLUMNS, skiprows=1 if test else 0,
                     skipinitialspace=True, na_filter=False, comment=None)
    for col in ALL_COLUMNS:
        df[col] = df[col].astype(str).str.strip()
    if test:
        df[LABEL] = df[LABEL].str.removesuffix(".")
    # '?' is intentionally an explicit category; preserve every source row.
    for col in CATEGORICAL:
        df[col] = df[col].replace("", "?").fillna("?")
    for col in NUMERIC:
        df[col] = pd.to_numeric(df[col], errors="raise")
    allowed = {"<=50K", ">50K"}
    bad = sorted(set(df[LABEL]) - allowed)
    if bad:
        raise ValueError(f"Unexpected income labels in {path}: {bad}")
    return df.loc[:, ALL_COLUMNS]


def read_adult(raw_dir: str | Path) -> pd.DataFrame:
    """Read official adult.data and adult.test, retaining all 48,842 rows.

    Index values are stable source IDs (``train:000000`` / ``test:000000``),
    and the index is metadata rather than a predictor column.
    """
    root = Path(raw_dir)
    train = _read_file(root / "adult.data", test=False)
    test = _read_file(root / "adult.test", test=True)
    train.index = pd.Index([f"train:{i:06d}" for i in range(len(train))], name="row_id")
    test.index = pd.Index([f"test:{i:06d}" for i in range(len(test))], name="row_id")
    return pd.concat([train, test], axis=0)


def _record_key(row: tuple) -> tuple:
    return tuple(row)


def _stratified_group_split(frame: pd.DataFrame, fractions: dict[str, float], seed: int) -> dict[str, pd.DataFrame]:
    names = list(fractions)
    proportions = np.asarray([fractions[n] for n in names], dtype=float)
    if np.any(proportions <= 0) or not np.isclose(proportions.sum(), 1):
        raise ValueError("Split fractions must be positive and sum to 1")
    groups: dict[tuple, list[str]] = {}
    vals = frame.loc[:, ALL_COLUMNS].itertuples(index=False, name=None)
    for idx, row in zip(frame.index.astype(str), vals):
        groups.setdefault(_record_key(row), []).append(idx)
    by_label: dict[str, list[list[str]]] = {"<=50K": [], ">50K": []}
    for key, ids in groups.items():
        by_label[key[-1]].append(ids)
    assigned: dict[str, list[str]] = {n: [] for n in names}
    rng = np.random.default_rng(seed)
    # Greedy largest-group allocation keeps duplicate records intact while
    # tracking target row counts separately for each class.
    for label, label_groups in by_label.items():
        label_groups.sort(key=lambda ids: (-len(ids), ids[0]))
        # Randomize equal-size ties reproducibly without depending on hash order.
        tie = rng.random(len(label_groups))
        label_groups = [g for _, g in sorted(zip(tie, label_groups), key=lambda x: (-len(x[1]), x[0]))]
        total = sum(map(len, label_groups))
        target = proportions * total
        counts = np.zeros(len(names), dtype=float)
        for ids in label_groups:
            # Choose split with the greatest remaining proportional deficit.
            deficits = target - counts
            j = int(np.argmax(deficits))
            assigned[names[j]].extend(ids)
            counts[j] += len(ids)
    return {n: frame.loc[sorted(assigned[n])].copy() for n in names}


def prepare_splits(raw_dir: str | Path, seed: int = 42,
                   fractions: dict[str, float] | None = None) -> dict[str, pd.DataFrame]:
    """Prepare reproducible train/tune/calibration/validation/locked-test sets.

    The official UCI test set remains locked test data. Exact duplicate records
    found in official train are quarantined from development data to prevent
    cross-boundary leakage. Remaining official train records are grouped by all
    15 values before a class-stratified split; duplicate rows remain together.
    """
    df = read_adult(raw_dir)
    fr = dict(fractions or SPLIT_FRACTIONS)
    expected = {"train", "tune", "calibration", "validation"}
    if set(fr) != expected:
        raise ValueError(f"Development fractions must have keys {sorted(expected)}")
    if not np.isclose(sum(fr.values()), 1):
        raise ValueError("Development split fractions must sum to 1")
    official_train = df.loc[df.index.str.startswith("train:")]
    official_test = df.loc[df.index.str.startswith("test:")]
    test_keys = {_record_key(row) for row in official_test.loc[:, ALL_COLUMNS].itertuples(index=False, name=None)}
    train_keys = [_record_key(row) for row in official_train.loc[:, ALL_COLUMNS].itertuples(index=False, name=None)]
    keep_mask = np.fromiter((key not in test_keys for key in train_keys), dtype=bool, count=len(train_keys))
    dev = official_train.loc[keep_mask]
    quarantine = official_train.loc[~keep_mask].copy()
    out = _stratified_group_split(dev, fr, seed)
    out["test"] = official_test.copy()
    out["quarantine"] = quarantine
    # Public provenance useful to downstream reports and audit checks.
    manifest = {"seed": int(seed), "counts": {name: int(len(part)) for name, part in out.items()},
                "quarantined_train_rows": int((~keep_mask).sum()),
                "official_test_rows": int(len(official_test)),
                "policy": "official test locked; exact full-record duplicates in official train quarantined; remaining official train duplicate groups stratified by income"}
    for part in out.values():
        part.attrs["manifest"] = manifest
    return out


def _stable_uniform(row_id: object, seed: int) -> float:
    raw = f"{seed}|{row_id}".encode("utf-8")
    n = int.from_bytes(hashlib.blake2b(raw, digest_size=8).digest(), "big")
    return n / 2**64


@dataclass(frozen=True)
class PartitionRule:
    kind: str
    k: int
    seed: int
    severity: float
    age_edges: tuple[float, ...] = ()
    education_edges: tuple[float, ...] = ()
    label_probs: tuple[tuple[float, ...], ...] = ()

    def assign(self, frame: pd.DataFrame, seed: int | None = None) -> np.ndarray:
        """Return one client id per row, deterministic by row ID and seed."""
        seed = self.seed if seed is None else int(seed)
        if self.kind == "label_skew":
            labels = np.asarray(self.label_probs)
            result = []
            for row_id, label in zip(frame.index.astype(str), frame[LABEL].astype(str)):
                li = 0 if label == "<=50K" else 1
                u = _stable_uniform(row_id, seed)
                result.append(int(np.searchsorted(np.cumsum(labels[li]), u, side="right").clip(0, self.k - 1)))
            return np.asarray(result, dtype=int)
        ages = pd.to_numeric(frame["age"], errors="coerce").to_numpy(dtype=float)
        age_bin = np.searchsorted(np.asarray(self.age_edges), ages, side="right")
        if self.kind == "age":
            score = age_bin.astype(float)
            n_bins = len(self.age_edges) + 1
            centers = np.linspace(0, n_bins - 1, self.k)
            # Map quantile-age strata to clients with controlled soft mixing.
            logits = -np.square(score[:, None] / max(n_bins - 1, 1) - centers[None, :] / max(self.k - 1, 1))
        elif self.kind == "age_education":
            edu = pd.to_numeric(frame["education-num"], errors="coerce").to_numpy(dtype=float)
            edu_bin = np.searchsorted(np.asarray(self.education_edges), edu, side="right")
            a = age_bin / max(len(self.age_edges), 1)
            e = edu_bin / max(len(self.education_edges), 1)
            score = np.clip(.65 * a + .35 * e, 0, 1)
            centers = np.linspace(0, 1, self.k)
            logits = -np.square(score[:, None] - centers[None, :])
        else:
            raise ValueError(f"Unsupported partition kind: {self.kind}")
        temperature = max(.02, (1.01 - self.severity) * .8 + .02)
        logits = logits / temperature
        logits -= logits.max(axis=1, keepdims=True)
        probs = np.exp(logits)
        probs /= probs.sum(axis=1, keepdims=True)
        result = []
        for row_id, p in zip(frame.index.astype(str), probs):
            u = _stable_uniform(row_id, seed)
            result.append(int(np.searchsorted(np.cumsum(p), u, side="right").clip(0, self.k - 1)))
        return np.asarray(result, dtype=int)


def build_partition_rule(train: pd.DataFrame, k: int, kind: str = "age", seed: int = 42,
                         severity: float = .8) -> PartitionRule:
    """Fit a reusable non-IID assignment rule using training data only.

    ``kind`` is ``age``, ``age_education`` or ``label_skew``. Severity is in
    [0, 1], where larger values make feature partitions sharper; label-skew
    concentration is inversely related to severity.
    """
    if k < 2:
        raise ValueError("k must be at least 2")
    if not 0 <= severity <= 1:
        raise ValueError("severity must be between 0 and 1")
    aliases = {"two_feature": "age_education", "education_age": "age_education", "label": "label_skew"}
    kind = aliases.get(kind, kind)
    if kind not in {"age", "age_education", "label_skew"}:
        raise ValueError("kind must be age, age_education, or label_skew")
    if kind == "label_skew":
        rng = np.random.default_rng(seed)
        alpha = max(.05, (1 - severity) * 2 + .05)
        # Predeclared 5% common assignment mass prevents degenerate empty
        # clients without inspecting/repairing any validation or test split.
        probs = tuple(tuple(.95*rng.dirichlet(np.full(k, alpha))+.05/k) for _ in range(2))
        return PartitionRule(kind, k, seed, severity, label_probs=probs)
    age = pd.to_numeric(train["age"], errors="coerce").dropna().to_numpy()
    if not len(age):
        raise ValueError("Training data must contain numeric age values")
    age_edges = tuple(float(x) for x in np.unique(np.quantile(age, [0.2, .4, .6, .8])))
    edu_edges: tuple[float, ...] = ()
    if kind == "age_education":
        edu = pd.to_numeric(train["education-num"], errors="coerce").dropna().to_numpy()
        if not len(edu):
            raise ValueError("Training data must contain numeric education-num values")
        edu_edges = tuple(float(x) for x in np.unique(np.quantile(edu, [.2, .4, .6, .8])))
    return PartitionRule(kind, k, seed, severity, age_edges, edu_edges)


def partition_frame(frame: pd.DataFrame, k: int, kind: str = "age", seed: int = 42,
                    severity: float = .8) -> pd.Series:
    """Convenience partitioner for one frame (for experiments only).

    For evaluation splits, prefer ``build_partition_rule(train, ...).assign``
    so the same training-fitted rule is applied to every split.
    """
    rule = build_partition_rule(frame, k, kind, seed, severity)
    return pd.Series(rule.assign(frame), index=frame.index, name="client_id")

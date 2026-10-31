"""Official UCI Bank Marketing additional-full ingestion and fixed split rules."""
from __future__ import annotations

import argparse
import hashlib
import io
import json
import urllib.request
import zipfile
from dataclasses import dataclass
from decimal import Decimal
from pathlib import Path

import numpy as np
import pandas as pd

SOURCE_URL = "https://archive.ics.uci.edu/static/public/222/bank+marketing.zip"
MEMBER = "bank-additional/bank-additional-full.csv"
LABEL = "y"
RAW_COLUMNS = ("age", "job", "marital", "education", "default", "housing", "loan",
               "contact", "month", "day_of_week", "duration", "campaign", "pdays",
               "previous", "poutcome", "emp.var.rate", "cons.price.idx", "cons.conf.idx",
               "euribor3m", "nr.employed", "y")
MODEL_COLUMNS = tuple(c for c in RAW_COLUMNS if c != "duration")
SCALES = {"age": 1, "campaign": 1, "previous": 1, "emp.var.rate": 1000,
          "cons.price.idx": 1000, "cons.conf.idx": 1000,
          "euribor3m": 1000, "nr.employed": 1000}
FRACTIONS = {"train": .55, "tune": .15, "calibration": .10,
             "validation": .10, "assessment": .10}
SPLIT_SEED = 7171


def sha_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def fetch_archive(path: Path) -> dict:
    """Download only the named official UCI archive; preserve source bytes."""
    path.parent.mkdir(parents=True, exist_ok=True)
    if not path.exists():
        with urllib.request.urlopen(SOURCE_URL, timeout=120) as response:
            content = response.read()
        temp = path.with_suffix(path.suffix + ".tmp")
        temp.write_bytes(content)
        temp.replace(path)
    outer_bytes = path.read_bytes()
    with zipfile.ZipFile(io.BytesIO(outer_bytes)) as outer:
        matches = [n for n in outer.namelist() if n.endswith("bank-additional.zip")]
        if len(matches) != 1:
            raise ValueError(f"Expected one bank-additional.zip in official source, found {matches}")
        outer_member = matches[0]
        inner_bytes = outer.read(outer_member)
    with zipfile.ZipFile(io.BytesIO(inner_bytes)) as inner:
        matches = [n for n in inner.namelist() if n.endswith(MEMBER)]
        if len(matches) != 1:
            raise ValueError(f"Expected exactly {MEMBER}, found {matches}")
        csv_member = matches[0]
        member_bytes = inner.read(csv_member)
    return {"source_url": SOURCE_URL, "archive_path": str(path),
            "archive_sha256": sha_bytes(outer_bytes), "nested_member": outer_member,
            "inner_archive_sha256": sha_bytes(inner_bytes),
            "csv_member": csv_member, "csv_member_sha256": sha_bytes(member_bytes),
            "csv_bytes": member_bytes,
            "license": "CC BY 4.0; cite UCI Bank Marketing and Moro et al. (2014)"}


def read_bank(member_bytes: bytes) -> pd.DataFrame:
    raw = pd.read_csv(io.BytesIO(member_bytes), sep=";", dtype=str, na_filter=False)
    if tuple(raw.columns) != RAW_COLUMNS or len(raw) != 41188:
        raise ValueError(f"Wrong Bank version/schema: {len(raw)} rows, columns {list(raw.columns)}")
    if set(raw[LABEL]) != {"yes", "no"}:
        raise ValueError("Invalid Bank outcome labels")
    raw.index = pd.Index([f"bank:{i:06d}" for i in range(len(raw))], name="row_id")
    frame = raw.drop(columns="duration").copy()
    for c, scale in SCALES.items():
        values = []
        for value in frame[c]:
            exact = Decimal(value) * scale
            if exact != exact.to_integral_value():
                raise ValueError(f"Unregistered precision beyond 0.001 in {c}: {value}")
            values.append(int(exact))
        frame[c] = np.asarray(values, dtype=np.int64)
    for c in frame.columns.difference(SCALES):
        frame[c] = frame[c].astype(str).str.strip()
    if frame.isna().any().any() or tuple(frame.columns) != MODEL_COLUMNS:
        raise ValueError("Invalid cleaned Bank table")
    if "999" not in set(frame.pdays):
        raise ValueError("Declared no-prior-contact pdays atom missing")
    return frame


def _group_split(frame: pd.DataFrame) -> dict[str, pd.DataFrame]:
    names = list(FRACTIONS)
    proportions = np.asarray(list(FRACTIONS.values()))
    groups: dict[tuple, list[str]] = {}
    for row_id, row in zip(frame.index.astype(str), frame.itertuples(index=False, name=None)):
        groups.setdefault(tuple(row), []).append(row_id)
    by_label = {"no": [], "yes": []}
    for key, ids in groups.items():
        by_label[key[-1]].append(ids)
    rng = np.random.default_rng(SPLIT_SEED)
    assignment = {name: [] for name in names}
    for label in ("no", "yes"):
        candidates = by_label[label]
        tie = rng.random(len(candidates))
        candidates = [group for _, group in sorted(zip(tie, candidates),
                     key=lambda pair: (-len(pair[1]), pair[0]))]
        target = proportions * sum(map(len, candidates))
        achieved = np.zeros(len(names))
        for group in candidates:
            j = int(np.argmax(target - achieved))
            assignment[names[j]].extend(group)
            achieved[j] += len(group)
    parts = {name: frame.loc[sorted(assignment[name])].copy() for name in names}
    if sum(map(len, parts.values())) != len(frame):
        raise ValueError("Bank split lost records")
    hashes = {}
    for name, part in parts.items():
        for row in part.itertuples(index=False, name=None):
            digest = sha_bytes(repr(tuple(row)).encode())
            if digest in hashes and hashes[digest] != name:
                raise ValueError("Full-record duplicate group crossed splits")
            hashes[digest] = name
    return parts


def prepare_bank(path: Path, out: Path) -> tuple[dict[str, pd.DataFrame], dict]:
    provenance = fetch_archive(path)
    frame = read_bank(provenance.pop("csv_bytes"))
    parts = _group_split(frame)
    out.mkdir(parents=True, exist_ok=True)
    manifest = pd.concat([pd.DataFrame({"row_id": part.index, "split": name})
                          for name, part in parts.items()], ignore_index=True)
    manifest = manifest.sort_values("row_id")
    manifest.to_csv(out / "split_manifest.csv", index=False)
    cleaned = frame.to_csv(index=True).encode()
    (out / "cleaned.csv").write_bytes(cleaned)
    observed_bounds = {c: [int(parts["train"][c].min()), int(parts["train"][c].max())]
                       for c in SCALES}
    support_bounds = {}
    for c, (lo, hi) in observed_bounds.items():
        slack = max(1, int(np.ceil(.1 * max(hi - lo, 1))))
        lower = lo - slack
        if c in ("age", "campaign", "previous"):
            lower = max(0, lower)
        support_bounds[c] = [lower, hi + slack]
    schema = {"source": "official UCI bank-additional-full.csv", "outcome": LABEL,
              "predictors": [c for c in MODEL_COLUMNS if c != LABEL],
              "duration_dropped_before_all_fitting": True,
              "numeric_scale": SCALES, "pdays_type": "explicit categorical; 999=no previous contact",
              "numeric_observed_extrema_training_only": observed_bounds,
              "numeric_bounds_training_only": support_bounds,
              "numeric_bound_rule": "train minimum/maximum extended by ceil(10% of observed range), at least one unit; age/campaign/previous lower bound at zero",
              "category_vocab_training_only": {c: sorted(parts["train"][c].unique().tolist())
                                                for c in MODEL_COLUMNS if c not in SCALES},
              "split_seed": SPLIT_SEED, "split_fractions": FRACTIONS}
    (out / "schema.json").write_text(json.dumps(schema, indent=2) + "\n")
    details = {**provenance, "rows": len(frame), "source_row_id_first": frame.index[0],
               "source_row_id_last": frame.index[-1], "cleaned_csv_sha256": sha_bytes(cleaned),
               "split_manifest_sha256": sha_bytes((out / "split_manifest.csv").read_bytes()),
               "schema_sha256": sha_bytes((out / "schema.json").read_bytes()),
               "split_counts": {name: len(part) for name, part in parts.items()},
               "record_duplicate_groups": int(len(frame) - frame.drop_duplicates().shape[0]),
               "person_identity_available": False,
               "chronology_note": "Source is date ordered; registered primary split is random by full record, not person or time."}
    (out / "data_manifest.json").write_text(json.dumps(details, indent=2) + "\n")
    return parts, schema


def stable_uniform(row_id: object, seed: int) -> float:
    digest = hashlib.blake2b(f"{seed}|{row_id}".encode(), digest_size=8).digest()
    return int.from_bytes(digest, "big") / 2**64


EDUCATION_LEVEL = {"illiterate": 0, "basic.4y": 1, "basic.6y": 2,
                   "basic.9y": 3, "high.school": 4, "professional.course": 5,
                   "university.degree": 6, "unknown": -1}


@dataclass(frozen=True)
class BankPartitionRule:
    kind: str
    k: int
    seed: int
    severity: float
    age_edges: tuple[float, ...] = ()
    education_edges: tuple[float, ...] = ()
    label_probs: tuple[tuple[float, ...], ...] = ()

    def assign(self, frame: pd.DataFrame) -> np.ndarray:
        if self.kind == "label_skew":
            probs = np.asarray(self.label_probs)
            return np.asarray([min(self.k - 1, int(np.searchsorted(np.cumsum(probs[int(y == "yes")]),
                                 stable_uniform(rid, self.seed), side="right")))
                               for rid, y in zip(frame.index, frame.y)], dtype=int)
        age_bin = np.searchsorted(self.age_edges, frame.age.to_numpy(), side="right")
        edu = frame.education.map(EDUCATION_LEVEL).fillna(-1).to_numpy()
        edu_bin = np.searchsorted(self.education_edges, edu, side="right")
        score = np.clip(.65 * age_bin / max(len(self.age_edges), 1)
                        + .35 * edu_bin / max(len(self.education_edges), 1), 0, 1)
        centers = np.linspace(0, 1, self.k)
        temperature = max(.02, (1.01 - self.severity) * .8 + .02)
        logits = -(score[:, None] - centers[None, :]) ** 2 / temperature
        logits -= logits.max(axis=1, keepdims=True)
        probs = np.exp(logits)
        probs /= probs.sum(axis=1, keepdims=True)
        return np.asarray([min(self.k - 1, int(np.searchsorted(np.cumsum(p),
                           stable_uniform(rid, self.seed), side="right")))
                           for rid, p in zip(frame.index, probs)], dtype=int)


def fit_partition_rule(train: pd.DataFrame, kind: str, k: int, seed: int,
                       severity: float = .8) -> BankPartitionRule:
    if kind not in ("age_education", "label_skew") or k != 5:
        raise ValueError("Outside registered external partition protocol")
    if kind == "label_skew":
        rng = np.random.default_rng(seed)
        concentration = max(.05, (1 - severity) * 2 + .05)
        probs = tuple(tuple(.95 * rng.dirichlet(np.full(k, concentration)) + .05 / k)
                      for _ in range(2))
        return BankPartitionRule(kind, k, seed, severity, label_probs=probs)
    age_edges = tuple(float(x) for x in np.unique(np.quantile(train.age, [.2, .4, .6, .8])))
    edu = train.education.map(EDUCATION_LEVEL).fillna(-1)
    edu_edges = tuple(float(x) for x in np.unique(np.quantile(edu, [.2, .4, .6, .8])))
    return BankPartitionRule(kind, k, seed, severity, age_edges, edu_edges)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--archive", type=Path, required=True)
    ap.add_argument("--out", type=Path, required=True)
    args = ap.parse_args()
    parts, _ = prepare_bank(args.archive, args.out)
    print(json.dumps({"split_counts": {k: len(v) for k, v in parts.items()},
                      "manifest": str(args.out / "data_manifest.json")}, sort_keys=True))


if __name__ == "__main__":
    main()

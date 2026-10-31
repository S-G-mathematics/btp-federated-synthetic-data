from pathlib import Path
import sys

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from btp.data import (ALL_COLUMNS, CATEGORICAL, NUMERIC, build_partition_rule,
                      prepare_splits, read_adult)


def _write_fixture(root: Path):
    # Each record follows the official 14-predictor + income layout.
    base = ["39", " State-gov", "77516", " Bachelors", "13", " Never-married",
            " Adm-clerical", " Not-in-family", " White", " Male", "2174", "0",
            "40", " United-States", " <=50K"]
    rows = []
    for i in range(30):
        r = base.copy()
        r[0] = str(20 + i)
        r[2] = str(1000 + i)
        r[4] = str(1 + i % 15)
        r[10] = str(i * 10)
        r[12] = str(20 + i % 50)
        r[14] = " >50K" if i % 2 else " <=50K"
        if i == 2:
            r[1] = " ?"
        rows.append(r)
    # Deliberate train duplicate of first official test row; quarantine it.
    train = rows + [rows[0]]
    test = [rows[0].copy()]
    for i, source in enumerate(rows[10:18]):
        r = source.copy()
        r[2] = str(50000 + i)  # keep test rows distinct from official train
        test.append(r)
    root.joinpath("adult.data").write_text("\n".join(", ".join(r) for r in train) + "\n")
    test = [r[:-1] + [r[-1] + "."] for r in test]
    root.joinpath("adult.test").write_text("|1x3 Cross validator\n" + "\n".join(", ".join(r) for r in test) + "\n")


def test_read_schema_and_preserves_missing_category(tmp_path):
    _write_fixture(tmp_path)
    df = read_adult(tmp_path)
    assert df.shape == (40, 15)
    assert tuple(df.columns) == ALL_COLUMNS
    assert df.index.name == "row_id"
    assert df.index.is_unique
    assert df.loc["train:000002", "workclass"] == "?"
    assert df.loc["test:000000", "income"] in {"<=50K", ">50K"}
    assert all(pd.api.types.is_numeric_dtype(df[c]) for c in NUMERIC)
    assert all(pd.api.types.is_object_dtype(df[c]) for c in CATEGORICAL)


def test_splits_reproducible_grouped_and_no_test_overlap(tmp_path):
    _write_fixture(tmp_path)
    a = prepare_splits(tmp_path, seed=19)
    b = prepare_splits(tmp_path, seed=19)
    assert set(a) == {"train", "tune", "calibration", "validation", "test", "quarantine"}
    assert all(a[k].index.equals(b[k].index) for k in a)
    all_ids = [idx for part in a.values() for idx in part.index]
    assert len(all_ids) == len(set(all_ids))
    assert sum(map(len, a.values())) == 40
    assert len(a["quarantine"]) == 2
    assert {"train:000000", "train:000030"} <= set(a["quarantine"].index)
    # Each identical full record stays in a single partition.
    df = read_adult(tmp_path)
    membership = {idx: name for name, part in a.items() for idx in part.index}
    groups = {}
    for idx, row in df.iterrows():
        groups.setdefault(tuple(row), set()).add(membership[idx])
    # Official-test duplicates retain their test copy; only the development
    # copies are quarantined. No test duplicate may enter an active fit split.
    assert all(len(parts) == 1 or parts <= {"test", "quarantine"} for parts in groups.values())
    assert a["train"].attrs["manifest"]["counts"]["test"] == len(a["test"])


def test_partition_rule_fit_once_and_stable_for_all_splits(tmp_path):
    _write_fixture(tmp_path)
    splits = prepare_splits(tmp_path, seed=5)
    train = splits["train"]
    for kind in ("age", "age_education", "label_skew"):
        rule = build_partition_rule(train, 5, kind=kind, seed=77, severity=.8)
        assignments = rule.assign(splits["validation"])
        assert assignments.shape == (len(splits["validation"]),)
        assert np.all((assignments >= 0) & (assignments < 5))
        assert np.array_equal(assignments, rule.assign(splits["validation"]))
        expected = pd.Series(assignments, index=splits["validation"].index).sort_index()
        shuffled = splits["validation"].sample(frac=1, random_state=3)
        actual = pd.Series(rule.assign(shuffled), index=shuffled.index).sort_index()
        pd.testing.assert_series_equal(expected, actual)

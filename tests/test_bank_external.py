import numpy as np
import pandas as pd

from scripts.bank_data import _group_split, fit_partition_rule
from scripts.bank_workload import workloads


def miniature_bank():
    education = ["basic.9y", "university.degree"]
    rows = []
    for i in range(80):
        rows.append({"age": 20+i%30, "job": "admin." if i%2 else "technician",
                     "marital": "married", "education": education[i%2], "default": "no",
                     "housing": "yes", "loan": "no", "contact": "cellular", "month": "may",
                     "day_of_week": "mon", "campaign": 1, "pdays": "999", "previous": 0,
                     "poutcome": "nonexistent", "emp.var.rate": -1100,
                     "cons.price.idx": 93000, "cons.conf.idx": -40000,
                     "euribor3m": 2500, "nr.employed": 5100000,
                     "y": "yes" if i%5==0 else "no"})
    rows[79] = rows[0].copy()
    frame = pd.DataFrame(rows)
    frame.index = pd.Index([f"bank:{i:06d}" for i in range(len(frame))], name="row_id")
    return frame


def test_bank_group_split_keeps_retained_record_duplicates_together():
    frame = miniature_bank()
    parts = _group_split(frame)
    assert sum(map(len, parts.values())) == len(frame)
    found = [name for name, part in parts.items() if frame.index[0] in part.index]
    assert len(found) == 1
    assert frame.index[79] in parts[found[0]].index


def test_bank_partition_rule_reuses_training_fit_and_is_deterministic():
    frame = miniature_bank()
    for kind in ("age_education", "label_skew"):
        rule = fit_partition_rule(frame, kind, 5, 611, .8)
        first = rule.assign(frame)
        assert np.array_equal(first, rule.assign(frame))
        assert first.min() >= 0 and first.max() < 5


def test_bank_workload_has_registered_pdays_atom_and_label_interactions():
    frame = miniature_bank()
    nums = ("age", "campaign", "previous", "emp.var.rate", "cons.price.idx",
            "cons.conf.idx", "euribor3m", "nr.employed")
    schema = {"category_vocab_training_only": {c: sorted(frame[c].unique().tolist())
              for c in frame if c not in nums}}
    primary, audit = workloads(frame, schema)
    names = [q.name for q in primary.queries]
    assert "pdays=999&y=yes" in names
    assert "poutcome=nonexistent&y=yes" in names
    assert len(audit.queries) == 6

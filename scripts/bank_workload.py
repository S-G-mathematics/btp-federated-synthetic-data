"""Predeclared Bank workloads; thresholds/vocab use train only."""
from __future__ import annotations

import hashlib
import json

import numpy as np
import pandas as pd

from btp.evaluation import Query, Workload
from scripts.bank_data import LABEL, MODEL_COLUMNS, SCALES


def workloads(train: pd.DataFrame, schema: dict) -> tuple[Workload, Workload]:
    primary = []
    thresholds = {}
    for c in SCALES:
        values = sorted(set(int(x) for x in np.quantile(train[c], [.2, .4, .6, .8])))
        thresholds[c] = values
        primary.extend(Query(f"{c}<={v}", ((c, "le", v),)) for v in values)
    for c in MODEL_COLUMNS:
        if c not in SCALES:
            primary.extend(Query(f"{c}={v}", ((c, "eq", v),))
                           for v in schema["category_vocab_training_only"][c])
    for c in ("education", "job", "contact", "poutcome"):
        for value in schema["category_vocab_training_only"][c]:
            primary.append(Query(f"{c}={value}&y=yes", ((c, "eq", value), (LABEL, "eq", "yes"))))
    primary.append(Query("pdays=999&y=yes", (("pdays", "eq", "999"), (LABEL, "eq", "yes"))))
    age_mid = int(np.median(train.age))
    primary.append(Query(f"age<={age_mid}&y=yes", (("age", "le", age_mid), (LABEL, "eq", "yes"))))
    audit = [
        Query("audit:young_university_yes", (("age", "le", age_mid),
              ("education", "eq", "university.degree"), (LABEL, "eq", "yes"))),
        Query("audit:admin_cellular_yes", (("job", "eq", "admin."),
              ("contact", "eq", "cellular"), (LABEL, "eq", "yes"))),
        Query("audit:never_no_previous_yes", (("pdays", "eq", "999"),
              ("previous", "le", 0), (LABEL, "eq", "yes"))),
        Query("audit:older_basic_no", (("age", "gt", age_mid),
              ("education", "eq", "basic.9y"), (LABEL, "eq", "no"))),
        Query("audit:euribor_low_contact_yes", (("euribor3m", "le", int(np.median(train.euribor3m))),
              ("contact", "eq", "cellular"), (LABEL, "eq", "yes"))),
        Query("audit:negative_economy_yes", (("emp.var.rate", "le", int(np.median(train["emp.var.rate"]))),
              ("cons.conf.idx", "le", int(np.median(train["cons.conf.idx"]))),
              (LABEL, "eq", "yes"))),
    ]
    result = Workload(primary), Workload(audit)
    if not all(0 <= q.evaluate(train).mean() <= 1 for q in primary + audit):
        raise ValueError("Query workload outside [0,1]")
    return result


def workload_bytes(primary: Workload, audit: Workload) -> bytes:
    return (json.dumps({"primary": primary.to_dict(), "audit": audit.to_dict()},
                       sort_keys=True, separators=(",", ":")) + "\n").encode()


def workload_hash(primary: Workload, audit: Workload) -> str:
    return hashlib.sha256(workload_bytes(primary, audit)).hexdigest()

"""Versioned, postpilot Adult workload for a future projected-model campaign.

The original public_workloads remains the historical 54-cell definition. This
module is deliberately separate so old calibration/query artifacts are not
silently relabeled after the education-number defect was discovered.
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd

from .evaluation import Query, Workload, public_workloads
from .privacy import PUBLIC_EDUCATION_NUMBER_MAP


@dataclass(frozen=True)
class EducationRelationQuery:
    name: str = "education_number_relation_violation_v2"
    terms: tuple = ()  # No income term; compatible with feature-only subworkloads.

    def evaluate(self, frame: pd.DataFrame) -> np.ndarray:
        expected = frame["education"].map(PUBLIC_EDUCATION_NUMBER_MAP)
        actual = pd.to_numeric(frame["education-num"], errors="coerce")
        return (expected.isna() | actual.ne(expected)).to_numpy(float)


def projected_workloads_v2(schema: dict) -> tuple[Workload, Workload]:
    """Postpilot primary workload plus a fixed structural audit interaction.

    This is a future development workload, never an independent audit of the
    earlier raw-model campaign. The previous queries keep their original order.
    """
    primary, audit = public_workloads(schema)
    primary = Workload([*primary.queries, EducationRelationQuery()])
    audit = Workload([*audit.queries,
        Query("audit:Bachelors_num13_income_high_v2", (
            ("education", "eq", "Bachelors"),
            ("education-num", "eq", 13),
            ("income", "eq", ">50K"),
        ))])
    return primary, audit

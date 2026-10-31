import pandas as pd

from btp.privacy import public_schema
from btp.evaluation import public_workloads
from btp.projected_workload import projected_workloads_v2


def test_v2_adds_bounded_structural_queries_without_mutating_historical_workload():
    schema = public_schema()
    old_primary, old_audit = public_workloads(schema)
    primary, audit = projected_workloads_v2(schema)
    assert len(primary.queries) == len(old_primary.queries) + 1
    assert len(audit.queries) == len(old_audit.queries) + 1
    assert [q.name for q in primary.queries[:-1]] == [q.name for q in old_primary.queries]
    frame = pd.DataFrame({
        "education": ["Bachelors", "Bachelors", "?", "HS-grad"],
        "education-num": [13, 12, 0, 9],
        "income": [">50K", ">50K", "<=50K", ">50K"],
    })
    assert primary.queries[-1].evaluate(frame).tolist() == [0, 1, 1, 0]
    assert audit.queries[-1].evaluate(frame).tolist() == [1, 0, 0, 0]

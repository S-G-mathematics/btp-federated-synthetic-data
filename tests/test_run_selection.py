"""The registered unseen-interaction workload must remain audit-only."""

import pytest

from btp.run import select_release_method


def test_primary_tie_does_not_consult_audit_metric():
    rows = [
        {
            "method": "kernel_mean_matching",
            "access": "released_models_and_permitted_summaries",
            "query_linf": 0.03,
            "unseen_query_mae": 0.001,
        },
        {
            "method": "entropy_calibration",
            "access": "released_models_and_permitted_summaries",
            "query_linf": 0.03,
            "unseen_query_mae": 0.9,
        },
        {
            "method": "stacking_logscore",
            "access": "privileged_real_calibration_scores",
            "query_linf": 0.001,
            "unseen_query_mae": 0.0,
        },
    ]
    assert select_release_method(rows) == "entropy_calibration"


def test_nonfinite_primary_loss_cannot_select_a_method():
    rows = [
        {
            "method": "size",
            "access": "released_models_and_permitted_summaries",
            "query_linf": float("nan"),
        }
    ]
    with pytest.raises(ValueError, match="nonfinite"):
        select_release_method(rows)

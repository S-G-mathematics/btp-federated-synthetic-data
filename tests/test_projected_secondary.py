import importlib.util
from pathlib import Path

import numpy as np
import pandas as pd
import pytest


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("eval_projected_secondary", ROOT / "scripts/eval_projected_secondary.py")
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(MODULE)


def test_probability_metrics_respect_weights_and_undefined_single_class():
    y = np.array([0, 1, 0, 1])
    p = np.array([.1, .9, .8, .2])
    weighted = MODULE.probability_metrics(y, p, np.array([4., 4., 1., 1.]))
    equal = MODULE.probability_metrics(y, p, np.ones(4))
    assert weighted["auroc"] > equal["auroc"]
    assert weighted["brier"] < equal["brier"]
    assert 0 <= weighted["ece_fixed10"] <= 1
    one_class = MODULE.probability_metrics(np.zeros(3, int), np.array([.1, .2, .3]), np.ones(3))
    assert one_class["auroc"] is None
    assert one_class["auprc"] is None
    assert one_class["balanced_accuracy"] is None
    assert np.isfinite(one_class["log_loss"])


def test_declared_subgroup_queries_are_bounded_and_fixed():
    frame = pd.DataFrame({"sex": ["Female", "Male"], "race": ["Black", "White"],
                          "education": ["Bachelors", "HS-grad"], "income": [">50K", "<=50K"],
                          "age": [30, 50]})
    matrix = MODULE.Workload(MODULE.SUBGROUP_QUERIES).transform(frame)
    assert matrix.shape == (2, 17)
    assert set(np.unique(matrix)) <= {0., 1.}
    names = [q.name for q in MODULE.SUBGROUP_QUERIES]
    assert matrix[0, names.index("Black_income_high")] == 1
    assert matrix[1, names.index("Black_income_high")] == 0

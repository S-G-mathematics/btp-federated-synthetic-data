"""Known solutions and target-mass guarantees for fixed-budget calibration."""

from pathlib import Path
import sys

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from representation_constrained import constrained_query_minimax


def test_known_two_client_floor_and_l1_solution():
    H = np.eye(2)
    b = np.array([0.9, 0.1])
    alpha = np.array([0.5, 0.5])
    weights, certificate = constrained_query_minimax(
        H, b, alpha, delta=0.25, floor_ratio=0.5
    )
    np.testing.assert_allclose(weights, [0.625, 0.375], atol=1e-8)
    assert certificate["success"]
    assert certificate["actual_weight_l1"] <= 0.25 + 1e-8
    assert certificate["minimum_weight_alpha_ratio"] >= 0.5 - 1e-8


def test_weight_induced_query_bound_for_declared_support():
    H = np.array([[0.0, 0.4, 1.0], [1.0, 0.0, 0.2]])
    b = np.array([0.8, 0.3])
    alpha = np.array([0.2, 0.3, 0.5])
    weights, certificate = constrained_query_minimax(
        H, b, alpha, delta=0.25, floor_ratio=0.5
    )
    shift = float(np.max(np.abs(H @ (weights - alpha))))
    assert shift <= 0.5 * certificate["actual_weight_l1"] + 1e-8

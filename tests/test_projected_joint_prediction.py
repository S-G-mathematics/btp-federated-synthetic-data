import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT), str(ROOT / "scripts")]
from eval_projected_joint_prediction import joint_ratio


class TinyJoint:
    def log_prob(self, frame):
        result = np.full(len(frame), -np.inf)
        supported = frame.feature.to_numpy() == 0
        high = frame.income.eq(">50K").to_numpy()
        result[supported & high] = np.log(.75)
        result[supported & ~high] = np.log(.25)
        return result


def test_joint_ratio_normalizes_and_abstains_off_support():
    features = pd.DataFrame({"feature": [0, 1]})
    probability, reason = joint_ratio([TinyJoint()], np.array([1.]), features)
    assert probability[0] == .75
    assert reason[0] == "covered"
    assert np.isnan(probability[1])
    assert reason[1] == "both_labels_zero_mass"
